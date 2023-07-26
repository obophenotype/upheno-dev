package monarch.ebi.phenotype.utils.violations;

import monarch.ebi.phenotype.utils.Entities;
import monarch.ebi.phenotype.utils.RenderManager;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLClassExpression;
import org.semanticweb.owlapi.model.OWLDataFactory;
import org.semanticweb.owlapi.model.OWLSubClassOfAxiom;
import org.semanticweb.owlapi.reasoner.OWLReasoner;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public class PhysicalQualityInheresInProcessViolation implements EQViolation {

    private OWLDataFactory df = OWLManager.getOWLDataFactory();
    private Map<OWLClassExpression,Map<String,String>> reports = new HashMap<>();
    private OWLClassExpression illegal;
    private OWLReasoner r;

    public PhysicalQualityInheresInProcessViolation(OWLReasoner r) {
        OWLClassExpression INE = df.getOWLObjectSomeValuesFrom(Entities.inheres_in_part_of,Entities.cl_go_biological_process);
        OWLClassExpression QINE = df.getOWLObjectIntersectionOf(Entities.cl_pato_physical_quality,INE);
        this.r = r;
        illegal = df.getOWLObjectSomeValuesFrom(Entities.haspart,QINE);
    }

    @Override
    public Map<String,String> report(OWLClassExpression c) {
        if(reports.containsKey(c)) {
            return reports.get(c);
        }
        return new HashMap<>();
    }

    @Override
    public boolean violatedBy(OWLClassExpression p) {
        OWLSubClassOfAxiom sbcl = df.getOWLSubClassOfAxiom(p,illegal);
        boolean violation = false;
        if(r.isEntailed(sbcl)) {
            violation = true;
        }
        if(violation) {
            Map<String,String> rec  = new HashMap<>();
            rec.put("physical_quality_in_process","* Phenotype with a pysical quality that inheres in a process: "+ RenderManager.getInstance().render(p));
            reports.put(p,rec);
            return true;
        }
        return false;
    }
}
