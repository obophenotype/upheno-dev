package monarch.ebi.phenotype.utils;

import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.model.parameters.Imports;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.HashSet;
import java.util.Set;

/**
 * Hello world!
 */
public class LoadSaveOntologyApp {
    private final File ontology_file;

    LoadSaveOntologyApp(File ontology_file) throws IOException, OWLOntologyCreationException, OWLOntologyStorageException {
        this.ontology_file = ontology_file;
        run();

    }

    private void run() throws IOException, OWLOntologyCreationException, OWLOntologyStorageException {
        OWLOntologyManager man = OWLManager.createOWLOntologyManager();
        OWLOntology o = man.loadOntology(IRI.create(ontology_file));
        man.saveOntology(o,new FileOutputStream(ontology_file));
    }

    public static void main(String[] args) throws OWLOntologyCreationException, IOException, OWLOntologyStorageException {

	    //String ontology_path = args[0];

        String ontology_path = "/Users/matentzn/ws/neo4j2owl/src/test/resources/smalltest.owl";

        File ontology_file = new File(ontology_path);

        new LoadSaveOntologyApp(ontology_file);
    }

}
