package monarch.ebi.phenotype.utils;

import org.apache.commons.io.FileUtils;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.model.parameters.Imports;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.HashSet;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Hello world!
 */
public class AddHasPartBufferApp {
    private static String OBOPURLSTRING = "http://purl.obolibrary.org/obo/";
    private final File ontology_file;
    private static OWLDataFactory df = OWLManager.getOWLDataFactory();
    private static OWLObjectProperty haspart = df.getOWLObjectProperty(IRI.create("http://purl.obolibrary.org/obo/BFO_0000051"));



    public AddHasPartBufferApp(File ontology_file) throws IOException, OWLOntologyCreationException, OWLOntologyStorageException {
        this.ontology_file = ontology_file;
        run();

    }

    private void run() throws IOException, OWLOntologyCreationException, OWLOntologyStorageException {
        OWLOntologyManager man = OWLManager.createOWLOntologyManager();
        OWLOntology o = man.loadOntology(IRI.create(ontology_file));
        RenderManager renderManager = RenderManager.getInstance();

        Set<OWLAxiom> axioms = new HashSet<>();
        for(OWLEquivalentClassesAxiom eq:o.getAxioms(AxiomType.EQUIVALENT_CLASSES, Imports.INCLUDED)) {
            Set<OWLClass> named_cls = eq.getNamedClasses();
            OWLClass named = null;
            for(OWLClass n:named_cls) {
                named = n;
            }
            if (named_cls.size() == 1) {
                if(eq.getClassExpressions().size() ==2) {
                    for (OWLClassExpression cein : eq.getClassExpressions()) {
                        if (cein instanceof OWLObjectIntersectionOf) {
                            OWLClassExpression haspartbuffer = df.getOWLObjectSomeValuesFrom(haspart, cein);
                            OWLEquivalentClassesAxiom ea = df.getOWLEquivalentClassesAxiom(named, haspartbuffer);
                            axioms.add(ea);
                        }
                    }
                }
                else {
                    log("More than one definition:" + renderManager.renderForMarkdown(eq));
                }
            } else {
                log("More than one named class:" + renderManager.renderForMarkdown(eq));
            }
        }



        OWLOntology out = man.createOntology(axioms);

        man.saveOntology(out,new FileOutputStream(new File(ontology_file.getParent(),"has_part_"+ontology_file.getName())));
    }


    private void log(Object o) {
        System.out.println(o.toString());
    }


    private OWLClass cl(String iri) {
        return df.getOWLClass(IRI.create(iri));
    }

    public static void main(String[] args) throws OWLOntologyCreationException, IOException, OWLOntologyStorageException {

	    String ontology_path = args[0];

        //String ontology_path = "/Users/matentzn/ws/fypo/src/ontology/components/fypo-eqs.owl";

        File ontology_file = new File(ontology_path);

        new AddHasPartBufferApp(ontology_file);
    }

}
