#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 8 14:24:37 2018

@author: Nicolas Matentzoglu
"""

import os, sys
import yaml
import re
import urllib.request
from shutil import copyfile
import pandas as pd
from subprocess import check_call
from lib import uPhenoConfig, cdir, robot_extract_module, robot_extract_seed, robot_merge, dosdp_generate

### Configuration
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
raw_ontologies_dir = os.path.join(ws, "curation/tmp/")
upheno_prepare_dir = os.path.join(ws, "curation/upheno-release-prepare/")
ontology_for_matching_dir = os.path.join(ws,"curation/ontologies-for-matching/")

cdir(pattern_dir)
cdir(matches_dir)
cdir(upheno_fillers_dir)
cdir(raw_ontologies_dir)
cdir(upheno_prepare_dir)
cdir(ontology_for_matching_dir)


# Files
upheno_id_map = os.path.join(ws,"curation/upheno_id_map.txt")
blacklisted_upheno_ids_file = os.path.join(ws,"curation/blacklisted_upheno_iris.txt")
java_fill = os.path.join(ws,'scripts/upheno-filler-pipeline.jar')
sparql_terms = os.path.join(ws, "sparql/terms.sparql")


# generated Files
legal_iri_patterns_path = os.path.join(ws,"curation/legal_fillers.txt")
legal_pattern_vars_path = os.path.join(ws,"curation/legal_pattern_vars.txt")

with open(legal_iri_patterns_path, 'w') as f:
    for item in upheno_config.get_legal_fillers():
        f.write("%s\n" % item)

with open(legal_pattern_vars_path, 'w') as f:
    for item in upheno_config.get_instantiate_superclasses_pattern_vars():
        f.write("%s\n" % item)

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


def get_upheno_filler_data(pattern_files,tsvs_repos,blacklist):
    # Get all url of the uPheno yaml patterns from the uPheno pattern registry (probably the Github repo)

    # Get the set of urls of all tsv files indexed
    tsvs_set = get_all_tsv_urls(tsvs_repos)
    data = dict()
    # Loop through all the uPheno patterns and (1) open them
    # (2) extract fillers from patterns
    # (3) for all related tsv files, get the respectives values from the columns
    # OUT: big Yaml file with all filler data
    for pattern in pattern_files:
        x = urllib.request.urlopen(pattern).read()
        try:
            y = yaml.load(x)

            filename = os.path.basename(pattern)
            print(filename)
            data[filename] = dict()
            data[filename]['keys'] = dict()
            #ct += 1
            #if ct > 6:
                #break
            # Extract fillers from uPheno pattern file
            columns = dict()
            for v in y['vars']:
                vs = re.sub("[^0-9a-zA-Z _]", "", y['vars'][v])
                filler = y['classes'][vs]
                r = curie_to_url_filtered(filler,curie_map)
                if r == None:
                    print("WARNING: "+filler+" not on curie map!")
                columns[vs]=r

            tsvfn = re.sub("[.]yaml$", ".tsv", filename)

            # For all the tsv files that pertain to the pattern we are currently looking at
            # (1) Load it (only the relevant columns)
            # (2) Loop through columns;
            for tsv in tsvs_set:
                if tsv.endswith(tsvfn) and tsv not in blacklist:
                    print(tsv)
                    df = pd.read_csv(tsv, usecols=list(columns.keys()), sep='\t')
                    print(str((df.shape)))
                    for col,filler in columns.items():
                        if col not in data[filename]:
                            data[filename][col] = dict()
                            data[filename][col]['keys'] = []
                            data[filename][col]['filler'] = filler
                        d = curie_to_url_filtered(df[col].tolist(),curie_map)
                        data[filename][col]['keys'].extend(d)
        except yaml.YAMLError as exc:
            print(exc)

    for pattern in data:
        print(pattern)
    return data


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
    df['pattern'] = pattern
    df = df.drop_duplicates()
    df = df.reindex(sorted(df.columns), axis=1)
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


def extract_upheno_fillers(ontology_path,oid_pattern_matches_dir,oid_upheno_fillers_dir,pattern_dir):
    print("Extracting fillers from "+ontology_path)
    global TIMEOUT,robot_opts, legal_iri_patterns_path, legal_pattern_vars_path
    try:
        check_call(['timeout','-t',TIMEOUT,'java', java_opts, '-jar',java_fill, ontology_path, oid_pattern_matches_dir, pattern_dir, oid_upheno_fillers_dir, legal_iri_patterns_path, legal_pattern_vars_path])
    except Exception as e:
        print(e.output)
        raise Exception("Filler extraction of" + ontology_path + " failed")

def extract_upheno_fillers_for_all_ontologies(oids):
    global pattern_dir, matches_dir, upheno_fillers_dir
    for id in oids:
        oid_pattern_matches_dir = os.path.join(matches_dir, id)
        oid_upheno_fillers_dir = os.path.join(upheno_fillers_dir, id)
        ontology_file = os.path.join(ontology_for_matching_dir, id + ".owl")
        extract_upheno_fillers(ontology_file, oid_pattern_matches_dir, oid_upheno_fillers_dir, pattern_dir)

def add_upheno_ids_to_fillers(pattern_dir):
    for pattern in os.listdir(pattern_dir):
        if pattern.endswith(".yaml"):
            tsv_file_name = pattern.replace(".yaml",".tsv")
            for oid in upheno_config.get_phenotype_ontologies():
                tsv = os.path.join(upheno_fillers_dir,oid,tsv_file_name)
                if os.path.exists(tsv):
                    print(tsv)
                    df = pd.read_csv(tsv, sep='\t')
                    df = add_upheno_id(df, tsv.replace(".tsv$", ""))
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
    global prefix
    x = [i.replace(prefix, "").lstrip("0") for i in ids]
    x = [s for s in x if s!='']
    if len(x)==0:
        x=[0,]
    x = [int(i) for i in x]
    return max(x)


### Methods end

### Run
upheno_map = pd.read_csv(upheno_id_map, sep='\t')

print("Computing start upheno id")
startid = get_highest_id(upheno_map['id'])
if startid<minid:
    startid=minid

print(startid)



# Do not use these Upheno IDs
with open(blacklisted_upheno_ids_file) as f:
    blacklisted_upheno_ids = f.read().splitlines()

#print(blacklisted_upheno_ids)

# The following function will extract the intermediate layer as TSVs
if False:
    extract_upheno_fillers_for_all_ontologies(upheno_config.get_phenotype_ontologies())
    add_upheno_ids_to_fillers(pattern_dir)
else:
    print("uPheno filler work currently skipped (DEV)")

# Generate upheno ids for TSV files generated in the previous step




# sys.exit("Intermediadte test stop")

# Generate uPheno profiles
for upheno_combination_id in upheno_config.get_upheno_profiles():
    oids = upheno_config.get_upheno_profile_components(upheno_combination_id)
    merged_tsv_dir = os.path.join(upheno_fillers_dir, upheno_combination_id)
    cdir(merged_tsv_dir)
    final_upheno_combo_dir = os.path.join(upheno_prepare_dir, upheno_combination_id)
    cdir(final_upheno_combo_dir)
    export_merged_tsvs_for_combination(merged_tsv_dir, oids)

    upheno_pattern_ontologies = []
    # For all tsvs, generate the dosdp instances and drop them in the combo directory
    for pattern in os.listdir(pattern_dir):
        if pattern.endswith(".yaml"):
            pattern_file = os.path.join(pattern_dir,pattern)
            tsv_file_name = pattern.replace(".yaml", ".tsv")
            tsv_file = os.path.join(merged_tsv_dir,tsv_file_name)
            if os.path.exists(tsv_file):
                outfile = os.path.join(final_upheno_combo_dir,pattern.replace(".yaml", ".owl"))
                upheno_pattern_ontologies.append(outfile)
                if overwrite_dosdp_upheno or not os.path.exists(outfile):
                    dosdp_generate(pattern_file,tsv_file,outfile, TIMEOUT)


    # Collect all ontologies (taxon restricted versions) and their dependencies as needed by this profile.
    species_components = []
    for oid in oids:
        fn = oid+".owl"
        o_base_taxon = os.path.join(raw_ontologies_dir, oid+"-upheno-component.owl")
        species_components.append(o_base_taxon)

    # create merged main
    upheno_layer_ontology = os.path.join(final_upheno_combo_dir, "upheno_layer.owl")
    upheno_species_components_ontology = os.path.join(final_upheno_combo_dir,"upheno_species_components.owl")
    upheno_species_components_dependencies_ontology = os.path.join(final_upheno_combo_dir, "upheno_species_components_dependencies.owl")
    upheno_species_components_dependencies_seed = os.path.join(final_upheno_combo_dir, upheno_combination_id + "_seed.txt")
    upheno_profile_ontology = os.path.join(final_upheno_combo_dir, "upheno_"+upheno_combination_id+".owl")

    print(upheno_pattern_ontologies)
    robot_merge(upheno_pattern_ontologies, upheno_layer_ontology, TIMEOUT, robot_opts)
    robot_merge(species_components, upheno_species_components_ontology, TIMEOUT, robot_opts)
    robot_extract_seed(upheno_species_components_ontology, upheno_species_components_dependencies_seed, sparql_terms, TIMEOUT, robot_opts)
    robot_extract_module(upheno_species_components_ontology, upheno_species_components_dependencies_seed, upheno_species_components_dependencies_ontology, TIMEOUT, robot_opts)

    upheno_profile = [upheno_species_components_ontology,upheno_species_components_dependencies_ontology,upheno_layer_ontology]
    robot_merge(upheno_profile, upheno_profile_ontology, TIMEOUT, robot_opts)
    sys.exit("Stopping just after generating first round.")










# Merge them for each pipeline
# Every combination of ontologies will get its own pattern directory, where all pattern tsv filed of species tsvs are merged together.



