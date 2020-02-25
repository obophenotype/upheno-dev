#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 8 14:24:37 2018

@author: Nicolas Matentzoglu
"""

import os, sys
import yaml
import urllib.request
from shutil import copyfile
import pandas as pd
from subprocess import check_call
from lib import uPhenoConfig, cdir,write_list_to_file, robot_extract_module, remove_all_sources_of_unsatisfiability, robot_remove_axioms_that_could_cause_unsat, robot_children_list, robot_remove_terms, robot_prepare_ontology_for_dosdp, robot_extract_seed, robot_merge, dosdp_generate, robot_upheno_release, dosdp_extract_pattern_seed

### Configuration
yaml.warnings({'YAMLLoadWarning': False})
upheno_config_file = sys.argv[1]
#upheno_config_file = os.path.join("/ws/upheno-dev/src/curation/upheno-config.yaml")
upheno_config = uPhenoConfig(upheno_config_file)
os.environ['ROBOT_JAVA_ARGS'] = upheno_config.get_robot_java_args()

TIMEOUT=upheno_config.get_external_timeout()
ws = upheno_config.get_working_directory()
robot_opts=upheno_config.get_robot_opts()
maxid = upheno_config.get_max_upheno_id()
minid = upheno_config.get_min_upheno_id()
startid = minid
blacklisted_upheno_ids = []
overwrite_dosdp_upheno = upheno_config.is_overwrite_upheno_intermediate()

#globals
upheno_prefix = 'http://purl.obolibrary.org/obo/UPHENO_'


# Data directories
#upheno_filler_data_file = os.path.join(ws,"curation/upheno_fillers.yml")
#upheno_filler_ontologies_list = os.path.join(ws,"curation/ontologies.txt")
#phenotype_ontologies_list = os.path.join(ws,"curation/phenotype_ontologies.tsv")
pattern_dir = os.path.join(ws, "curation/patterns-for-matching/")
matches_dir = os.path.join(ws, "curation/pattern-matches/")
upheno_fillers_dir = os.path.join(ws, "curation/upheno-fillers/")
upheno_profiles_dir = os.path.join(ws, "curation/upheno-profiles/")
raw_ontologies_dir = os.path.join(ws, "curation/tmp/")
upheno_prepare_dir = os.path.join(ws, "curation/upheno-release-prepare/")
upheno_release_dir = os.path.join(ws, "curation/upheno-release/")
ontology_for_matching_dir = os.path.join(ws,"curation/ontologies-for-matching/")
upheno_patterns_data_manual_dir = os.path.join(ws,"patterns/data/default/")
upheno_patterns_dir = os.path.join(ws,"patterns/dosdp-patterns/")
upheno_ontology_dir = os.path.join(ws,"ontology/")

cdir(pattern_dir)
cdir(matches_dir)
cdir(upheno_fillers_dir)
cdir(raw_ontologies_dir)
cdir(upheno_prepare_dir)
cdir(ontology_for_matching_dir)


# Files
upheno_id_map = os.path.join(ws,"curation/upheno_id_map.txt")
java_fill = os.path.join(ws,'scripts/upheno-filler-pipeline.jar')
java_relationships = os.path.join(ws,'scripts/upheno-relationship-augmentation.jar')
sparql_terms = os.path.join(ws, "sparql/terms.sparql")
sparql_uberon_terms = os.path.join(ws, "sparql/uberon_terms.sparql")
phenotype_classes_sparql = os.path.join(ws, "sparql/phenotype_classes.sparql")
phenotype_pattern = os.path.join(ws,"patterns/dosdp-patterns/phenotype.yaml")
phenotype_pattern_taxon = os.path.join(ws,"patterns/dosdp-patterns/phenotype_taxon.yaml")
phenotype_pattern_taxon_modified = os.path.join(ws,"patterns/dosdp-patterns/phenotype_taxon_modified.yaml")
allimports_merged = os.path.join(raw_ontologies_dir, 'upheno-allimports-merged.owl')
allimports_dosdp = os.path.join(raw_ontologies_dir, 'upheno-allimports-dosdp.owl')
upheno_components_dir = os.path.join(upheno_ontology_dir,"components/")
upheno_core_ontology = os.path.join(upheno_prepare_dir,"upheno-core.owl")
upheno_extra_axioms_ontology = os.path.join(upheno_components_dir,"upheno-extra.owl")
upheno_relations_ontology = os.path.join(upheno_components_dir,"upheno-relations.owl")


# generated Files
legal_iri_patterns_path = os.path.join(raw_ontologies_dir,"legal_fillers.txt")
legal_pattern_vars_path = os.path.join(raw_ontologies_dir,"legal_pattern_vars.txt")
blacklisted_upheno_ids_path = os.path.join(raw_ontologies_dir,"blacklisted_upheno_iris.txt")

write_list_to_file(legal_iri_patterns_path,upheno_config.get_legal_fillers())
write_list_to_file(legal_pattern_vars_path, upheno_config.get_instantiate_superclasses_pattern_vars())
write_list_to_file(blacklisted_upheno_ids_path, upheno_config.get_blacklisted_upheno_ids())

java_opts = upheno_config.get_robot_java_args()

#class OLS:
#    def __init__(self):
#      self.base = 'https://www.ebi.ac.uk/ols/api/ontologies/'
#
#    def parents(self, ontology, entity):
#        callols = str(self.base + "%s/ancestors?id=%s" % (ontology, entity))
#        print("Call: " + callols)
#
#
#OLS().parents('go','GO:1990722')


# This restricts what namespaces are considered to be acceptable for fillers..
# curie_map = dict([("GO:", "http://purl.obolibrary.org/obo/GO_"),
#                   ("CL:", "http://purl.obolibrary.org/obo/CL_"),
#                   ("BFO:", "http://purl.obolibrary.org/obo/BFO_"),
#                   ("MPATH:", "http://purl.obolibrary.org/obo/MPATH_"),
#                   ("PATO:", "http://purl.obolibrary.org/obo/PATO_"),
#                   ("BSPO:", "http://purl.obolibrary.org/obo/BSPO_"),
#                   ("NBO:", "http://purl.obolibrary.org/obo/NBO_"),
#                   ("UBERON:", "http://purl.obolibrary.org/obo/UBERON_"),
#                   ("CHEBI:", "http://purl.obolibrary.org/obo/CHEBI_")])
#


### Configuration end

### Methods


def get_files_of_type_from_github_repo_dir(q,type):
    gh = "https://api.github.com/repos/"
    print(q)
    contents = urllib.request.urlopen(gh+q).read()
    raw = yaml.load(contents)
    tsvs = []
    for e in raw:
        tsv = e['name']
        if tsv.endswith(type):
            tsvs.append(e['download_url'])
    return tsvs


def curie_to_url_filtered(string, dictionary):
    if isinstance(string,list):
        out = []
        for item in string:
            if ':' in item and '://' not in item:
                # Its a Curie, not a URL
                for k in dictionary.keys():
                    if item.startswith(k):
                        replace = item.replace(k, dictionary[k])
                        out.append(replace)
                        break
            else:
                for k in dictionary.values():
                    if item.startswith(k):
                        out.append(item)
                        break
        return out
    if isinstance(string,str):
        if ':' in string and '://' not in string:
            for k in dictionary.keys():
                if string.startswith(k):
                    return string.replace(k, dictionary[k])
        else:
            for k in dictionary.values():
                if string.startswith(k):
                    return string
    return None


def get_all_tsv_urls(tsvs_repos):
    tsvs = []

    for repo in tsvs_repos:
        ts = get_files_of_type_from_github_repo_dir(repo,'.tsv')
        tsvs.extend(ts)

    tsvs_set = set(tsvs)
    return tsvs_set


def get_upheno_pattern_urls(upheno_pattern_repo):
    upheno_patterns = get_files_of_type_from_github_repo_dir(upheno_pattern_repo,'.yaml')
    return upheno_patterns


# def get_upheno_filler_data(pattern_files,tsvs_repos,blacklist):
#     # Get all url of the uPheno yaml patterns from the uPheno pattern registry (probably the Github repo)
#
#     # Get the set of urls of all tsv files indexed
#     tsvs_set = get_all_tsv_urls(tsvs_repos)
#     data = dict()
#     # Loop through all the uPheno patterns and (1) open them
#     # (2) extract fillers from patterns
#     # (3) for all related tsv files, get the respectives values from the columns
#     # OUT: big Yaml file with all filler data
#     for pattern in pattern_files:
#         x = urllib.request.urlopen(pattern).read()
#         try:
#             y = yaml.load(x)
#
#             filename = os.path.basename(pattern)
#             print(filename)
#             data[filename] = dict()
#             data[filename]['keys'] = dict()
#             #ct += 1
#             #if ct > 6:
#                 #break
#             # Extract fillers from uPheno pattern file
#             columns = dict()
#             for v in y['vars']:
#                 vs = re.sub("[^0-9a-zA-Z _]", "", y['vars'][v])
#                 filler = y['classes'][vs]
#                 r = curie_to_url_filtered(filler,curie_map)
#                 if r == None:
#                     print("WARNING: "+filler+" not on curie map!")
#                 columns[vs]=r
#
#             tsvfn = re.sub("[.]yaml$", ".tsv", filename)
#
#             # For all the tsv files that pertain to the pattern we are currently looking at
#             # (1) Load it (only the relevant columns)
#             # (2) Loop through columns;
#             for tsv in tsvs_set:
#                 if tsv.endswith(tsvfn) and tsv not in blacklist:
#                     print(tsv)
#                     df = pd.read_csv(tsv, usecols=list(columns.keys()), sep='\t')
#                     print(str((df.shape)))
#                     for col,filler in columns.items():
#                         if col not in data[filename]:
#                             data[filename][col] = dict()
#                             data[filename][col]['keys'] = []
#                             data[filename][col]['filler'] = filler
#                         d = curie_to_url_filtered(df[col].tolist(),curie_map)
#                         data[filename][col]['keys'].extend(d)
#         except yaml.YAMLError as exc:
#             print(exc)
#
#     for pattern in data:
#         print(pattern)
#     return data


def export_yaml(data,fn):
    with open(fn, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)

def is_blacklisted(upheno_id):
    global blacklisted_upheno_ids
    return (upheno_id in blacklisted_upheno_ids)

def generate_id(i):
    global startid, maxid, upheno_prefix
    if(isinstance(i,str)):
        if(i.startswith(upheno_prefix)):
            return i
    startid = startid + 1
    if startid>maxid:
        raise ValueError('The ID space has been exhausted (maximum 10 million). Order a new one!')
    id = upheno_prefix+str(startid).zfill(7)
    if is_blacklisted(id):
        print("BLACK:"+id)
        return generate_id(i)
    else:
        return id


def add_upheno_id(df,pattern):
    global upheno_map
    if 'defined_class' in df.columns:
        df = df.drop(['defined_class'], axis=1)
    df = df.drop_duplicates()
    df = df.reindex(sorted(df.columns), axis=1)
    df['pattern'] = pattern
    df['id'] = df.apply('-'.join, axis=1)
    df = pd.merge(df, upheno_map, on='id', how='left')
    df['defined_class'] = [generate_id(i) for i in df['defined_class']]
    upheno_map = upheno_map.append(df[['id', 'defined_class']])
    df = df.drop(['pattern', 'id'], axis=1)
    return df

def get_pattern_urls(upheno_pattern_repo):
    upheno_patterns = []
    for location in upheno_pattern_repo:
        upheno_patterns.extend(get_upheno_pattern_urls(location))
    return upheno_patterns


def download_patterns(upheno_pattern_repo, pattern_dir):
    upheno_patterns = get_pattern_urls(upheno_pattern_repo)
    filenames = []
    for url in upheno_patterns:
        a = urllib.parse.urlparse(url)
        filename = os.path.join(pattern_dir,os.path.basename(a.path))
        urllib.request.urlretrieve(url, filename)
        filenames.append(filename)
    return upheno_patterns


def extract_upheno_fillers(ontology_path,oid_pattern_matches_dir,oid_upheno_fillers_dir,pattern_dir,depth):
    print("Extracting fillers from "+ontology_path)
    global TIMEOUT,java_opts, legal_iri_patterns_path, legal_pattern_vars_path
    try:
        check_call(['timeout',TIMEOUT,'java', java_opts, '-jar',java_fill, ontology_path, oid_pattern_matches_dir, pattern_dir, oid_upheno_fillers_dir, legal_iri_patterns_path, legal_pattern_vars_path, str(depth)])
    except Exception as e:
        print(e.output)
        raise Exception("Filler extraction of" + ontology_path + " failed")
        
def augment_upheno_relationships(ontology_path,out_dir,phenotype_list):
    print("Extracting upheno relationships for "+ontology_path)
    global TIMEOUT,java_opts
    try:
        check_call(['timeout',TIMEOUT,'java', java_opts, '-jar',java_relationships, ontology_path, out_dir, phenotype_list])
    except Exception as e:
        print(e.output)
        raise Exception("Extracting upheno relationships for " + ontology_path + " failed")

def extract_upheno_fillers_for_all_ontologies(oids):
    global pattern_dir, matches_dir, upheno_fillers_dir, upheno_config
    depth = upheno_config.get_upheno_intermediate_layer_depth()
    for id in oids:
        oid_pattern_matches_dir = os.path.join(matches_dir, id)
        oid_upheno_fillers_dir = os.path.join(upheno_fillers_dir, id)
        ontology_file = os.path.join(ontology_for_matching_dir, id + ".owl")
        extract_upheno_fillers(ontology_file, oid_pattern_matches_dir, oid_upheno_fillers_dir, pattern_dir, depth)

def add_upheno_ids_to_fillers(pattern_dir):
    for pattern in os.listdir(pattern_dir):
        if pattern.endswith(".yaml"):
            tsv_file_name = pattern.replace(".yaml",".tsv")
            for oid in upheno_config.get_phenotype_ontologies():
                tsv = os.path.join(upheno_fillers_dir,oid,tsv_file_name)
                if os.path.exists(tsv):
                    print(tsv)
                    df = pd.read_csv(tsv, sep='\t')
                    tsv_name = os.path.basename(tsv)
                    df = add_upheno_id(df, tsv_name.replace(".tsv$", ""))
                    df.to_csv(tsv, sep='\t', index=False)

def replace_owl_thing_in_tsvs(pattern_dir):
    for pattern in os.listdir(pattern_dir):
        if pattern.endswith(".yaml"):
            tsv_file_name = pattern.replace(".yaml",".tsv")
            for oid in upheno_config.get_phenotype_ontologies():
                tsv = os.path.join(upheno_fillers_dir,oid,tsv_file_name)
                if os.path.exists(tsv):
                    print("Replace owl:thing in "+tsv)
                    df = pd.read_csv(tsv, sep='\t')
                    df = df.replace("http://www.w3.org/2002/07/owl#Thing","owl:Thing")
                    df.to_csv(tsv, sep='\t', index=False)

# TODO: preprocessing: Inject taxon restrictions, extract ncbi taxon module for the relevant taxon facets in the config

def export_merged_tsvs_for_combination(merged_tsv_dir, oids):
    global pattern_dir
    for pattern in os.listdir(pattern_dir):
        tsv_file_name = pattern.replace(".yaml", ".tsv")
        merged_tsv_path = os.path.join(merged_tsv_dir, tsv_file_name)

        merged = []
        for oid in oids:
            tsv_file = os.path.join(upheno_fillers_dir, oid, tsv_file_name)
            if os.path.exists(tsv_file):
                # print(tsv_file)
                otsv = pd.read_csv(tsv_file, sep='\t')
                merged.append(otsv)
        if merged:
            appended_data = pd.concat(merged, axis=0)
            appended_data.drop_duplicates().to_csv(merged_tsv_path, sep='\t', index=False)


def get_highest_id(ids):
    global upheno_prefix
    x = [i.replace(upheno_prefix, "").lstrip("0") for i in ids]
    x = [s for s in x if s!='']
    if len(x)==0:
        x=[0,]
    x = [int(i) for i in x]
    return max(x)

def get_taxon_restriction_table(ids):
    global upheno_config
    d = upheno_config.get_taxon_restriction_table(ids)
    df = pd.DataFrame.from_records(d)
    df.columns = ['defined_class','taxon','taxon_label','modifier']
    df['bearer']="owl:Thing"
    return df

def create_upheno_core_manual_phenotypes(manual_tsv_files,allimports_dosdp):
    global upheno_patterns_data_manual_dir,upheno_patterns_dir, TIMEOUT, robot_opts, upheno_prepare_dir
    ontologies = []
    for pattern_tsv in os.listdir(upheno_patterns_data_manual_dir):
        if pattern_tsv.endswith(".tsv"):
            print(pattern_tsv)
            pattern_tsv_file = os.path.join(upheno_patterns_data_manual_dir, pattern_tsv)
            manual_tsv_files.append(pattern_tsv_file)
            pattern_file_name = pattern_tsv.replace(".tsv", ".yaml")
            pattern_ontology_name = pattern_tsv.replace(".tsv", ".owl")
            upheno_pattern_file = os.path.join(upheno_patterns_dir, pattern_file_name)
            ontology_file = os.path.join(upheno_prepare_dir, pattern_ontology_name)
            if overwrite_dosdp_upheno or not os.path.exists(ontology_file):
                dosdp_generate(upheno_pattern_file,pattern_tsv_file,ontology_file,False,TIMEOUT,ONTOLOGY=allimports_dosdp)
            ontologies.append(ontology_file)
    return ontologies


### Methods end


### Run

print("Preparing a dictionary for DOSDP extraction from the all imports merged ontology.")
# Used to loop up labels in the pattern generation process, so maybe I dont need anything other than rdfs:label?
if upheno_config.is_overwrite_ontologies() or not os.path.exists(allimports_dosdp):
    robot_prepare_ontology_for_dosdp(allimports_merged,allimports_dosdp,sparql_terms,TIMEOUT=TIMEOUT,robot_opts=robot_opts)

print("Loading the existing ID map, the blacklist for uPheno IDs and determining next available uPheno ID.")
upheno_map = pd.read_csv(upheno_id_map, sep='\t')
startid = get_highest_id(upheno_map['defined_class'])
if startid<minid:
    startid=minid

print(startid)

# Do not use these Upheno IDs
with open(blacklisted_upheno_ids_path) as f:
    blacklisted_upheno_ids = f.read().splitlines()

#print(blacklisted_upheno_ids)

print("Compute the uPheno fillers for all individual ontologies, including the assignment of the ids. The actual intermediate layer is produced, by profile, at a later stage.")
extract_upheno_fillers_for_all_ontologies(upheno_config.get_phenotype_ontologies())

add_upheno_ids_to_fillers(pattern_dir)
upheno_map = upheno_map.drop_duplicates()
upheno_map.sort_values("defined_class", inplace=True)
upheno_map.to_csv(upheno_id_map, sep='\t', index=False)
#sys.exit("Intermediadte test stop")

print("Rewriting owl:Thing in DOSDP files (should be unnecessary, review https://github.com/INCATools/dosdp-tools/issues/154).")
replace_owl_thing_in_tsvs(pattern_dir)

print("Generating uPheno core (part of uPheno common to all profiles).")
# Extra axioms, upheno relations, the manually curated intermediate phenotypes part of the upheno repo
manual_tsv_files = [] #the tsv files are generally being kept track of to generate seeds for the profile import modules later
upheno_core_parts = []
upheno_core_parts.append(upheno_extra_axioms_ontology)
upheno_core_parts.append(upheno_relations_ontology)
upheno_core_manual_phenotypes = create_upheno_core_manual_phenotypes(manual_tsv_files,allimports_dosdp)
upheno_core_parts.extend(upheno_core_manual_phenotypes)
if overwrite_dosdp_upheno or not os.path.exists(upheno_core_ontology):
    robot_merge(upheno_core_parts,upheno_core_ontology, TIMEOUT, robot_opts)

print("Generating uPheno profiles..")
# Generate uPheno profiles
for upheno_combination_id in upheno_config.get_upheno_profiles():
    print("Generating profile: "+upheno_combination_id)
    oids = upheno_config.get_upheno_profile_components(upheno_combination_id)
    profile_dir = os.path.join(upheno_profiles_dir, upheno_combination_id)
    cdir(profile_dir)
    final_upheno_combo_dir = os.path.join(upheno_prepare_dir, upheno_combination_id)
    final_upheno_profile_release_dir = os.path.join(upheno_release_dir, upheno_combination_id)
    cdir(final_upheno_combo_dir)
    cdir(final_upheno_profile_release_dir)

    print("Merge all tsvs from the ontologies participating in this profiles together")
    export_merged_tsvs_for_combination(profile_dir, oids)

    print("Create all top level phenotypes relevant to this profile (SSPO top level classes)")
    upheno_top_level_phenotypes_ontology = os.path.join(final_upheno_combo_dir, "upheno_top_level_phenotypes.owl")
    upheno_top_level_phenotypes_modified_ontology = os.path.join(final_upheno_combo_dir, "upheno_top_level_phenotypes_modified.owl")
    upheno_top_level_phenotypes_non_modified_ontology = os.path.join(final_upheno_combo_dir, "upheno_top_level_phenotypes_non_modified.owl")
    phenotype_tsv = os.path.join(final_upheno_combo_dir, "upheno_top_level_phenotypes.tsv")
    phenotype_modified_tsv = os.path.join(final_upheno_combo_dir, "upheno_top_level_phenotypes_modified.tsv")
    if overwrite_dosdp_upheno or not os.path.exists(upheno_top_level_phenotypes_ontology):
        df_tr = get_taxon_restriction_table(oids)
        print(str(df_tr))
        df_tr_no_modifier = df_tr[df_tr['modifier']=="False"]
        df_tr_modifier = df_tr[df_tr['modifier']!="False"]
        df_tr_no_modifier.to_csv(phenotype_tsv, sep='\t', index=False)
        df_tr_modifier.to_csv(phenotype_modified_tsv, sep='\t', index=False)
        dosdp_generate(phenotype_pattern_taxon, phenotype_tsv, upheno_top_level_phenotypes_non_modified_ontology, RESTRICT_LOGICAL=True, TIMEOUT=TIMEOUT,ONTOLOGY=allimports_dosdp)
        dosdp_generate(phenotype_pattern_taxon_modified, phenotype_modified_tsv, upheno_top_level_phenotypes_modified_ontology, RESTRICT_LOGICAL=True, TIMEOUT=TIMEOUT,ONTOLOGY=allimports_dosdp)
        robot_merge([upheno_top_level_phenotypes_non_modified_ontology,upheno_top_level_phenotypes_modified_ontology], upheno_top_level_phenotypes_ontology, TIMEOUT, robot_opts)
    # upheno_intermediate_ontologies contains all the files that will be merged together to form the
    # intermediate (i.e. uPheno) layer of this profile, including the core, top-level and upheno-class component
    upheno_intermediate_ontologies = []
    upheno_intermediate_ontologies.append(upheno_top_level_phenotypes_ontology)
    upheno_intermediate_ontologies.append(upheno_core_ontology)

    # These TSVs are purely kept for bookkeeping and to generate the seed in the end for the profile imports module
    tsvs = []
    tsvs.append(phenotype_tsv)
    tsvs.extend(manual_tsv_files)

    # For all tsvs, generate the dosdp instances and drop them in the combo directory
    print("Profile: Generate uPheno intermediate layer")
    for pattern in os.listdir(pattern_dir):
        if pattern.endswith(".yaml"):
            pattern_file = os.path.join(pattern_dir,pattern)
            tsv_file_name = pattern.replace(".yaml", ".tsv")
            tsv_file = os.path.join(profile_dir,tsv_file_name)
            if os.path.exists(tsv_file):
                tsvs.append(tsv_file)
                outfile = os.path.join(final_upheno_combo_dir,pattern.replace(".yaml", ".owl"))
                upheno_intermediate_ontologies.append(outfile)
                if overwrite_dosdp_upheno or not os.path.exists(outfile):
                    dosdp_generate(pattern_file,tsv_file,outfile, False,TIMEOUT,ONTOLOGY=allimports_dosdp)


    print("Profile: Collect all ontologies (taxon restricted versions) and their dependencies as needed by this profile.")
    species_components = []
    for oid in oids:
        fn = oid+".owl"
        o_base_taxon = os.path.join(raw_ontologies_dir, oid+"-upheno-component.owl")
        o_base_class_hierarchy = os.path.join(raw_ontologies_dir, oid + "-class-hierarchy.owl")
        species_components.append(o_base_taxon)
        species_components.append(o_base_class_hierarchy)

    # create merged main
    upheno_layer_ontology = os.path.join(final_upheno_combo_dir, "upheno_layer.owl")
    upheno_species_components_ontology = os.path.join(final_upheno_combo_dir,"upheno_species_components.owl")
    upheno_species_components_dependencies_ontology = os.path.join(final_upheno_combo_dir, "upheno_species_components_dependencies.owl")
    upheno_species_components_dependencies_seed = os.path.join(final_upheno_combo_dir, upheno_combination_id + "_seed.txt")
    upheno_species_components_dependencies_pattern_seed = os.path.join(final_upheno_combo_dir,
                                                               upheno_combination_id + "_pattern_seed.txt")
    upheno_profile_prepare_ontology = os.path.join(final_upheno_combo_dir, "upheno_pre_" + upheno_combination_id + ".owl")
    upheno_profile_ontology = os.path.join(final_upheno_profile_release_dir, "upheno_"+upheno_combination_id+".owl")
    upheno_profile_ontology_with_relations = os.path.join(final_upheno_profile_release_dir, "upheno_"+upheno_combination_id+"_with_relations.owl")
    # print(upheno_intermediate_ontologies)
    
    print("Profile: Create upheno intermediate layer")
    if overwrite_dosdp_upheno or not os.path.exists(upheno_layer_ontology):
        robot_merge(upheno_intermediate_ontologies, upheno_layer_ontology, TIMEOUT, robot_opts)
    
    print("Profile: Prepare upheno species specific layer")
    if upheno_config.is_overwrite_ontologies() or not os.path.exists(upheno_species_components_ontology):
        robot_merge(species_components, upheno_species_components_ontology, TIMEOUT, robot_opts,ONTOLOGYIRI="http://upheno.com/upheno_species_components.owl")

    print("#####")
    print("TSVS: "+str(tsvs))
    print("#####")

    print("Profile: Prepare dependency layer (module from all merged dependencies/imports)")
    if overwrite_dosdp_upheno or not os.path.exists(upheno_species_components_dependencies_seed):
        robot_extract_seed(upheno_species_components_ontology, upheno_species_components_dependencies_seed, sparql_terms, TIMEOUT, robot_opts)
    if overwrite_dosdp_upheno or not os.path.exists(upheno_species_components_dependencies_pattern_seed):
        dosdp_extract_pattern_seed(tsvs, upheno_species_components_dependencies_pattern_seed)
    if overwrite_dosdp_upheno or not os.path.exists(upheno_species_components_dependencies_ontology):
        robot_extract_module(allimports_merged, upheno_species_components_dependencies_seed, upheno_species_components_dependencies_ontology, TIMEOUT, robot_opts)

    print("Profile: Preparing the full profile ontology (Step 1: Merging all associated OWL files)")
    upheno_profile = []
    upheno_profile.append(upheno_species_components_ontology)
    upheno_profile.append(upheno_species_components_dependencies_ontology)
    upheno_profile.append(upheno_layer_ontology)

    if overwrite_dosdp_upheno or not os.path.exists(upheno_profile_prepare_ontology):
        robot_merge(upheno_profile, upheno_profile_prepare_ontology, TIMEOUT, robot_opts)
        robot_remove_terms(ontology_path=upheno_profile_prepare_ontology,remove_list=upheno_config.get_remove_blacklist(), ontology_removed_path=upheno_profile_prepare_ontology,TIMEOUT=TIMEOUT,robot_opts=robot_opts)
        remove_all_sources_of_unsatisfiability(upheno_profile_prepare_ontology,upheno_config.get_upheno_axiom_blacklist(),TIMEOUT,robot_opts)
        # TODO: Review this step!
    
    print("Profile: Preparing the full profile ontology (Step 2: Creating the release file (reasoning, labelling etc))")
    if overwrite_dosdp_upheno or not os.path.exists(upheno_profile_ontology):
        robot_upheno_release([upheno_profile_prepare_ontology], upheno_profile_ontology,upheno_combination_id, TIMEOUT, robot_opts)
    #sys.exit("Stopping just after generating first round.")

    print("Profile: Creating uPheno addons - compute extra relations.")
    upheno_ontology_no_taxon_restictions = os.path.join(raw_ontologies_dir, "upheno_ontology_no_taxon_restictions.owl")
    upheno_phenotype_list = os.path.join(final_upheno_combo_dir, "upheno_phenotype_list.txt")
    upheno_has_phenotypic_orthologue = os.path.join(final_upheno_combo_dir, "upheno_has_phenotypic_orthologue.owl")
    upheno_has_phenotype_affecting = os.path.join(final_upheno_combo_dir, "upheno_has_phenotype_affecting.owl")
    
    if overwrite_dosdp_upheno or not os.path.exists(upheno_phenotype_list):
        robot_children_list(upheno_profile_ontology,phenotype_classes_sparql,upheno_phenotype_list)
    if overwrite_dosdp_upheno or not os.path.exists(upheno_has_phenotypic_orthologue):
        augment_upheno_relationships(upheno_ontology_no_taxon_restictions,final_upheno_combo_dir,upheno_phenotype_list)

    print("Profile: Creating uPheno addons - merge extra relations into augmented upheno release file.")
    if overwrite_dosdp_upheno or not os.path.exists(upheno_profile_ontology_with_relations):
        robot_upheno_release([upheno_profile_ontology,upheno_has_phenotypic_orthologue,upheno_has_phenotype_affecting], upheno_profile_ontology_with_relations,upheno_combination_id, TIMEOUT, robot_opts)
