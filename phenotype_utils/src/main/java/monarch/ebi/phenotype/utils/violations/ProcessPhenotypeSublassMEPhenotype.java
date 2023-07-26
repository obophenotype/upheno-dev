package monarch.ebi.phenotype.utils.violations;

import monarch.ebi.phenotype.utils.Entities;
import monarch.ebi.phenotype.utils.OntologyUtils;
import monarch.ebi.phenotype.utils.RenderManager;
import org.semanticweb.elk.util.collections.FList;
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

public class ProcessPhenotypeSublassMEPhenotype implements EQViolation {

    private OWLReasoner elk;
    private OWLDataFactory df = OWLManager.getOWLDataFactory();
    private Map<OWLClassExpression, Map<String,String>> reports = new HashMap<>();

    public ProcessPhenotypeSublassMEPhenotype(OWLReasoner elk, Set<OWLClass> phenotypes) {
        this.elk = elk;
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
        String ps = RenderManager.getInstance().render(p);
        boolean violates = false;
        if(!elk.isSatisfiable(p)) {
            return violates;
        }
        if(isProcessPhenotype(p) && !isMEPhenotype(p)) {
            for(OWLClass sub: getSubs(p, elk, true)) {
                OWLClassExpression eqsub = OntologyUtils.getEQ(elk.getRootOntology(),sub);
                if(eqsub!=null) {
                    if (isMEPhenotype(sub) && elk.isSatisfiable(sub) && !isProcessPhenotype(eqsub)) {
                        String msg = String.format("(%s) is process phenotype and superclass of anatomy phenotype %s (%s) \n", RenderManager.getInstance().render(p), RenderManager.getInstance().render(sub), RenderManager.getInstance().render(eqsub));

                        if(isDevelopmentPhenotype(sub)) {
                            addViolation(p, "super_developmental_sub_me", msg);
                        } else if(isHomeostaticPhenotype(sub)) {
                            addViolation(p, "super_homeostatic_sub_me", msg);
                        } else if(isPigmentationPhenotype(sub)) {
                            addViolation(p, "super_pigmentation_sub_me", msg);
                        } else {
                            addViolation(p,"super_process_sub_me",msg);
                        }
                        violates = true;
                        //System.out.println(msg);
                    }
                }
            }
        }
        if(isMEPhenotype(p) && !isProcessPhenotype(p)) {
            for(OWLClass sub: getSubs(p, elk, true)) {
                OWLClassExpression eqsub = OntologyUtils.getEQ(elk.getRootOntology(),sub);
                if(eqsub!=null) {
                    if (isProcessPhenotype(sub) && elk.isSatisfiable(sub) && !isMEPhenotype(eqsub)) {
                        String msg = String.format("(%s) is anatomy phenotype and superclass of process phenotype %s (%s) \n", RenderManager.getInstance().render(p), RenderManager.getInstance().render(sub), RenderManager.getInstance().render(eqsub));
                        if(isDevelopmentPhenotype(sub)) {
                            addViolation(p, "super_me_sub_development", msg);
                        } else if(isHomeostaticPhenotype(sub)) {
                            addViolation(p, "super_me_sub_homeostatic", msg);
                        } else if(isPigmentationPhenotype(sub)) {
                            addViolation(p, "super_me_sub_pigmentation", msg);
                        } else {
                            addViolation(p, "super_me_sub_process", msg);
                        }
                        violates = true;
                        //System.out.println(msg);
                    }
                }
            }
        }
        return violates;
    }

    private boolean isDevelopmentPhenotype(OWLClass sub) {
        return isXPhenotype(sub,Entities.developmentalPhenotype);
    }

    private boolean isHomeostaticPhenotype(OWLClass sub) {
        return isXPhenotype(sub,Entities.homeostatisPhenotype);
    }

    private boolean isPigmentationPhenotype(OWLClass sub) {
        return isXPhenotype(sub,Entities.pigmentationPhenotype);
    }

    private void addViolation(OWLClassExpression p, String cat, String msg) {
        if(!reports.containsKey(p)) {
            reports.put(p, new HashMap<>());
        }
        reports.get(p).put(cat,msg);
    }

    private Set<OWLClass> getSubs(OWLClassExpression p, OWLReasoner elk, boolean b) {
        Set<OWLClass> subs = new HashSet<>(elk.getSubClasses(p, b).getFlattened());
        return subs;
    }

    private boolean isMEPhenotype(OWLClassExpression p) {
        return isXPhenotype(p,Entities.materialEntityPhenotype);
    }

    private boolean isProcessPhenotype(OWLClassExpression p) {
        return isXPhenotype(p,Entities.processPhenotype);
    }

    private boolean isXPhenotype(OWLClassExpression p, OWLClassExpression xPhenotype) {
        OWLSubClassOfAxiom sbcl;
        if(p.isClassExpressionLiteral()) {
            sbcl = df.getOWLSubClassOfAxiom(p,xPhenotype);
        } else {
            OWLClassExpression bearerIn = OntologyUtils.extractBearerFromEQ(p);
            OWLClassExpression bearerX = OntologyUtils.extractBearerFromEQ(xPhenotype);
            if(bearerIn==null) {
                return false;
            }
            sbcl = df.getOWLSubClassOfAxiom(bearerIn, bearerX);
        }
        return elk.isEntailed(sbcl);
    }
}
