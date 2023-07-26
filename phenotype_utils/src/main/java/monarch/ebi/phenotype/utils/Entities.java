package monarch.ebi.phenotype.utils;

import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;

public class Entities {
    public static OWLDataFactory df = OWLManager.getOWLDataFactory();
    public static final OWLObjectProperty haspart = df.getOWLObjectProperty(IRI.create("http://purl.obolibrary.org/obo/BFO_0000051"));
    public static final OWLObjectProperty present_in_taxon = df.getOWLObjectProperty(IRI.create("http://purl.obolibrary.org/obo/RO_0002175"));
    public static final OWLObjectProperty inheres_in = df.getOWLObjectProperty(IRI.create("http://purl.obolibrary.org/obo/RO_0000052"));
    public static final OWLObjectProperty inheres_in_part_of = df.getOWLObjectProperty(IRI.create("http://purl.obolibrary.org/obo/RO_0002314"));
    public static final OWLObjectProperty has_phenotype_affecting = df.getOWLObjectProperty(IRI.create("http://purl.obolibrary.org/obo/UPHENO_0000001"));
    public static final OWLAnnotationProperty has_associated_entity = df.getOWLAnnotationProperty(IRI.create("http://purl.obolibrary.org/obo/UPHENO_0000003"));
    public static final OWLAnnotationProperty has_phenotypic_analogue = df.getOWLAnnotationProperty(IRI.create("http://purl.obolibrary.org/obo/UPHENO_0000002"));

    public static String OBOPURLSTRING = "http://purl.obolibrary.org/obo/";
    public static final OWLAnnotationProperty ap_xref = df.getOWLAnnotationProperty(IRI.create("http://www.geneontology.org/formats/oboInOwl#hasDbXref"));
    public static final OWLClass cl_go_biological_process = df.getOWLClass(IRI.create("http://purl.obolibrary.org/obo/GO_0008150"));
    public static final OWLClass cl_uberon_anatomical_entity = df.getOWLClass(IRI.create("http://purl.obolibrary.org/obo/UBERON_0001062"));
    public static final OWLClass cl_upheno_phenotype = df.getOWLClass(IRI.create("http://purl.obolibrary.org/obo/UPHENO_0001001"));
    public static final OWLClass cl_pato_quality = df.getOWLClass(IRI.create("http://purl.obolibrary.org/obo/PATO_0000001"));
    public static final OWLClass cl_pato_physical_quality = df.getOWLClass(IRI.create("http://purl.obolibrary.org/obo/PATO_0001241"));
    public static final OWLClass cl_pato_process_quality = df.getOWLClass(IRI.create("http://purl.obolibrary.org/obo/PATO_0001236"));
    public static final OWLClass cl_pato_qualitative_quality = df.getOWLClass(IRI.create("http://purl.obolibrary.org/obo/PATO_0000068"));
    public static final OWLClass cl_go_homeostasis = df.getOWLClass(IRI.create("http://purl.obolibrary.org/obo/GO_0042592"));
    public static final OWLClass cl_go_development = df.getOWLClass(IRI.create("http://purl.obolibrary.org/obo/GO_0032502"));
    public static final OWLClass cl_go_pigmentation = df.getOWLClass(IRI.create("http://purl.obolibrary.org/obo/GO_0043473"));
    public static final OWLClassExpression INE = df.getOWLObjectSomeValuesFrom(Entities.inheres_in_part_of,df.getOWLThing());
    public static final OWLClassExpression INBP = df.getOWLObjectSomeValuesFrom(Entities.inheres_in_part_of,cl_go_biological_process);
    public static final OWLClassExpression INME = df.getOWLObjectSomeValuesFrom(Entities.inheres_in_part_of,cl_uberon_anatomical_entity);
    public static final OWLClassExpression INHOMEO = df.getOWLObjectSomeValuesFrom(Entities.inheres_in_part_of,cl_go_homeostasis);
    public static final OWLClassExpression INDEVELOPMENT = df.getOWLObjectSomeValuesFrom(Entities.inheres_in_part_of,cl_go_development);
    public static final OWLClassExpression INPIGMENT = df.getOWLObjectSomeValuesFrom(Entities.inheres_in_part_of,cl_go_pigmentation);
    public static final OWLClassExpression QINE = df.getOWLObjectIntersectionOf(Entities.cl_pato_quality,INE);
    public static final OWLClassExpression QINBP = df.getOWLObjectIntersectionOf(Entities.cl_pato_quality,INBP);
    public static final OWLClassExpression QINME = df.getOWLObjectIntersectionOf(Entities.cl_pato_quality,INME);
    public static final OWLClassExpression QINHOMEO = df.getOWLObjectIntersectionOf(Entities.cl_pato_quality,INHOMEO);
    public static final OWLClassExpression QINDEVELOP = df.getOWLObjectIntersectionOf(Entities.cl_pato_quality,INDEVELOPMENT);
    public static final OWLClassExpression QINPIGMENT = df.getOWLObjectIntersectionOf(Entities.cl_pato_quality,INPIGMENT);
    public static final OWLClassExpression phenotype = df.getOWLObjectSomeValuesFrom(Entities.haspart,QINE);
    public static final OWLClassExpression processPhenotype = df.getOWLObjectSomeValuesFrom(Entities.haspart,QINBP);
    public static final OWLClassExpression materialEntityPhenotype = df.getOWLObjectSomeValuesFrom(Entities.haspart,QINME);
    public static final OWLClassExpression developmentalPhenotype = df.getOWLObjectSomeValuesFrom(Entities.haspart,QINDEVELOP);
    public static final OWLClassExpression homeostatisPhenotype = df.getOWLObjectSomeValuesFrom(Entities.haspart,QINHOMEO);
    public static final OWLClassExpression pigmentationPhenotype = df.getOWLObjectSomeValuesFrom(Entities.haspart,QINPIGMENT);

    public static OWLClass cl(String iri) {
        return df.getOWLClass(IRI.create(iri));
    }
}
