package monarch.ebi.phenotype.utils;

import org.semanticweb.elk.owlapi.ElkReasonerFactory;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.reasoner.OWLReasoner;
import org.semanticweb.owlapi.reasoner.OWLReasonerFactory;
import org.semanticweb.owlapi.reasoner.structural.StructuralReasonerFactory;
import org.semanticweb.owlapi.search.EntitySearcher;

import java.io.File;
import java.util.*;

/**
 * Hello world!
 */
public class CompareOntologyLinksApp {
    private final File ontology1_file;
    private final File ontology2_file;
    private final boolean allSignature;
    private final IRI subClassIRI = IRI.create("http://www.w3.org/2000/01/rdf-schema#subClassOf");
    private final int printStepSize = 1000;

    private final File data_out;
    private static final OWLDataFactory df = OWLManager.getOWLDataFactory();
    private final OWLAnnotationProperty sourceAp = df.getOWLAnnotationProperty(IRI.create("http://www.geneontology.org/formats/oboInOwl#source"));
    private final OWLClass obsoleteClass = df.getOWLClass(IRI.create("http://www.geneontology.org/formats/oboInOwl#ObsoleteClass"));
    private final Map<LinkBetweenEntity,Map<String,Set<String>>> additionalMetadata = new HashMap<>();
    private final RenderManager ren = RenderManager.getInstance();
    private final OWLReasonerFactory rf;


    private CompareOntologyLinksApp(File ontology1_file, File ontology2_file, OWLReasonerFactory rf , boolean allSignature, File data_out) throws OWLOntologyCreationException {
        this.ontology1_file = ontology1_file;
        this.ontology2_file = ontology2_file;
        this.data_out = data_out;
        this.allSignature = allSignature;
        this.rf = rf;
        run();
    }



    private String categoriseLink(LinkBetweenEntity l, OWLReasoner r, Set<LinkBetweenEntity> allLinks){
        if(allLinks.contains(l)) {
            return "asserted";
        } else if(linkImplied(l,r)) {
           return "inferred";
        } else {
            return "none";
        }
    }

    private void run() throws OWLOntologyCreationException {
        List<Map<String,String>> data = new ArrayList<>();
        OWLOntology o1 = OWLManager.createOWLOntologyManager().loadOntology(IRI.create(ontology1_file));
        OWLOntology o2 = OWLManager.createOWLOntologyManager().loadOntology(IRI.create(ontology2_file));
        OWLReasoner r1 = rf.createReasoner(o1);
        OWLReasoner r2 = rf.createReasoner(o2);
        ren.addLabel(o1);
        ren.addLabel(o2);
        Set<OWLClass> o1_classes = o1.getClassesInSignature();
        Set<OWLClass> o2_classes = o2.getClassesInSignature();
        Set<OWLClass> o1_obsoleted_classes = getObsoletedClasses(o1);
        Set<OWLClass> o2_obsoleted_classes = getObsoletedClasses(o2);
        Set<OWLClass> signature = new HashSet<>(o1_classes);
        if(this.allSignature) {
            signature.addAll(o2_classes);
        } else {
            signature.retainAll(o2_classes);
        }
        Set<LinkBetweenEntity> linkBetweenEntityO1 = getAllAssertedLinksBetweenEntities(o1,signature);
        Set<LinkBetweenEntity> linkBetweenEntityO2 = getAllAssertedLinksBetweenEntities(o2,signature);
        Set<LinkBetweenEntity> union = new HashSet<>(linkBetweenEntityO1);
        union.addAll(linkBetweenEntityO2);
        Set<LinkBetweenEntity> intersection = new HashSet<>(linkBetweenEntityO1);
        intersection.retainAll(linkBetweenEntityO2);
        Set<LinkBetweenEntity> difference = new HashSet<>(union);
        difference.removeAll(intersection);
        log("O1 classes: "+o1_classes.size()+" ("+o1_obsoleted_classes.size()+" obsolete)");
        log("O2 classes: "+o2_classes.size()+" ("+o2_obsoleted_classes.size()+" obsolete)");
        log("O1: "+linkBetweenEntityO1.size());
        log("O2: "+linkBetweenEntityO2.size());
        log("Union: "+union.size());
        log("Intersection: "+intersection.size());
        log("Difference: "+difference.size());
        int ct = 0;
        for(LinkBetweenEntity l:union) {
            ct++;
            if(ct % printStepSize == 0) {
                log(ct+"/"+union.size()+" processed.");
            }
            Map<String,String> rec = new HashMap<>();
            additionalMetadataToRec(l, rec);
            OWLClass c1 = df.getOWLClass(l.e1);
            OWLClass c2 = df.getOWLClass(l.e2);
            OWLObjectProperty p = df.getOWLObjectProperty(l.relation);
            rec.put("o1",ontology1_file.getName());
            rec.put("o2",ontology2_file.getName());
            rec.put("e1",l.e1.toString());
            rec.put("e2",l.e2.toString());
            rec.put("p",l.relation.toString());
            rec.put("e1_label",RenderManager.getInstance().getLabel(c1));
            rec.put("e2_label",RenderManager.getInstance().getLabel(c2));
            rec.put("p_label",RenderManager.getInstance().getLabel(p));
            rec.put("e1_sig",includedInOntology(o1_classes, o2_classes, c1));
            rec.put("e2_sig",includedInOntology(o1_classes, o2_classes, c2));
            rec.put("e1_obsolete",includedInOntology(o1_obsoleted_classes, o2_obsoleted_classes, c1));
            rec.put("e2_obsolete",includedInOntology(o1_obsoleted_classes, o2_obsoleted_classes, c2));
            String categorise_o1 = classifyEntity(r1, linkBetweenEntityO1, l, rec);
            String categorise_o2 = classifyEntity(r2, linkBetweenEntityO2, l, rec);
            rec.put("o1_link",categorise_o1);
            rec.put("o2_link",categorise_o2);
            data.add(rec);
        }
        Export.writeCSV(data,data_out);
    }

