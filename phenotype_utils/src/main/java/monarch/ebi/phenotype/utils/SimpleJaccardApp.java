package monarch.ebi.phenotype.utils;

import org.apache.commons.io.FileUtils;
import org.semanticweb.elk.owlapi.ElkReasonerFactory;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.reasoner.OWLReasoner;

import java.io.File;
import java.io.IOException;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Hello world!
 */
public class SimpleJaccardApp {

    private final File ontology_file;
    private final File data_file;
    private static OWLDataFactory df = OWLManager.getOWLDataFactory();
    private Set<String> c1_classes = new HashSet<>();
    private Set<String> c2_classes = new HashSet<>();
    private Set<OWLClass> phenotype = new HashSet<>();
    private RenderManager ren = RenderManager.getInstance();
    private OWLClass root;
    private boolean materialise_subconcepts;
    private double cutoff;


    private SimpleJaccardApp(File ontology_file,File c1_list_file,File c2_list_file, String root, File data_file, boolean materialise_subconcepts, double cutoff) throws IOException, OWLOntologyCreationException {
        this.ontology_file = ontology_file;
        this.data_file = data_file;
        this.root = cl(root);
        this.materialise_subconcepts = materialise_subconcepts;
        this.cutoff = cutoff;
        FileUtils.readLines(c1_list_file, "utf-8").forEach(e -> c1_classes.add(e));
        FileUtils.readLines(c2_list_file, "utf-8").forEach(e -> c2_classes.add(e));
        run();
    }

    private void run() throws OWLOntologyCreationException {
        OWLOntologyManager man = OWLManager.createOWLOntologyManager();
        OWLOntology o = man.loadOntology(IRI.create(ontology_file));
        long start = System.currentTimeMillis();
        phenotype.addAll(new ElkReasonerFactory().createReasoner(o).getSubClasses(root,false).getFlattened());
        phenotype.remove(df.getOWLThing());
        phenotype.remove(df.getOWLNothing());

        if(materialise_subconcepts) {
            Set<OWLAxiom> axioms = getDefinedSubConcepts(o);
            log("Added generated equivalent class axioms: "+axioms.size());
            //axioms.forEach(e->log(ren.render(e)));
            man.addAxioms(o,axioms);
        }

        long end_materialise = System.currentTimeMillis();

        OWLReasoner elk = new ElkReasonerFactory().createReasoner(o);
        ren.addLabel(o);
        phenotype.removeAll(elk.getUnsatisfiableClasses().getEntities());

        Map<OWLClass,Set<OWLClass>> superClassCache = new HashMap<>();
        for(OWLClass c:phenotype) {
            Set<OWLClass> sc = elk.getSuperClasses(c,false).getFlattened();
            sc.remove(df.getOWLNothing());
            sc.remove(df.getOWLThing());
            sc.remove(Entities.cl_upheno_phenotype);
            sc.add(c);
            superClassCache.put(c,uPhenoClasses(sc));
        }

        //int loops = 5000;

        long end_prepare_superclass_sets = System.currentTimeMillis();
        long total = c1_classes.size() * c2_classes.size();

        Set<Match> matches_threshold = new HashSet<>();

        int i = 0;
        for(String c1:c1_classes) {
            if (i % 1000 == 0) {
                System.out.println(i+" ("+((double)i/(double)total)+", "+matches_threshold.size()+" matches)");
            }
            i++;
            for (String c2 : c2_classes) {
                if(c1!=c2) {
                    OWLClass l = cl(c1);
                    OWLClass r = cl(c2);
                    //log(l+" vs "+r);
                    double jacc = computeJaccardSimilarity(superClassCache,l, r);
                    if(jacc>cutoff) {
                        Match match = new ClassMatch(l,r);
                        match.setValue("jaccard",jacc);
                        matches_threshold.add(match);
                    }
                }
            }
        }

        long sim_done = System.currentTimeMillis();
        log("");
        log("Total number of matches to above threshold: "+matches_threshold.size());
        List<Map<String,String>> data = new ArrayList<>();
        for(Match match:matches_threshold) {
            Map<String,String> rec = new HashMap<>();
            rec.put("c1",match.getLeftMatch().toString());
            rec.put("c2",match.getRightMatch().toString());
            rec.put("c1_label",ren.render(match.getLeftMatch()));
            rec.put("c2_label",ren.render(match.getRightMatch()));
            for(String s: match.getData().keySet()) {
                rec.put(s, match.getData().get(s)+"");
            }
            data.add(rec);
        }
        long end = System.currentTimeMillis();
        log("Overall:" +(end-start)/1000+" sec");
        log("Materialise:" +(end_materialise-start)/1000+" sec");
        log("Prepare superclass sets:" +(end_prepare_superclass_sets-end_materialise)/1000+" sec");
        log("Similarity:" +(sim_done-end_prepare_superclass_sets)/1000+" sec");
        log("Data:" +(end-sim_done)/1000+" sec");

        Export.writeCSV(data,data_file);
    }

