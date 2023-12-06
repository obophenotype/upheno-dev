package monarch.ebi.phenotype.utils;

/**
import com.fasterxml.jackson.core.JsonProcessingException;
import org.apache.commons.io.FileUtils;
import org.geneontology.obographs.io.OgJsonGenerator;
import org.geneontology.obographs.io.OgJsonReader;
import org.geneontology.obographs.model.GraphDocument;
import org.geneontology.obographs.owlapi.FromOwl;
import org.semanticweb.elk.owlapi.ElkReasonerFactory;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.reasoner.OWLReasoner;

import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.util.*;
import java.util.stream.Collectors;


 * Hello world!

public class OBOGraphsTesterApp {

    private final File ontology_file;
    private final File testdir;

    private OBOGraphsTesterApp(File ontology_file, File testdir) throws OWLOntologyCreationException {
        this.ontology_file = ontology_file;
        this.testdir = testdir;
        run();
    }

    private void run() throws OWLOntologyCreationException {

// usual OWLAPI invocations:
        OWLOntologyManager m = OWLManager.createOWLOntologyManager();
        OWLOntology ontology = m.loadOntologyFromOntologyDocument(ontology_file);
//OboGraphs
        FromOwl fromOwl = new FromOwl();
        GraphDocument gd = fromOwl.generateGraphDocument(ontology);

        String name = ontology_file.getName().replace(".obo", ".json").replace(".owl", ".json");
        File jsonOutFile = new File(ontology_file.getParent(),name+"_1.json");
        File jsonOutFile2 = new File(ontology_file.getParent(),name+"_2.json");



        try {
            String jsonStr = OgJsonGenerator.render(gd);
            FileUtils.writeStringToFile(jsonOutFile, jsonStr,"utf-8");


            GraphDocument gd2 = OgJsonReader.readFile(jsonOutFile);
            String jsonStr2 = OgJsonGenerator.render(gd2);
            FileUtils.writeStringToFile(jsonOutFile2, jsonStr2,"utf-8");

        } catch (JsonProcessingException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    private void log(Object o) {
        System.out.println(o.toString());
    }

    public static void main(String[] args) throws OWLOntologyCreationException {
		String ontology_path = args[0];
        String testdir_path = args[1];

//        String ontology_path = "/Users/matentzn/ws/pato/pato.owl";
 // String testdir_path = "/Users/matentzn/data";

        File ontology_file = new File(ontology_path);
        File testdir_file = new File(testdir_path);
        new OBOGraphsTesterApp(ontology_file,testdir_file);
    }

}
 */
