package monarch.ebi.phenotype.utils;

import org.apache.commons.io.FileUtils;
import org.semanticweb.elk.owlapi.ElkReasonerFactory;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.model.parameters.Imports;
import org.semanticweb.owlapi.reasoner.OWLReasoner;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.HashSet;
import java.util.Set;

/**
 * Hello world!
 */
public class AssertMatchesAsSubclassOfAxiomsApp {
    private static String OBOPURLSTRING = "http://purl.obolibrary.org/obo/";
    private final Set<Match> matches = new HashSet<>();
    private final File ontology_file;
    private final File ontology_file_out;
    private static OWLDataFactory df = OWLManager.getOWLDataFactory();




    public AssertMatchesAsSubclassOfAxiomsApp(File ontology_file, File ontology_file_out, File matches_csv_file) throws IOException, OWLOntologyCreationException, OWLOntologyStorageException {
        this.ontology_file = ontology_file;
        this.ontology_file_out = ontology_file_out;
        if(matches_csv_file.isFile()) {
            FileUtils.readLines(matches_csv_file,"utf-8").forEach(s-> {
                String[] sa = s.trim().split(",");
                matches.add(new ClassMatch(cl(sa[0]),cl(sa[1])));
            });
        }
        run();
    }

    private void run() throws IOException, OWLOntologyCreationException, OWLOntologyStorageException {
        OWLOntologyManager man = OWLManager.createOWLOntologyManager();
        OWLOntology o = man.loadOntology(IRI.create(ontology_file));
        OWLReasoner elk = new ElkReasonerFactory().createReasoner(o);


        Set<OWLAxiom> axioms = new HashSet<>();
        for(Match match:matches) {
            OWLClassExpression l = match.getLeftMatch();
            OWLClassExpression r = match.getRightMatch();
            copySubclasses(elk, axioms, l, r);
            copySubclasses(elk, axioms, r, l);
        }

        OWLOntology out = man.createOntology(axioms);

        man.saveOntology(out,new FileOutputStream(ontology_file_out));
    }

    private void copySubclasses(OWLReasoner elk, Set<OWLAxiom> axioms, OWLClassExpression l, OWLClassExpression r) {
        for(OWLClass superClass1:elk.getSuperClasses(l,true).getFlattened()) {
            if(superClass1.getIRI().toString().startsWith("http://purl.obolibrary.org/obo/UPHENO_")) {
                OWLSubClassOfAxiom ax = df.getOWLSubClassOfAxiom(r, superClass1);
                axioms.add(ax);
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
        String matches_csv = args[2];

/*
        String ontology_path = "/Users/matentzn/ws/upheno-dev/src/curation/upheno-release/all/upheno_all_with_relations.owl";
        String ontology_path_out = "/Users/matentzn/ws/upheno-dev/src/curation/upheno-release/all/upheno_for_semantic_similarity.owl";
        String matches_csv = "/Users/matentzn/ws/upheno-dev/src/curation/upheno-release/all/upheno_mapping_lexical.csv";
*/
        File ontology_file = new File(ontology_path);
        File ontology_file_out = new File(ontology_path_out);
        File matches_csv_file = new File(matches_csv);

        new AssertMatchesAsSubclassOfAxiomsApp(ontology_file, ontology_file_out, matches_csv_file);
    }

}