    private void additionalMetadataToRec(LinkBetweenEntity l, Map<String, String> rec) {
        if(additionalMetadata.containsKey(l)) {
            for(String key:additionalMetadata.get(l).keySet()) {
                rec.put(key,String.join("|", additionalMetadata.get(l).get(key)));
            }
        }
    }

    private Set<OWLClass> getObsoletedClasses(OWLOntology o) {
        Set<OWLClass> obsoleted = new HashSet<>();
        OWLAnnotationProperty ap = df.getOWLDeprecated();
        for(OWLClass c:o.getClassesInSignature()) {
            Collection<OWLAnnotation> annotations = EntitySearcher.getAnnotations(c, o, ap);
            boolean obsoletedB = isDeclaredToBeDeprecated(annotations);
            if(!obsoletedB) {
                obsoletedB = isChildOfObsoleteClass(o, obsoleteClass, c);
            }
            if(obsoletedB) {
                obsoleted.add(c);
            }
        }
        return obsoleted;
    }

    private boolean isChildOfObsoleteClass(OWLOntology o, OWLClass obsoleteClass, OWLClass c) {
        Collection<OWLClassExpression> parents = EntitySearcher.getSuperClasses(c, o);
        for(OWLClassExpression ce:parents) {
            if(ce.equals(obsoleteClass)) {
                return true;
            }
        }
        return false;
    }

    private boolean isDeclaredToBeDeprecated(Collection<OWLAnnotation> annotations) {
        for(OWLAnnotation a: annotations) {
            OWLAnnotationValue val = a.getValue();
            if(val.isLiteral()) {
                com.google.common.base.Optional<OWLLiteral> l = val.asLiteral();
                if(l.isPresent()) {
                    if(l.get().isBoolean()) {
                        if(l.get().parseBoolean()) {
                            return true;
                        }
                    }
                }
            }
        }
        return false;
    }

    private String classifyEntity(OWLReasoner r, Set<LinkBetweenEntity> linkBetweenEntities, LinkBetweenEntity l, Map<String, String> rec) {
        String categorise = categoriseLink(l, r, linkBetweenEntities);
        if(categorise.equals("none")) {
            Optional<LinkBetweenEntity> ol = getLinkDifferentRelation(l, linkBetweenEntities);
            if(ol.isPresent()) {
                categorise = "rewired";
                rec.put("p_rewired",ol.get().relation.toString());
            }
        }
        return categorise;
    }

    private String includedInOntology(Set<OWLClass> o1_classes, Set<OWLClass> o2_classes, OWLClass c) {
        if(o1_classes.contains(c)) {
            if(o2_classes.contains(c)) {
                return "both";
            } else {
                return "o1";
            }
        } else if (o2_classes.contains(c)) {
            return "o2";
        } else {
            return "none";
        }
    }

    private Optional<LinkBetweenEntity> getLinkDifferentRelation(LinkBetweenEntity l, Set<LinkBetweenEntity> set) {
        for(LinkBetweenEntity l2:set) {
            if(l.e1.equals(l2.e1) && l.e2.equals(l2.e2)) {
                return Optional.of(l2);
            }
        }
        return Optional.empty();
    }

