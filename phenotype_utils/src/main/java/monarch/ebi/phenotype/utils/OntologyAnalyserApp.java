package monarch.ebi.phenotype.utils;

import org.semanticweb.elk.owlapi.ElkReasonerFactory;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.reasoner.OWLReasoner;
import org.semanticweb.owlapi.search.EntitySearcher;

import java.io.File;
import java.io.IOException;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Hello world!
 */
public class OntologyAnalyserApp {
    private static String OBO = "http://purl.obolibrary.org/obo/";
    private static OWLAnnotationProperty ap_gwas = OWLManager.getOWLDataFactory().getOWLAnnotationProperty(IRI.create("http://www.ebi.ac.uk/efo/gwas_trait"));
    private final File ontology_file;
    private final File dir_out;
    private static OWLDataFactory df = OWLManager.getOWLDataFactory();


    public OntologyAnalyserApp(File ontology_file, File dir_out) throws IOException, OWLOntologyCreationException, OWLOntologyStorageException {
        this.ontology_file = ontology_file;
        this.dir_out = dir_out;
        run();
    }

    private void run() throws OWLOntologyCreationException {
        OWLOntologyManager man = OWLManager.createOWLOntologyManager();
        OWLOntology o = man.loadOntology(IRI.create(ontology_file));
        OWLReasoner r = new ElkReasonerFactory().createReasoner(o);
        Map<String, Integer> count_term_iris = new HashMap<>();
        Map<String,Set<OWLClass>> all_categories = new HashMap<>();
        Set<OWLClass> efo_disease_group = new HashSet<>();
        all_categories.put("efo_disease_group",efo_disease_group);
        efo_disease_group.add(cl("http://www.ebi.ac.uk/efo/EFO_0000651"));
        efo_disease_group.add(cl("http://www.ebi.ac.uk/efo/EFO_0000408"));
        Set<OWLClass> efo_anatomy_group = new HashSet<>();
        all_categories.put("efo_anatomy_group",efo_anatomy_group);
        efo_anatomy_group.add(cl("http://www.ebi.ac.uk/efo/EFO_0000635"));
        efo_anatomy_group.add(cl("http://www.ebi.ac.uk/efo/EFO_0000399"));
        efo_anatomy_group.add(cl("http://www.ebi.ac.uk/efo/EFO_0000324"));
        efo_anatomy_group.add(cl("http://purl.obolibrary.org/obo/OBI_0100026"));
        efo_anatomy_group.add(cl("http://purl.obolibrary.org/obo/CL_0000010"));
        Set<OWLClass> efo_assays_group = new HashSet<>();
        all_categories.put("efo_assays_group",efo_assays_group);
        efo_assays_group.add(cl("http://www.ebi.ac.uk/efo/EFO_0002694"));
        efo_assays_group.add(cl("http://www.ebi.ac.uk/efo/EFO_0001444"));
        efo_assays_group.add(cl("http://purl.obolibrary.org/obo/CHEBI_24431"));
        Set<OWLClass> efo_process_group = new HashSet<>();
        all_categories.put("efo_process_group",efo_process_group);
        efo_process_group.add(cl("http://purl.obolibrary.org/obo/GO_0008150"));
        Map<String,Set<OWLClass>> allentities_by_category = new HashMap<>();
        for(String cat:all_categories.keySet()) {
            Set<OWLClass> all = new HashSet<>();
            for(OWLClass catc:all_categories.get(cat)) {
                all.add(catc);
                all.addAll(r.getSubClasses(catc,false).getFlattened());
            }
            all.remove(df.getOWLThing());
            all.remove(df.getOWLNothing());
            allentities_by_category.put(cat,all);
        }

        Map<String, Integer> count_annotation_properties = new HashMap<>();
        Map<String, Integer> xrefs_iris = new HashMap<>();
        List<Map<String, String>> broken_xrefs = new ArrayList<>();
        List<Map<String, String>> data_term_data = new ArrayList<>();
        Set<OWLClass> terms = new HashSet<>(o.getClassesInSignature());
        terms.remove(df.getOWLThing());
        terms.remove(df.getOWLNothing());

        for (OWLClass cl : terms) {
            Map<String, String> rec = new HashMap<>();
            data_term_data.add(rec);
            if (cl.getIRI().toString().endsWith("http://www.w3.org/2002/07/owl#Thing")) {
                continue;
            }
            Set<OWLClass> subs = new HashSet<>(r.getSubClasses(cl, false).getFlattened());
            subs.remove(df.getOWLThing());
            subs.remove(df.getOWLNothing());
            Set<OWLClass> subs_efo = new HashSet<>();
            Set<String> namespaces = new HashSet<>();
            Set<String> xrefs_sources = new HashSet<>();
            boolean gwas_annotation = !EntitySearcher.getAnnotations(cl,o,ap_gwas).isEmpty();

            int gwas_annotations = 0;
            for (OWLClass sc : subs) {
                String iri = sc.getIRI().toString();
                if (iri.startsWith("http://www.ebi.ac.uk/efo/EFO_")) {
                    subs_efo.add(sc);
                }
                namespaces.add(getNamespace(iri));
                xrefs(sc, o).forEach(x -> xrefs_sources.add(getNamespace(x)));
                if(!EntitySearcher.getAnnotations(sc,o,ap_gwas).isEmpty()) {
                    gwas_annotations++;
                }
            }
            rec.put("id", cl.getIRI().toString());
            rec.put("ct_subclasses", subs.size() + "");
            rec.put("ns", getNamespace(cl.getIRI().toString()));
            rec.put("ct_subclasses_efo", subs_efo.size() + "");
            rec.put("pc_subclasses", 100 * ((double)subs.size() / (double)terms.size()) + "");
            rec.put("pc_subclasses_efo", 100 * ((double)subs_efo.size() / (double)subs.size()) + "");
            rec.put("sources", commaSepList(namespaces));
            rec.put("xref_sources", commaSepList(xrefs_sources));
            rec.put("gwas_annotation", gwas_annotation+"");
            rec.put("ct_gwas", gwas_annotations+"");
            rec.put("pc_gwas", 100 * ((double)gwas_annotations / (double)subs.size()) + "");
            rec.put("main",getCategory(allentities_by_category,cl)+"");
            String label = "";
            try {
                label = EntitySearcher.getAnnotations(cl, o, df.getRDFSLabel()).stream().findFirst().get().getValue().asLiteral().get().getLiteral();
            } catch (Exception e) {
                //System.out.println("No label");
            }
            rec.put("label", label);
            //log(subs_efo.size()+"|"+subs.size());
            String ns = getNamespaceFromIRI(cl.getIRI().toString());
            pp(count_term_iris, ns);
            Set<String> xrefs = xrefs(cl, o);
            for (String xref : xrefs) {
                String ns_x = getNamespace(xref);
                if (ns_x.equals("other")) {
                    //log(cl+" xref to "+xref+" broken.");
                    Map<String, String> rec_b = new HashMap<>();
                    rec_b.put("iri", cl.getIRI().toString());
                    rec_b.put("value", xref);
                    rec_b.put("category", "xref_format");
                    broken_xrefs.add(rec_b);
                }
                String xrefcat = ns + "-" + ns_x;
                pp(xrefs_iris, xrefcat);
            }
            for (OWLAnnotationAssertionAxiom anno : o.getAnnotationAssertionAxioms(cl.getIRI())) {
                pp(count_annotation_properties, anno.getProperty().getIRI().toString());
            }
        }

        export(getMaps(count_term_iris, "efo_term_sources"), "term_sources");
        export(getMaps(count_annotation_properties, "efo_annotation_properties"), "annotation_properties");
        export(getMaps(xrefs_iris, "efo_xref_categories"), "xref_categories");
        export(data_term_data, "terms");
        Export.writeCSV(broken_xrefs, new File(dir_out, "data_broken_xrefs.csv"));
    }

