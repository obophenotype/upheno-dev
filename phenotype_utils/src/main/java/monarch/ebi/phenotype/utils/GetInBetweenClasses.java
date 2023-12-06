package monarch.ebi.phenotype.utils;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.InputStream;
import java.io.IOException;
import java.util.*;
import java.util.stream.Collectors;

import com.google.common.collect.Lists;
import org.apache.commons.io.FileUtils;
import org.semanticweb.elk.owlapi.ElkReasonerFactory;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.reasoner.OWLReasoner;
import org.yaml.snakeyaml.Yaml;

/**
 * Hello world!
 */
public class GetInBetweenClasses {
    private static String OBOPURLSTRING = "http://purl.obolibrary.org/obo/";
    private final List<String> legal_filler_patterns = new ArrayList<>();
    private final Set<String> legal_patterns_vars_set = new HashSet<>();
    private final File ontology_file;
    private final File oid_pattern_matches_dir;
    private final File pattern_dir;
    private final File oid_upheno_fillers_dir;
    private final File legal_filler_iri_patterns;
    private final File legal_pattern_vars;
    private static OWLDataFactory df = OWLManager.getOWLDataFactory();
    private final int SUPER_CLASS_DEPTH;

    public GetInBetweenClasses(File ontology_file, File oid_pattern_matches_dir, File pattern_dir, File oid_upheno_fillers_dir, File legal_filler_iri_patterns, File legal_pattern_vars, int SUPER_CLASS_DEPTH) throws IOException, OWLOntologyCreationException {
        this.ontology_file = ontology_file;
        this.oid_pattern_matches_dir = oid_pattern_matches_dir;
        this.pattern_dir = pattern_dir;
        this.oid_upheno_fillers_dir = oid_upheno_fillers_dir;
        this.legal_filler_iri_patterns = legal_filler_iri_patterns;
        this.legal_pattern_vars = legal_pattern_vars;
        this.SUPER_CLASS_DEPTH = SUPER_CLASS_DEPTH;
        run();
    }

    private void run() throws IOException, OWLOntologyCreationException {
        legal_filler_patterns.addAll(FileUtils.readLines(this.legal_filler_iri_patterns,"utf-8"));
        legal_patterns_vars_set.addAll(FileUtils.readLines(this.legal_pattern_vars,"utf-8"));
        OWLOntology o = OWLManager.createOWLOntologyManager().loadOntology(IRI.create(ontology_file));
        OWLReasoner r = new ElkReasonerFactory().createReasoner(o);
        for (File tsv_file : oid_pattern_matches_dir.listFiles((dir, name) -> name.toLowerCase().endsWith(".tsv"))) {
            //if(tsv_file.getName().contains("abnormalAbsenceOfBehavi"))
                extract_fillers_for_tsv(r, tsv_file);
        }

    }

    private void extract_fillers_for_tsv(OWLReasoner r, File tsv_file) throws IOException {
        File pattern = new File(pattern_dir, tsv_file.getName().replaceAll(".tsv$", ".yaml"));
        List<Map<String, String>> tsv = loadTsv(tsv_file);
        if(!tsv.isEmpty()) {

            log("Processing TSV: "+tsv_file+" , size: "+tsv.size());

            Map<String, Object> obj = loadPattern(pattern);
            Map<String, OWLClass> filler = getFillerClassesFromPattern(obj);
            List<String> filler_columns = new ArrayList<>(filler.keySet());

            //if(tsv.size()>2&&tsv.size()<8&&filler.keySet().size()>1) {
                //log("TSV:");
                //log(tsv);
                //log("Filler classes:");
                //log(filler);
                //log("Filler: "+filler.toString());

                //log("Filler columns: "+filler_columns.toString());
                Set<Map<String, String>> upheno_fillers = computeAllFillerCombinations(r, tsv, filler, filler_columns);
                //log("transformed combinations:");
                //log(upheno_fillers);
                //System.exit(0);
                log("Cartesian product size: " + upheno_fillers.size());
                exportTSVs(upheno_fillers, filler_columns, tsv_file.getName());
            //}
        }
    }

    private Set<List<OWLClass>> computeCartesianProduct(List<List<OWLClass>> fillers) {
        Set<List<OWLClass>> cp = new HashSet<>();
        if(fillers.size()==1) {
            //log("Only one feature, no cartesian product necessary.");
            for(List<OWLClass> column:fillers) {
                for(OWLClass cl:column) {
                    cp.add(Collections.singletonList(cl));
                }
            }
        }
        else {
            //log("More than one feature, computing cartesian product.");
            //log(filler_map);
            //filler_map.forEach(l->log(l.size()));
            cp.addAll(Lists.cartesianProduct(fillers).stream().distinct().collect(Collectors.toList()));
        }
        return cp;
    }