    private boolean linkImplied(LinkBetweenEntity l, OWLReasoner r) {
        OWLAxiom ax;
        if(l.relation.equals(subClassIRI)) {
            ax = df.getOWLSubClassOfAxiom(df.getOWLClass(l.e1),df.getOWLClass(l.e2));
        } else {
            // we assume its and existential restricton.
            ax = df.getOWLSubClassOfAxiom(df.getOWLClass(l.e1),df.getOWLObjectSomeValuesFrom(df.getOWLObjectProperty(l.relation),df.getOWLClass(l.e2)));
        }
        return r.isEntailed(ax);
    }

    @SuppressWarnings("SuspiciousMethodCalls")
    private Set<LinkBetweenEntity> getAllAssertedLinksBetweenEntities(OWLOntology o, Set<OWLClass> signature) {
        Set<LinkBetweenEntity> links = new HashSet<>();
        for(OWLAxiom ax:o.getLogicalAxioms()) {
            if(ax instanceof OWLSubClassOfAxiom) {
                OWLSubClassOfAxiom sax = (OWLSubClassOfAxiom)ax;
                OWLClassExpression sub = sax.getSubClass();
                OWLClassExpression sup = sax.getSuperClass();
                if(sub.isClassExpressionLiteral()) {
                    if (signature.contains(sub)) {
                        if (sup.isClassExpressionLiteral() && signature.contains(sup)) {
                            LinkBetweenEntity l = new LinkBetweenEntity(sub.asOWLClass().getIRI(), sup.asOWLClass().getIRI(), subClassIRI);
                            addMetadata(l,"source",getSource(ax.getAnnotations(sourceAp)));
                            links.add(l);
                        } else {
                            if (sub instanceof OWLObjectSomeValuesFrom) {
                                OWLObjectSomeValuesFrom osub = (OWLObjectSomeValuesFrom) sub;
                                OWLObjectPropertyExpression property = osub.getProperty();
                                OWLClassExpression object = osub.getFiller();
                                if (object.isClassExpressionLiteral() && !property.isAnonymous() && signature.contains(object)) {
                                    LinkBetweenEntity l = new LinkBetweenEntity(sub.asOWLClass().getIRI(), object.asOWLClass().getIRI(), osub.getProperty().asOWLObjectProperty().getIRI());
                                    addMetadata(l,"source",getSource(ax.getAnnotations(sourceAp)));
                                    links.add(l);
                                }
                            }
                        }
                    }
                }
            }
        }
        return links;
    }

    private void addMetadata(LinkBetweenEntity l, String k, String v) {
        if(!additionalMetadata.containsKey(l)) {
            additionalMetadata.put(l,new HashMap<>());
        }
        if(!additionalMetadata.get(l).containsKey(k)) {
            additionalMetadata.get(l).put(k,new HashSet<>());
        }
        additionalMetadata.get(l).get(k).add(v);
    }

    private String getSource(Set<OWLAnnotation> sourceAnnotations) {
        Set<String> sources = new HashSet<>();
        for(OWLAnnotation anno:sourceAnnotations) {
            if(anno.getProperty().equals(sourceAp)) {
                OWLAnnotationValue val = anno.getValue();
                if(val.isLiteral()) {
                    com.google.common.base.Optional<OWLLiteral> l = val.asLiteral();
                    if(l.isPresent()) {
                        if(l.get().isLiteral()) {
                            String source = l.get().getLiteral().trim();
                            if(!source.isEmpty()) {
                                sources.add(source);
                            }
                        }
                    }
                }
            }
        }
        return String.join("|", sources);
    }


    private void log(Object o) {
        System.out.println(o.toString());
    }


    public static void main(String[] args) throws OWLOntologyCreationException {

        String ontology1_path = args[0];
        String ontology2_path = args[1];
        boolean all_signature = args[2].equals("all");
        String reasoner = args[3];
        String data_out = args[4];

        OWLReasonerFactory rf;
        switch (reasoner){
            case "elk":
                rf = new ElkReasonerFactory();
                break;
            case "structural":
                rf = new StructuralReasonerFactory();
                break;
            default:
                rf = new ElkReasonerFactory();
                break;
        }

        /*
        String ontology1_path = "/Users/matentzn/ws/mondo-analysis/sources/mondo.owl";
        String ontology2_path = "/Users/matentzn/ws/mondo-analysis/mondo_translate/omim.owl";
        String data_out = "/Users/matentzn/ws/mondo-analysis/mondo_translate/mondo-omim-analysis.csv";
        boolean all_signature = true;
 */

        File ontology1_file = new File(ontology1_path);
        File ontology2_file = new File(ontology2_path);
        File ontology_out = new File(data_out);

        new CompareOntologyLinksApp(ontology1_file, ontology2_file, rf, all_signature, ontology_out);
    }

}
