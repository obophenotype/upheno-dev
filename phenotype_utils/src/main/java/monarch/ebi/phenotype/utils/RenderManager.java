package monarch.ebi.phenotype.utils;

import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.dlsyntax.renderer.DLSyntaxObjectRenderer;
import org.semanticweb.owlapi.io.OWLObjectRenderer;
import org.semanticweb.owlapi.manchestersyntax.renderer.ManchesterOWLSyntaxOWLObjectRendererImpl;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.model.parameters.Imports;
import org.semanticweb.owlapi.reasoner.OWLReasoner;

import java.util.*;

public class RenderManager {

    private OWLObjectRenderer ren = new DLSyntaxObjectRenderer();
    private OWLObjectRenderer renManchester = new ManchesterOWLSyntaxOWLObjectRendererImpl();

    private Map<OWLEntity, String> labels = new HashMap<>();
    private Map<OWLEntity, String> descriptions = new HashMap<>();
    private OWLDataFactory df = OWLManager.getOWLDataFactory();

    private static RenderManager instance = null;


    private RenderManager() {
    }

    public static RenderManager getInstance() {
        if(instance==null) {
            instance = new RenderManager();
        }
        return instance;
    }

    public void addLabel(OWLOntology o) {
        o.getSignature(Imports.INCLUDED).forEach(s -> OntologyUtils.getLabelsRDFSIfExistsElseOther(s, o).forEach(l -> labels.put(s, hackLabel(s,l))));
        o.getSignature(Imports.INCLUDED).forEach(s -> OntologyUtils.getRDFSDescription(s, o).forEach(l -> descriptions.put(s, l)));
    }

    private String hackLabel(OWLEntity e,String l) {
        if(e.equals(df.getOWLThing())) {
            return replaceIRIWithLabel(l, df.getOWLThing(), "Thing");
        } else {
            return l;
        }
    }

    public void clear() {
        labels.clear();
    }

    public String render(OWLObject ax) {
        String s = ren.render(ax);
        for (OWLEntity k : ax.getSignature()) {
            String l = getLabel(k);
            s = replaceIRIWithLabel(s, k, l);
        }
        return s;
    }

    public String renderManchester(OWLObject ax) {
        String s = renManchester.render(ax);
        for (OWLEntity k : ax.getSignature()) {
            String l = getLabel(k);
            s = replaceIRIWithLabel(s, k, l);
        }
        return s;
    }

    private String replaceIRIWithLabel(String s, OWLEntity k, String l) {
        return s.replaceAll(k.getIRI().getRemainder().or(""), "'"+l+"'");
    }

    public String getLabel(OWLEntity k) {
        return labels.get(k) == null ? k.getIRI().getRemainder().or("") : labels.get(k);
    }

    public String renderForMarkdown(OWLObject ax) {
        return renderManchester(ax).replaceAll("(\n|\r\n|\r)", "  \n");
    }

    public void renderTreeForMarkdown(OWLClass c, OWLReasoner r, List<String> sb, int level, Set<OWLEntity> k, Map<OWLClass,OWLClassExpression> g, Set<OWLClass> u) {
        for (OWLClass sub : r.getSubClasses(c, true).getFlattened()) {
            if(sub.equals(df.getOWLNothing())) {
              continue;
            }
            String repeated = new String(new char[level]).replace("\0", "  ");
            sb.add(repeated+  " * " + renderTreeEntity(sub,k,g,u));
            renderTreeForMarkdown(sub, r, sb, level + 1,k,g,u);
        }
    }

    public void renderTreeForMarkdown(OWLClass c, OWLReasoner r, List<String> sb, int level) {
        for (OWLClass sub : r.getSubClasses(c, true).getFlattened()) {
            String repeated = new String(new char[level]).replace("\0", "  ");
            sb.add(repeated+  " * " + renderTreeEntity(sub,new HashSet<>(),new HashMap<>(),new HashSet<>()));
            renderTreeForMarkdown(sub, r, sb, level + 1,new HashSet<>(),new HashMap<>(),new HashSet<>());
        }
    }

    public String renderTreeEntity(OWLClass sub, Set<OWLEntity> keyentities, Map<OWLClass,OWLClassExpression> generated, Set<OWLClass> unsatisfiable) {
        String base = getLabel(sub);
        if (keyentities.contains(sub)) {
            base = "(" + base + ")";
        }
        if (generated.containsKey(sub)) {
            base = base+" ["+ render(generated.get(sub)) + "]";
        }
        if (unsatisfiable.contains(sub)) {
            base = "{" + base + "}";
        }
        return base;
    }

    public String stripKnownIRIs(String name) {
        String s = name.replace("http://purl.obolibrary.org/obo/","");
        s = s.replace("https://raw.githubusercontent.com/","");
        s = s.replaceAll("master/releases/","");
        return s;
    }

    public String getDescription(OWLClass k) {
        return descriptions.get(k) == null ? "No description" : descriptions.get(k);
    }
}