    private Set<Map<String, String>> computeAllFillerCombinations(OWLReasoner r, List<Map<String, String>> tsv, Map<String, OWLClass> filler, List<String> filler_columns) {
        Set<Map<String, String>> upheno_fillers = new HashSet<>();
        //log("Computing all filler combinations..");
        for (Map<String, String> rec : tsv) {
            //log("Record: "+rec);
            // The filler_combinations will contain one list of owlclasses for each feature (anatomical_entity, biological_process, etc)
            List<List<OWLClass>> filler_combinations = new ArrayList<>();
            boolean at_least_one_column_no_fillers = false;
            for (String filler_col : filler_columns) {
                OWLClass cl = cl(rec.get(filler_col));
                //log(cl);
                // Computing all inferences between the filler class declared in the pattern and the class in the record. Filtering out those fillers that are not declared legal, species independent fillers in the legal_filler.txt file. If the current column is configured to be expanded to superclasses, it is done, else only the entity itself is taken over.
                List<OWLClass> classes_in_between = between(cl, filler.get(filler_col), r, legal_patterns_vars_set.contains(filler_col));
                if(classes_in_between.isEmpty()) {
                    //log("No fillers found for class: "+cl);
                    at_least_one_column_no_fillers = true;
                    break;
                } else {
                    filler_combinations.add(classes_in_between);
                }

            }
            //log("Filler combinations:");
            //filler_combinations.forEach(this::log);
            if(at_least_one_column_no_fillers) {
                log("At least one column has no fillers for rec: "+rec);
            } else {
                Set<List<OWLClass>> cp = computeCartesianProduct(filler_combinations);
                //log("CartesianXYZ:");
                //System.exit(0);
                for(List<OWLClass> row:cp) {
                    //log(cp);
                    Map<String,String> nrec = new HashMap<>();
                    for (int i = 0; i < filler_columns.size(); i++) {
                        try {
                            nrec.put(filler_columns.get(i), row.get(i).getIRI().toString());
                        } catch (Exception e) {
                            e.printStackTrace();
                            log(row);
                            log(filler_columns);
                            System.exit(0);
                        }
                    }
                    //log(nrec);
                    upheno_fillers.add(nrec);
                }
            }
        }
        return upheno_fillers;
    }

    private boolean legalFiller(OWLClass owlClass) {
        for(String iripattern:this.legal_filler_patterns) {
            if(owlClass.getIRI().toString().startsWith(iripattern)) {
                return true;
            }
        }
        return false;
    }

    private Map<String,OWLClass> getFillerClassesFromPattern(Map<String, Object> obj) {
        Map<String,OWLClass> fillers = new HashMap<>();
        Map<String,Object> classes = (Map<String, Object>) obj.get("classes");
        Map<String,Object> vars = (Map<String, Object>) obj.get("vars");
        for(String var:vars.keySet()) {
            //log(var);
            //log(vars.get(var));
            String cl = classes.get(vars.get(var).toString().replaceAll("'","")).toString().trim();
            if(cl.equals("owl:Thing")) {
                fillers.put(var, df.getOWLThing());
            } else {
                String iri = OBOPURLSTRING + cl.replaceAll(":", "_");
                fillers.put(var, cl(iri));
            }
        }
        return fillers;
    }

    private void log(Object o) {
        System.out.println(o.toString());
    }

    private List<OWLClass> between(OWLClass e, OWLClass filler, OWLReasoner r, boolean legal_pattern_var) {
        //log(e);
        //log(filler);
        Set<OWLClass> between = new HashSet<>();

        if(r.getUnsatisfiableClasses().contains(e)) {
            log(e+" is unsatisfiable, ignoring");
            return new ArrayList<>(between);
        }

        Set<OWLClass> superClasses = new HashSet<>();
        if(legal_pattern_var) {
            superClasses.addAll(getSuperclasses(e,r,SUPER_CLASS_DEPTH));
            superClasses.add(e);
        } else {
            superClasses.add(e);
        }
        if(superClasses.size()>1000) {
            log("Number of superclasses >1000");
            log(e);
            log(superClasses.size());
            //log(superClasses);

        }
        if(!r.getSuperClasses(e, false).getFlattened().contains(filler)) {
            log(e +" is not a legal instance of the filler! This should not happen.");
            return new ArrayList<>(between);
        }
        for(OWLClass s:superClasses) {
            if(legalFiller(s)) {
                between.add(s);
            }
        }
        between.removeAll(r.getSuperClasses(filler, false).getFlattened());
        between.add(filler);
        return new ArrayList<>(between);
    }

