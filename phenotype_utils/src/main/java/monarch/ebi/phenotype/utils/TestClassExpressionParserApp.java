package monarch.ebi.phenotype.utils;

import org.apache.commons.io.FileUtils;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.dlsyntax.renderer.DLSyntaxObjectRenderer;
import org.semanticweb.owlapi.expression.OWLEntityChecker;
import org.semanticweb.owlapi.expression.ShortFormEntityChecker;
import org.semanticweb.owlapi.manchestersyntax.parser.ManchesterOWLSyntaxInlineAxiomParser;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.model.parameters.Imports;
import org.semanticweb.owlapi.util.mansyntax.ManchesterOWLSyntaxParser;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * Hello world!
 */
public class TestClassExpressionParserApp {

    public static void main(String[] args)  {
        OWLDataFactory df = OWLManager.getOWLDataFactory();

        OWLObjectProperty R = df.getOWLObjectProperty(IRI.create("http://purl.obolibrary.org/obo/R"));
        OWLClass C = df.getOWLClass(IRI.create("http://purl.obolibrary.org/obo/C"));
        DLSyntaxObjectRenderer ren = new DLSyntaxObjectRenderer();

        Map<String, OWLEntity> entities = new HashMap<>();
        entities.put(R.getIRI().toString(), R);
        entities.put(C.getIRI().toString(), C);

        ManchesterOWLSyntaxParser parser = OWLManager.createManchesterParser();
        parser.setOWLEntityChecker(new OWLEntityChecker() {

            @Override
            public OWLObjectProperty getOWLObjectProperty(String name) {
                OWLEntity o = entities.get(name);
                if (o != null && o.isOWLObjectProperty()) {
                    return o.asOWLObjectProperty();
                }
                return null;
            }

            @Override
            public OWLNamedIndividual getOWLIndividual(String name) {
                return null;
            }

            @Override
            public OWLDatatype getOWLDatatype(String name) {
                return null;
            }

            @Override
            public OWLDataProperty getOWLDataProperty(String name) {
                return null;
            }

            @Override
            public OWLClass getOWLClass(String name) {
                OWLEntity o = entities.get(name);
                if (o != null && o.isOWLClass()) {
                    return o.asOWLClass();
                }
                return null;
            }

            @Override
            public OWLAnnotationProperty getOWLAnnotationProperty(String name) {
                return null;
            }
        });

        String manchester = String.format("%s some %s",R.getIRI(),C.getIRI());
        parser.setStringToParse(manchester);

        OWLClassExpression ce = parser.parseClassExpression();
        if(ce.equals(df.getOWLObjectSomeValuesFrom(R,C))) {
            System.out.println(ren.render(ce));
            System.out.println("succeeded.");
        }
    }

}