    private double computeJaccardSimilarity(Map<OWLClass,Set<OWLClass>> cache, OWLClassExpression c1, OWLClassExpression c2) {
        if(! (cache.containsKey(c1) && cache.containsKey(c2))) {
            return 0.0;
        }
        if(!cache.containsKey(c1)) {
            return 0.0;
        }
        Set<OWLClass> superClassesUnion = new HashSet<>(cache.get(c1));
        Set<OWLClass> superClassesIntersection = new HashSet<>(cache.get(c1));
        superClassesUnion.addAll(cache.get(c2));
        superClassesIntersection.retainAll(cache.get(c2));
        return (double)superClassesIntersection.size()/(double)superClassesUnion.size();
    }

    String TMPURL = Entities.OBOPURLSTRING + "UPHENOTMP_";
    private Set<OWLAxiom> getDefinedSubConcepts(OWLOntology o) {
        Set<OWLAxiom> axioms = new HashSet<>();
        int i = 0;
        for(OWLClass p: phenotype) {
            OWLClassExpression ce_bearer = OntologyUtils.getHasAffectedEntity(o,p);
            if(ce_bearer!=null) {
                i++;
                createNewEquivalentClassAxiom(axioms, i, ce_bearer);
            }
        }
        return axioms;
    }

    private void createNewEquivalentClassAxiom(Set<OWLAxiom> axioms, int i, OWLClassExpression bearer_filler) {
        OWLClass e = df.getOWLClass(IRI.create(TMPURL + i));
        OWLClassExpression eq = composePhenotypeBearerExpression(bearer_filler, e);
        OWLEquivalentClassesAxiom e1 = df.getOWLEquivalentClassesAxiom(e, eq);
        axioms.add(e1);
    }

    private OWLClassExpression composePhenotypeBearerExpression(OWLClassExpression bearer_filler, OWLClass e) {
        OWLClassExpression INE = df.getOWLObjectSomeValuesFrom(Entities.inheres_in_part_of, bearer_filler);
        OWLClassExpression QINE = df.getOWLObjectIntersectionOf(Entities.cl_pato_quality, INE);
        OWLClassExpression phenotype = df.getOWLObjectSomeValuesFrom(Entities.haspart, QINE);
        return phenotype;
    }

    private Set<OWLClass> uPhenoClasses(Set<OWLClass> classes) {
        return classes.stream().filter(e->phenotype.contains(e)).collect(Collectors.toSet());
    }

    private OWLClass cl(String iri) {
        return df.getOWLClass(IRI.create(iri));
    }

    private void log(Object o) {
        System.out.println(o.toString());
    }

    public static void main(String[] args) throws OWLOntologyCreationException, IOException {


		String ontology_path = args[0];
        String c1_list = args[1];
        String c2_list = args[2];
        String root = args [3];
        String data_path_out = args[4];
        boolean materialise_has_phenotype_affecting = args[5].equals("materialise");
        double cutoff = Double.valueOf(args[6]);

/*
        String ontology_path = "/Users/matentzn/ws/upheno-dev/src/curation/upheno-release/all/upheno_all_with_relations.owl";
        String c1_list = "/Users/matentzn/ws/upheno-dev/src/curation/tmp/mp-class-hierarchy.txt";
        String c2_list = "/Users/matentzn/ws/upheno-dev/src/curation/tmp/hp-class-hierarchy.txt";
        String root = "http://purl.obolibrary.org/obo/UPHENO_0001001";
        String data_path_out = "/Users/matentzn/ws/upheno-dev/src/curation/upheno-release/all/upheno_semantic_similarity.csv";
*/
        File ontology_file = new File(ontology_path);
        File c1_list_file = new File(c1_list);
        File c2_list_file = new File(c2_list);
        File data_file_out = new File(data_path_out);
        new SimpleJaccardApp(ontology_file, c1_list_file, c2_list_file, root, data_file_out, materialise_has_phenotype_affecting, cutoff);
    }

}
