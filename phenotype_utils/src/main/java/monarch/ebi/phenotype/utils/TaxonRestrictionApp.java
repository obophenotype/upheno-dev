package monarch.ebi.phenotype.utils;

import org.apache.commons.io.FileUtils;
import org.semanticweb.elk.owlapi.ElkReasonerFactory;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.model.parameters.Imports;
import org.semanticweb.owlapi.reasoner.OWLReasoner;

import java.io.*;
import java.util.*;

/**
 * Hello world!
 */
public class TaxonRestrictionApp {
    private static String OBOPURLSTRING = "http://purl.obolibrary.org/obo/";
    private final Set<OWLClass> preserve_eq = new HashSet<>();
    private final File ontology_file;
    private final File ontology_file_out;
    private final OWLClass taxon;
    private final String taxon_label;
    private final String phenotype_prefix;
    private static OWLDataFactory df = OWLManager.getOWLDataFactory();
    private static OWLObjectProperty haspart = df.getOWLObjectProperty(IRI.create("http://purl.obolibrary.org/obo/BFO_0000051"));
    private final OWLObjectProperty present_in_taxon = df.getOWLObjectProperty(IRI.create("http://purl.obolibrary.org/obo/UPHENO_9000005"));



    public TaxonRestrictionApp(File ontology_file, File ontology_file_out,String taxon, String taxon_label, String phenotype_prefix, File preserve_eq_file) throws IOException, OWLOntologyCreationException, OWLOntologyStorageException {
        this.ontology_file = ontology_file;
        this.ontology_file_out = ontology_file_out;
        this.taxon = cl(taxon);
        this.taxon_label = taxon_label;
        this.phenotype_prefix = phenotype_prefix;
        if(preserve_eq_file.isFile()) {
            FileUtils.readLines(preserve_eq_file,"utf-8").forEach(s->preserve_eq.add(cl(s)));
        }
        run();
    }

    private void run() throws IOException, OWLOntologyCreationException, OWLOntologyStorageException {
        OWLOntologyManager man = OWLManager.createOWLOntologyManager();
        OWLOntology o = man.loadOntology(IRI.create(ontology_file));
        Set<OWLClass> phenotypeClasses = new HashSet<>();
        for(OWLClass cl:o.getClassesInSignature(Imports.INCLUDED)) {
            if(cl.getIRI().toString().startsWith(phenotype_prefix)) {
                phenotypeClasses.add(cl);
            }
        }
        Set<OWLAxiom> remove = new HashSet<>();
        Set<OWLAxiom> add = new HashSet<>();
        Set<OWLAxiom> eqs = new HashSet<>();

        for(OWLEquivalentClassesAxiom eq:o.getAxioms(AxiomType.EQUIVALENT_CLASSES, Imports.INCLUDED)) {
            if(eq.getNamedClasses().size()>1) {
                remove.add(eq);
                continue;
            }
            for(OWLClass n:eq.getNamedClasses()) {
                if(preserve_eq.contains(n)) {
                    eqs.add(eq);
                } else {
                    remove.add(eq);
                }
            }
        }


        adding_taxon_restrictions(eqs, remove, add);

        // JM commented out for OLS4 test July 2023
        // for(OWLClass p:phenotypeClasses) {
        //     add_taxon_label(o, remove, add, p);
        // }

        //log(remove.size());
        //log(add.size());

        Set<OWLAxiom> axioms = new HashSet<>(o.getAxioms(Imports.INCLUDED));
        axioms.removeAll(remove);
        axioms.addAll(add);

        /*for(OWLAxiom ax:axioms) {
            for(OWLClass c:ax.getClassesInSignature()) {
                if(c.getIRI().toString().endsWith("HP_0003214")) {
                    log(ax);
                }
            }
        }*/

        OWLOntology out = man.createOntology(axioms);

        man.saveOntology(out,new FileOutputStream(ontology_file_out));
    }

    private void add_taxon_label(OWLOntology o, Set<OWLAxiom> remove, Set<OWLAxiom> add, OWLClass p) {
        for (OWLAnnotationAssertionAxiom ax : o.getAnnotationAssertionAxioms(p.getIRI())) {
            if(ax.getProperty().isLabel()) {
                remove.add(ax);
                String label = ax.annotationValue().asLiteral().get().getLiteral();
                label = label +" ("+taxon_label+")";
                add.add(df.getOWLAnnotationAssertionAxiom(ax.getProperty(),ax.getSubject(),df.getOWLLiteral(label)));
            }
        }
    }

    private void adding_taxon_restrictions(Set<OWLAxiom> eqs, Set<OWLAxiom> remove, Set<OWLAxiom> add) {
        for(OWLAxiom ax:eqs) {
            if(ax instanceof OWLEquivalentClassesAxiom) {
            OWLEquivalentClassesAxiom eq = (OWLEquivalentClassesAxiom)ax;
            Set<OWLClass> named_cls = eq.getNamedClasses();
            OWLClass named = null;
            for(OWLClass n:named_cls) {
                named = n;
            }
            if (named_cls.size() == 1) {
                for (OWLClassExpression cein : eq.getClassExpressions()) {
                    if (cein instanceof OWLObjectSomeValuesFrom) {
                        OWLObjectSomeValuesFrom ce = (OWLObjectSomeValuesFrom) cein;
                        if (!ce.getProperty().isAnonymous()) {
                            if (ce.getProperty().asOWLObjectProperty().equals(haspart)) {
                                if (ce.getFiller() instanceof OWLObjectIntersectionOf) {
                                    OWLObjectIntersectionOf ois = (OWLObjectIntersectionOf) ce.getFiller();
                                    Set<OWLClassExpression> operands = new HashSet<>(ois.getOperands());
                                    operands.add(df.getOWLObjectSomeValuesFrom(present_in_taxon, taxon));
                                    OWLObjectIntersectionOf oisn = df.getOWLObjectIntersectionOf(operands);
                                    remove.add(ax);
                                    add.add(df.getOWLEquivalentClassesAxiom(named, df.getOWLObjectSomeValuesFrom(haspart, oisn)));
                                    break;
                                }
                            }
                        }
                    }
                }
            }
            }
        }
    }

    private void log(Object o) {
        System.out.println(o.toString());
    }


    private OWLClass cl(String iri) {
        return df.getOWLClass(IRI.create(iri));
    }

    public static void main(String[] args) throws OWLOntologyCreationException, IOException, OWLOntologyStorageException {

		String ontology_path = args[0];
        String ontology_path_out = args[1];
        String taxon = args[2];
        String taxon_label = args[3];
        String phenotype_prefix = args[4];
        String preserve_eq_file_path = args[5];

/*
        String ontology_path = "/ws/upheno-dev/src/curation/tmp/hp.owl";
        String ontology_path_out = "/data/hp-taxon.owl";
        String taxon = "http://purl.obolibrary.org/obo/NCBITaxon_9606";
        String taxon_label = "Human";
        String phenotype_prefix = "http://purl.obolibrary.org/obo/HP_";
        String preserve_eq_file_path = "/ws/upheno-dev/src/curation/tmp/preserve_eq_hp.owl";
*/
        File ontology_file = new File(ontology_path);
        File ontology_file_out = new File(ontology_path_out);
        File preserve_eq_file = new File(preserve_eq_file_path);

        new TaxonRestrictionApp(ontology_file, ontology_file_out, taxon, taxon_label, phenotype_prefix, preserve_eq_file);
    }

}
