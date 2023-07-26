package monarch.ebi.phenotype.utils;

import org.semanticweb.owlapi.model.OWLClass;

public class Filler {

	@Override
	public String toString() {
		return "Filler [iri=" + iri + ", column=" + column + "]";
	}

	final private OWLClass iri;
	final private String column;

	Filler(OWLClass iri, String column) {
		this.iri = iri;
		this.column = column;
	}

	public OWLClass getOWLClass() {
		return iri;
	}

	public String getColumn() {
		return column;
	}

}
