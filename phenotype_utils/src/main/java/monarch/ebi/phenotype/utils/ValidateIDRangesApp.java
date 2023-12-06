package monarch.ebi.phenotype.utils;

import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.vocab.OWLFacet;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;

/**
 * Hello world!
 */
public class ValidateIDRangesApp {

    public static void run(File id_range_file) throws OWLOntologyCreationException {
        OWLOntology o = OWLManager.createOWLOntologyManager().loadOntology(IRI.create(id_range_file));
        List<MyFacet> allMyFacets = new ArrayList<>();
        for(OWLDatatype dt: o.getDatatypesInSignature()) {
            Set<OWLDatatypeDefinitionAxiom> defs = o.getAxioms(dt);
            for(OWLDatatypeDefinitionAxiom ax:defs) {
                OWLDataRange range = ax.getDataRange();

                MyFacet f = new MyFacet();
                f.id = dt.toString();
                range.accept(new OWLDataRangeVisitor() {
                    @Override
                    public void visit(OWLDatatype owlDatatype) {}

                    @Override
                    public void visit(OWLDataOneOf owlDataOneOf) {}

                    @Override
                    public void visit(OWLDataComplementOf owlDataComplementOf) {}

                    @Override
                    public void visit(OWLDataIntersectionOf owlDataIntersectionOf) {}

                    @Override
                    public void visit(OWLDataUnionOf owlDataUnionOf) {}

                    @Override
                    public void visit(OWLDatatypeRestriction owlDatatypeRestriction) {
                        for (OWLFacetRestriction fr:owlDatatypeRestriction.getFacetRestrictions()) {
                            int i = fr.getFacetValue().parseInteger();
                            if(fr.getFacet().equals(OWLFacet.MIN_INCLUSIVE)) {
                                f.min = i;
                            } else if(fr.getFacet().equals(OWLFacet.MAX_INCLUSIVE)) {
                                f.max = i;
                            } else if(fr.getFacet().equals(OWLFacet.MIN_EXCLUSIVE)) {
                                i++;
                                f.min = i;
                            } else if(fr.getFacet().equals(OWLFacet.MAX_EXCLUSIVE)) {
                                i--;
                                f.max = i;
                            } else {
                                log("Unknown range restriction: "+fr);
                            }
                        }
                    }
                });
                log("Testing range: "+f);
                testFacetViolation(f,allMyFacets);
                allMyFacets.add(f);
            }
        }

    }

    private static void testFacetViolation(MyFacet f, List<MyFacet> allMyFacets) {
        for(MyFacet f_p:allMyFacets) {
            if(((f.min<=f_p.max) && (f_p.min <= f.max))) {
                throw new IllegalStateException(f+" overlaps with "+f_p+"!");
            }
        }
    }

    private static void log(Object o) {
        System.out.println(o.toString());
    }


    public static void main(String[] args) throws OWLOntologyCreationException {

        String id_range_path = args[0];

/*
        String id_range_path = "/Users/matentzn/knocean/cell-ontology/src/ontology/cl-idranges.owl";

*/
        File id_range_file = new File(id_range_path);
        run(id_range_file);
    }

    static class MyFacet {
        int min;
        int max;
        String id;

        public String toString() {
            return "Facet{"+id+"}[min:"+min+"; max:"+max+"]";
        }

    }

}