    private String getCategory(Map<String, Set<OWLClass>> allentities_by_category, OWLClass cl) {
        for( String cat:allentities_by_category.keySet()) {
            if(allentities_by_category.get(cat).contains(cl)) {
                return cat;
            }
        }
        return "Other";
    }

    private String commaSepList(Set<String> namespaces) {
        String sources = "";
        for (String ns : namespaces) {
            sources += ns + ",";
        }
        if (sources.endsWith(",")) {
            sources = sources.substring(0, sources.length() - 1);
        }
        return sources;
    }

    private String getNamespace(String xref) {
        String ns_x = getNamespaceFromIRI(xref);
        if (ns_x.equals("other")) {
            ns_x = getNamespaceFromCurie(xref);
        }
        return ns_x;
    }


    private Set<String> xrefs(OWLClass cl, OWLOntology o) {
        Set<String> xrefs = new HashSet<>();
        for (OWLAnnotationAssertionAxiom ax : o.getAnnotationAssertionAxioms(cl.getIRI())) {
            if (ax.getProperty().equals(Entities.ap_xref)) {
                try {
                    OWLAnnotationValue val = ax.annotationValue();
                    if (val.isLiteral()) {
                        xrefs.add(val.asLiteral().get().getLiteral());
                    } else {
                        xrefs.add(val.asIRI().get().toString());
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                    log("Broken xref for: " + cl);
                    log(ax);
                }
            }
        }
        return xrefs;
    }

    private void export(List<Map<String, String>> data, String name) {
        File file_data_efo_term_sources = new File(dir_out, "data_" + name + ".csv");
        Export.writeCSV(data, file_data_efo_term_sources);
    }

    private List<Map<String, String>> getMaps(Map<String, Integer> count, String name) {
        List<Map<String, String>> data = new ArrayList<>();
        for (String oid : count.keySet()) {
            //log(oid + ": " + count.get(oid));
            Map<String, String> rec = new HashMap<>();
            rec.put("id", oid);
            rec.put("count_" + name, count.get(oid) + "");
            data.add(rec);
        }
        return data;
    }

    private String getNamespaceFromIRI(String iri) {
        if (iri.startsWith(OBO)) {
            String id = iri.replaceAll(OBO,"");
            String ns = id.split("_")[0].toLowerCase();
            return ns;
        }
        if (iri.startsWith(OBO + "UBERON_")) {
            return "uberon";
        } else if (iri.startsWith(OBO + "HP_")) {
            return "hp";
        } else if (iri.startsWith(OBO + "MP_")) {
            return "mp";
        } else if (iri.startsWith(OBO + "DOID_")) {
            return "do";
        } else if (iri.startsWith(OBO + "BTO_")) {
            return "bto";
        } else if (iri.startsWith(OBO + "MPATH_")) {
            return "mpath";
        } else if (iri.startsWith(OBO + "MA_")) {
            return "ma";
        } else if (iri.startsWith(OBO + "GO_")) {
            return "go";
        } else if (iri.startsWith(OBO + "FBbt_")) {
            return "fbbt";
        } else if (iri.startsWith(OBO + "PO_")) {
            return "po";
        } else if (iri.startsWith(OBO + "OBI_")) {
            return "obi";
        } else if (iri.startsWith(OBO + "FMA_")) {
            return "fma";
        } else if (iri.startsWith(OBO + "EO_")) {
            return "eo";
        } else if (iri.startsWith(OBO + "ZEA_")) {
            return "zea";
        } else if (iri.startsWith(OBO + "UO_")) {
            return "uo";
        } else if (iri.startsWith(OBO + "PR_")) {
            return "pr";
        } else if (iri.startsWith(OBO + "HANCESTRO_")) {
            return "hancestro";
        } else if (iri.startsWith(OBO + "FBdv_")) {
            return "fbdv";
        } else if (iri.startsWith(OBO + "ZP_")) {
            return "zp";
        } else if (iri.startsWith(OBO + "NBO_")) {
            return "nbo";
        } else if (iri.startsWith(OBO + "WBPhenotype_")) {
            return "wbphenotype";
        } else if (iri.startsWith(OBO + "COHD_")) {
            return "cohd";
        } else if (iri.startsWith(OBO + "DC_")) {
            return "dc";
        } else if (iri.startsWith(OBO + "FAO_")) {
            return "fao";
        } else if (iri.startsWith(OBO + "FBcv_")) {
            return "fbcv";
        } else if (iri.startsWith(OBO + "GOCHE_")) {
            return "goche";
        } else if (iri.startsWith(OBO + "ICD10_")) {
            return "icd10";
        } else if (iri.startsWith(OBO + "KEGG_")) {
            return "kegg";
        } else if (iri.startsWith(OBO + "VT_")) {
            return "vt";
        } else if (iri.startsWith(OBO + "WBbt_")) {
            return "wbbt";
        } else if (iri.startsWith(OBO + "ONCOTREE_")) {
            return "oncotree";
        } else if (iri.startsWith("http://uri.neuinfo.org/nif/nifstd/")) {
            return "nifstd";
        } else if (iri.startsWith("http://www.genenames.org/")) {
            return "genenames";
        } else if (iri.startsWith(OBO + "ICD9_")) {
            return "icd9";
        } else if (iri.startsWith(OBO + "SO_")) {
            return "so";
        } else if (iri.startsWith(OBO + "NCIT_")) {
            return "ncit";
        } else if (iri.startsWith(OBO + "OGMS_")) {
            return "ogms";
        } else if (iri.startsWith(OBO + "IDO_")) {
            return "ido";
        } else if (iri.startsWith(OBO + "TO_")) {
            return "to";
        } else if (iri.startsWith(OBO + "WBls_")) {
            return "wbls";
        } else if (iri.startsWith(OBO + "ZFA_")) {
            return "zfa";
        } else if (iri.startsWith(OBO + "PATO_")) {
            return "pato";
        } else if (iri.startsWith(OBO + "IAO_")) {
            return "iao";
        } else if (iri.startsWith(OBO + "MONDO_")) {
            return "mondo";
        } else if (iri.startsWith(OBO + "NCBITaxon_")) {
            return "ncbitaxon";
        } else if (iri.startsWith(OBO + "CHEBI_")) {
            return "chebi";
        } else if (iri.startsWith(OBO + "CLO_")) {
            return "clo";
        } else if (iri.startsWith(OBO + "OMIT_")) {
            return "omit";
        } else if (iri.startsWith(OBO + "GARD_")) {
            return "gard";
        } else if (iri.startsWith(OBO + "SCTID_")) {
            return "sctid";
        } else if (iri.startsWith(OBO + "MESH_")) {
            return "mesh";
        } else if (iri.startsWith(OBO + "CMO_")) {
            return "cmo";
        } else if (iri.startsWith(OBO + "OBA_")) {
            return "oba";
        } else if (iri.startsWith(OBO + "CL_")) {
            return "cl";
        } else if (iri.startsWith("http://www.orpha.net/ORDO/Orphanet_")) {
            return "orphanet";
        } else if (iri.startsWith("http://www.ebi.ac.uk/efo/EFO_")) {
            return "efo";
        } else if (iri.startsWith("http://upload.wikimedia.org/wikipedia/")) {
            return "wikimedia ";
        } else if (iri.startsWith("http://ncicb.nci.nih.gov/xml")) {
            return "ncicb";
        } else if (iri.startsWith("http://dbpedia.org/resource/")) {
            return "dbpedia";
        } else if (iri.startsWith("http://www.snomedbrowser.com/")) {
            return "snomed";
        } else if (iri.startsWith("http://linkedlifedata.com/resource/umls/")) {
            return "umls";
        } else if (iri.startsWith("http://braininfo.rprc.washington.edu/")) {
            return "braininfo";
        } else if (iri.startsWith("http://www.ifomis.org/bfo/1.1/snap#")) {
            return "bfo1.1";
        } else if (iri.startsWith("http://omim.org/entry/")) {
            return "omim";
        } else if (iri.startsWith("http://www.omim.org/phenotypicSeries/")) {
            return "omim";
        } else if (iri.startsWith("http://neurolex.org/wiki/Category")) {
            return "neurolex";
        } else if (iri.startsWith("http://en.wikipedia.org/wiki")) {
            return "wikipedia";
        } else if (iri.startsWith("http://www.w3.org/2002/07/owl#")) {
            return "owl";
        } else if (iri.startsWith("http://www.ifomis.org/bfo/1.1/snap#")) {
            return "bfo1.1";
        } else if (iri.endsWith("http://www.ebi.ac.uk/efo/http")) {
            log("Counting currently broken iri..");
            return "efo";
        } else if (iri.startsWith("http:")) {
            //log("Unknown IRI namespace: " + iri);
            return "other";
        } else {
            //log("Unknown namespace: "+iri);
            return "other";
        }
    }


    private String getNamespaceFromCurie(String iri) {
        if (iri.contains(":")) {
            String[] a = iri.split(":");
            if (a.length == 2) {
                return a[0].toLowerCase();
            } else {
                //log("Unknown CURIE: "+iri);
                return "other";
            }
        } else {
            //log("Unknown CURIE: "+iri);
            return "other";
        }
    }


    private void pp(Map<String, Integer> count, String oid) {
        if (!count.containsKey(oid)) {
            count.put(oid, 0);
        }
        count.put(oid, count.get(oid) + 1);
    }


    private void log(Object o) {
        System.out.println(o.toString());
    }

    private OWLClass cl(String iri) {
        return df.getOWLClass(IRI.create(iri));
    }

    public static void main(String[] args) throws OWLOntologyCreationException, IOException, OWLOntologyStorageException {

	    String ontology_path = args[0];
        String dir_path_out = args[1];

        //String ontology_path = "/Users/matentzn/Dropbox/efo2019_paper/data/ontologies/efo2019.owl";
        //String dir_path_out = "/data/";

        File ontology_file = new File(ontology_path);
        File dir_out = new File(dir_path_out);

        new OntologyAnalyserApp(ontology_file, dir_out);
    }

}