    private Collection<? extends OWLClass> getSuperclasses(OWLClass e, OWLReasoner r, int i) {
        Set<OWLClass> superc = new HashSet<>();
        if(i>0) {
            for(OWLClass s:r.getSuperClasses(e, true).getFlattened()) {
                superc.add(s);
                getSuperclasses(s, r, (i-1));
            }
        }
        return superc;
    }

    public OWLClass cl(String iri) {
        return df.getOWLClass(IRI.create(iri));
    }

    public static void main(String[] args) throws OWLOntologyCreationException, IOException {

		String ontology_path = args[0];
		String oid_pattern_matches_dir_path = args[1];
		String pattern_dir_path = args[2];
        String oid_upheno_fillers_dir_path = args[3];
        String legal_filler_iri_patterns_path = args[4];
        String legal_pattern_vars_path = args[5];
        int SUPER_CLASS_DEPTH = Integer.valueOf(args[6]);
   /*
        String ontology_path = "/Users/matentzn/ws/upheno-dev/src/curation/ontologies-for-matching/mp.owl";
        String oid_pattern_matches_dir_path = "/Users/matentzn/ws/upheno-dev/src/curation/pattern-matches/mp";
        String pattern_dir_path = "/Users/matentzn/ws/upheno-dev/src/curation/patterns-for-matching/";
        String oid_upheno_fillers_dir_path = "/Users/matentzn/ws/upheno-dev/src/curation/upheno-fillers/mp";
        String legal_filler_iri_patterns_path = "/Users/matentzn/ws/upheno-dev/src/curation/tmp/legal_fillers.txt";
        String legal_pattern_vars_path = "/Users/matentzn/ws/upheno-dev/src/curation/tmp/legal_pattern_vars.txt";
        int SUPER_CLASS_DEPTH = 1;
*/
        File ontology_file = new File(ontology_path);
        File oid_pattern_matches_dir = new File(oid_pattern_matches_dir_path);
        File pattern_dir = new File(pattern_dir_path);
        File oid_upheno_fillers_dir = new File(oid_upheno_fillers_dir_path);
        File legal_filler_iri_patterns = new File(legal_filler_iri_patterns_path);
        File legal_pattern_vars = new File(legal_pattern_vars_path);

        new GetInBetweenClasses(ontology_file, oid_pattern_matches_dir, pattern_dir, oid_upheno_fillers_dir, legal_filler_iri_patterns, legal_pattern_vars,SUPER_CLASS_DEPTH);
    }

    private Map<String, Object> loadPattern(File pattern) throws FileNotFoundException {
        Yaml yaml = new Yaml();
        InputStream inputStream = new FileInputStream(pattern);
        Map<String, Object> obj = yaml.load(inputStream);
        return obj;
    }

    private List<Map<String, String>> loadTsv(File tsv_file) throws IOException {
        List<Map<String, String>> tsv = new ArrayList<>();
        log("Load TSV: "+tsv_file);
        List<String> lines = FileUtils.readLines(tsv_file, "utf-8");
        boolean first = true;
        String[] header = null;
        for (String l : lines) {
            Map<String, String> rec = new HashMap<>();
            String[] row = l.split("\\t");
            if (first) {
                header = row;
                first = false;
            } else {
                for (int i = 0; i < header.length; i++) {
                    String val = "";
                    if(row.length>i) {
                        val = row[i];
                    } else {
                        log("Warning, row has less columns than header.. ");
                    }
                    rec.put(header[i], val);
                }
                tsv.add(rec);
            }

        }
        return tsv;
    }


    private void exportTSVs(Collection<Map<String,String>> fillers, List<String> columns, String tsvname) {
        List<String> outlines = new ArrayList<>();
        File tsvf = new File(oid_upheno_fillers_dir,tsvname);
        outlines.add(String.join("\t", columns));
        for (Map<String,String> rec : fillers) {
            String s = "";
            for(String col:columns) {
                s+= rec.get(col)+"\t";
            }
            outlines.add(s.trim());
        }

        try {
            log("Exporting to file: "+tsvf);
            FileUtils.writeLines(tsvf, outlines);
        } catch (IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }

}
