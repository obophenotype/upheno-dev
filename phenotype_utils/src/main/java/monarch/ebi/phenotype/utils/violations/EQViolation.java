package monarch.ebi.phenotype.utils.violations;

import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLClassExpression;

import java.util.Map;

public interface EQViolation {
    Map<String,String> report(OWLClassExpression p);
    boolean violatedBy(OWLClassExpression p);
}
