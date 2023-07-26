package monarch.ebi.phenotype.utils;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.semanticweb.owlapi.model.OWLClass;

public class FillerData {
    private final String pattern;
    private Map<Filler,List<OWLClass>> fillers = new HashMap<>();
    public FillerData(String pattern) {
		this.pattern = pattern;
	}
	public String getPattern() {
        return pattern;
    }
	
	public void addFiller(Filler filler,List<OWLClass> f) {
		fillers.put(filler,f);
	}
	
	@Override
	public String toString() {
		return "FillerData [pattern=" + pattern + ", fillers=" + fillers + "]";
	}
	public boolean isEmpty() {
		return fillers.isEmpty();
	}
	public Map<Filler,List<OWLClass>> getFillers() {
		return fillers;
	}
	
}
