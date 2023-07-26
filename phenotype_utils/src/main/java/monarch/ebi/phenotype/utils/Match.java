package monarch.ebi.phenotype.utils;

import org.semanticweb.owlapi.model.OWLClassExpression;

import java.util.Map;

public interface Match {
    OWLClassExpression getLeftMatch();
    OWLClassExpression getRightMatch();

    void setValue(String jaccard, double jacc);

    Map<String, Double> getData();
}
