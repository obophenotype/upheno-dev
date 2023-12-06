package monarch.ebi.phenotype.utils;

import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.model.parameters.Imports;
import org.semanticweb.owlapi.reasoner.OWLReasoner;
import org.semanticweb.owlapi.search.EntitySearcher;
import org.semanticweb.owlapi.util.OWLObjectTransformer;

import java.util.*;
import java.util.stream.Collectors;

public class OntologyUtils {

    private static OWLDataFactory df = OWLManager.getOWLDataFactory();

    public static void p(Object label) {
        System.out.println(label);
    }

    public static Set<String> getLabels(OWLEntity c, OWLOntology o) {

        Set<OWLAnnotationProperty> annops = new HashSet<>();
        annops.add(df.getRDFSLabel());
        annops.add(df.getOWLAnnotationProperty(IRI.create("http://www.w3.org/2004/02/skos/core#prefLabel")));
        annops.add(df.getOWLAnnotationProperty(IRI.create("http://www.w3.org/2004/02/skos/core#altLabel")));
        annops.add(df.getOWLAnnotationProperty(IRI.create("http://www.geneontology.org/formats/oboInOwl#hasExactSynonym")));

        return getLabels(c, o, annops);
    }

    public static Set<String> getLabelsRDFS(OWLEntity c, OWLOntology o) {
        Set<OWLAnnotationProperty> annops = new HashSet<>();
        annops.add(df.getRDFSLabel());
        return getLabels(c, o, annops);
    }

    public static Set<String> getLabelsRDFSIfExistsElseOther(OWLEntity c, OWLOntology o) {
        Set<String> labels = getLabelsRDFS(c,o);
        if(labels.isEmpty()) {
            labels = getLabels(c,o);
        }
        return labels;
    }

    public static boolean isObsolete(OWLEntity c, OWLOntology o) {
        Set<String> labels = getLabels(c,o,new HashSet<>(Collections.singleton(df.getOWLDeprecated())));
        if(!labels.isEmpty()) {
            return new ArrayList<>(labels).get(0).equals("true");
        }
        return false;
    }



    private static Set<String> getLabels(OWLEntity c, OWLOntology o, Set<OWLAnnotationProperty> annops) {
        Set<String> labels = new HashSet<>();
        for(OWLOntology i:o.getImportsClosure()) {
            for(OWLAnnotationProperty annop:annops) {
                for (OWLAnnotation a : EntitySearcher.getAnnotations(c, i, annop)) {
                    OWLAnnotationValue value = a.getValue();
                    if (value instanceof OWLLiteral) {
                        String val = ((OWLLiteral) value).getLiteral();
                        labels.add(val);
                    }
                }
            }
        }
        return labels;
    }

    private static  Map<OWLAnnotationProperty,Set<String>> getAllAnnotations(OWLEntity c, OWLOntology o, Set<OWLAnnotationProperty> annops) {
        Map<OWLAnnotationProperty,Set<String>> labels = new HashMap<>();
        for(OWLOntology i:o.getImportsClosure()) {
            for(OWLAnnotationProperty annop:annops) {
                labels.put(annop,new HashSet<>());

                for (OWLAnnotation a : EntitySearcher.getAnnotations(c, i, annop)) {
                    OWLAnnotationValue value = a.getValue();
                    if (value instanceof OWLLiteral) {
                        String val = ((OWLLiteral) value).getLiteral();
                        labels.get(annop).add(val);
                    }
                }
            }
        }
        return labels;
    }

    public static OWLClassExpression getEQ(OWLOntology o, OWLClass p) {
        for(OWLEquivalentClassesAxiom ax:o.getAxioms(AxiomType.EQUIVALENT_CLASSES)) {
            if(ax.getNamedClasses().contains(p)) {
                for(OWLClassExpression ce:ax.getClassExpressions()) {
                    if(ce.isAnonymous()) {
                        return ce;
                    }
                }
            }
        }
        return null;
    }
    public static OWLClassExpression getHasAffectedEntity(OWLOntology o, OWLClass p) {
        for(OWLAxiom ax:o.getAxioms(p, Imports.INCLUDED)) {
            if (ax instanceof OWLSubClassOfAxiom) {
                OWLSubClassOfAxiom sbcl = (OWLSubClassOfAxiom) ax;
                OWLClassExpression superCe = sbcl.getSuperClass();
                OWLClassExpression svf = extractBearerFromEQ(superCe);
                if (svf != null) return svf;
            }
        }
        return null;
    }

    public static OWLClassExpression extractBearerFromEQ(OWLClassExpression ce) {
        if (ce instanceof OWLObjectSomeValuesFrom) {
            OWLObjectSomeValuesFrom haspart = (OWLObjectSomeValuesFrom) ce;
            OWLClassExpression haspart_filler = haspart.getFiller();
            if (haspart_filler instanceof OWLObjectIntersectionOf) {
                OWLObjectIntersectionOf has_part_intersection = (OWLObjectIntersectionOf) haspart_filler;
                for (OWLClassExpression has_part_intersection_operand : has_part_intersection.getOperands()) {
                    if (has_part_intersection_operand instanceof OWLObjectSomeValuesFrom) {
                        OWLObjectSomeValuesFrom bearer_expression = (OWLObjectSomeValuesFrom) has_part_intersection_operand;
                        if (!bearer_expression.getProperty().isAnonymous()) {
                            OWLObjectProperty ii_po = bearer_expression.getProperty().asOWLObjectProperty();
                            if (ii_po.equals(Entities.inheres_in) || ii_po.equals(Entities.inheres_in_part_of)) {
                                OWLClassExpression bearer_filler = bearer_expression.getFiller();
                                return bearer_filler;
                            }
                        }
                    }
                }
            }
        }
        return null;
    }

    public static Set<OWLClass> getSubClasses(Set<OWLClass> roots, OWLReasoner r) {
        Set<OWLClass> subs = new HashSet<>();
        for(OWLEntity e:roots) {
            if(e instanceof OWLClass) {
                subs.addAll(r.getSubClasses((OWLClass)e,false).getFlattened());
            }
        }
        return subs;
    }

    public static String getRandomLabelIfAny(OWLEntity e,OWLOntology o) {
        for(String l:getLabels(e,o)) {
            return l;
        }
        return e.getIRI().getRemainder().or(e.getIRI().toString());
    }


    public static void replaceAllClassExpressions(OWLOntology o, Map<OWLClassExpression, OWLClassExpression> replacements) {
        OWLObjectTransformer<OWLClassExpression> replacer = new OWLObjectTransformer<>((x) -> true,
                (input) -> {
                    OWLClassExpression l = replacements.get(input);
                    if (l == null) {
                        return input;
                    }
                    return l;
                }, df, OWLClassExpression.class);

        List<OWLOntologyChange> results = replacer.change(o);
        o.getOWLOntologyManager().applyChanges(results);
    }


    public static Set<String> getRDFSDescription(OWLEntity c, OWLOntology o) {
        Set<OWLAnnotationProperty> annops = new HashSet<>();
        annops.add(df.getOWLAnnotationProperty(IRI.create("http://purl.obolibrary.org/obo/IAO_0000115")));
        Set<String> labels = getLabels(c, o, annops);
        if(labels.isEmpty()) {
            annops.add(df.getRDFSComment());
            return getLabels(c,o,annops);
        }
        return labels;
    }
}
