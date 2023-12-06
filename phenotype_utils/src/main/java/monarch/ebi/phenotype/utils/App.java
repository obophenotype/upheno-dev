package monarch.ebi.phenotype.utils;

import java.io.File;
import java.io.IOException;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import org.apache.commons.io.FileUtils;
import org.semanticweb.elk.owlapi.ElkReasonerFactory;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.IRI;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLLogicalAxiom;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLOntologyCreationException;
import org.semanticweb.owlapi.model.parameters.Imports;
import org.semanticweb.owlapi.reasoner.OWLReasoner;

/**
 * Hello world!
 *
 */
public class App {
	public static void main(String[] args) throws OWLOntologyCreationException, IOException {
		String ontology = args[0];
		String phenoclass = args[1];
		String out = args[2];
		File outf = new File(out);
		System.out.println("Extracting signatures of definitions related to " + phenoclass);
		System.out.println("Loading ontology: " + ontology);
		OWLOntology o = OWLManager.createOWLOntologyManager().loadOntology(IRI.create(ontology));
		OWLReasoner r = new ElkReasonerFactory().createReasoner(o);
		System.out.println("Initialising ELK..");
		Set<OWLClass> signature = new HashSet<>();
		if (phenoclass.equals("all")) {
			signature.addAll(o.getClassesInSignature(Imports.INCLUDED));
		} else {
			OWLClass pc = OWLManager.getOWLDataFactory().getOWLClass(IRI.create(phenoclass));
			Set<OWLClass> phenotypes = new HashSet<>();
			System.out.println("Collecting Phenotype Classes..");
			for (OWLClass phenotype : r.getSubClasses(pc, false).getFlattened()) {
				phenotypes.add(phenotype);
			}

			System.out.println("Extracting signature from phenotypes: " + phenotypes.size());
			for (OWLClass phenotype : phenotypes) {
				for (OWLLogicalAxiom ax : o.getAxioms(phenotype, Imports.INCLUDED)) {
					System.out.println(ax);
					signature.addAll(ax.getClassesInSignature());
				}
			}
		}
		System.out.println("Write to file..");
		Set<String> write = signature.stream().map(OWLClass::toString).collect(Collectors.toSet());
		FileUtils.writeLines(outf, write);
	}
}
