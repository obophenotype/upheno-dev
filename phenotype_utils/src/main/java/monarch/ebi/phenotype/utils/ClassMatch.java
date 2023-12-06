package monarch.ebi.phenotype.utils;

import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLClassExpression;

import java.util.*;

public class ClassMatch implements Match {
    private OWLClass cl1;
    private OWLClass cl2;

    private Map<String,Double> values = new HashMap<>();

    ClassMatch(OWLClass cl1, OWLClass cl2) {
        this.cl1=cl1;
        this.cl2=cl2;
    }

    @Override
    public OWLClassExpression getLeftMatch() {
        return cl1;
    }

    @Override
    public OWLClassExpression getRightMatch() {
        return cl2;
    }

    @Override
    public void setValue(String s, double v) {
        values.put(s,v);
    }

    @Override
    public Map<String, Double> getData() {
        return values;
    }
}
