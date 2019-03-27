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

#globals
upheno_prefix = 'http://purl.obolibrary.org/obo/UPHENO_'

# Data directories
#upheno_filler_data_file = os.path.join(ws,"curation/upheno_fillers.yml")
#upheno_filler_ontologies_list = os.path.join(ws,"curation/ontologies.txt")
#phenotype_ontologies_list = os.path.join(ws,"curation/phenotype_ontologies.tsv")
pattern_dir = os.path.join(ws, "curation/patterns-for-matching/")
matches_dir = os.path.join(ws, "curation/pattern-matches-test/")
upheno_fillers_dir = os.path.join(ws, "curation/upheno-fillers/")
raw_ontologies_dir = os.path.join(ws, "curation/tmp/")
upheno_prepare_dir = os.path.join(ws, "curation/upheno-release-prepare/")
ontology_for_matching_dir = os.path.join(ws,"curation/ontologies-for-matching/")

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


def upheno_id(i):
    global last_upheno_index
    if(isinstance(i,str)):
        return i
    else:
        last_upheno_index = last_upheno_index + 1
        id = upheno_prefix+str(last_upheno_index).zfill(7)
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
    df['defined_class'] = [upheno_id(i) for i in df['defined_class']]
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
        check_call(['gtimeout',TIMEOUT,'java', java_opts, '-jar',java_fill, ontology_path, oid_pattern_matches_dir, pattern_dir, oid_upheno_fillers_dir, legal_iri_patterns_path, legal_pattern_vars_path])
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
        tsv_file_name = pattern.replace(".yaml",".tsv")
        for oid in upheno_config.get_phenotype_ontologies():
            tsv = os.path.join(upheno_fillers_dir,oid,tsv_file_name)
            if os.path.exists(tsv):
                df = pd.read_csv(f, sep='\t')
                df = add_upheno_id(df, tsv.replace(".tsv$", ""))
                df.to_csv(f, sep='\t', index=False)
### Methods end

### Run
upheno_map = pd.read_csv(upheno_id_map, sep='\t')

# Do not use these Upheno IDs
with open(blacklisted_upheno_ids_file) as f:
    blacklisted_upheno_ids = f.read().splitlines()

extract_upheno_fillers_for_all_ontologies(upheno_config.get_phenotype_ontologies())

sys.exit("Error message")
# Assign upheno ids
add_upheno_ids_to_fillers(upheno_config.get_phenotype_ontologies(),pattern_dir)

sys.exit("Intermediadte test stop")

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


for upheno_combination_id in upheno_config.get_upheno_combos():
    oids = upheno_config.get_upheno_combo_oids(upheno_combination_id)
    merged_tsv_dir = os.path.join(upheno_fillers_dir, upheno_combination_id)
    cdir(merged_tsv_dir)
    final_upheno_combo_dir = os.path.join(upheno_prepare_dir, upheno_combination_id)
    cdir(final_upheno_combo_dir)
    export_merged_tsvs_for_combination(merged_tsv_dir, oids)

    # For all tsvs, generate the dosdp instances and drop them in the combo directory
    for pattern in os.listdir(pattern_dir):
        tsv_file_name = pattern.replace(".yaml", ".tsv")
        outfile = os.path.join(final_upheno_combo_dir,pattern.replace(".yaml", ".owl"))
        dosdp_generate(pattern,tsv_file_name,outfile, TIMEOUT)

    # For all participating ontologies
    dependencies = []
    main_files = []
    for oid in oids:
        fn = oid+".owl"
        o_base = os.path.join(raw_ontologies_dir,fn)
        main_files.append(o_base)
        for dependency in upheno_config.get_dependencies(oid):
            fn_dep = dependency+".owl"
            o_dep = os.path.join(raw_ontologies_dir, fn_dep)
            dependencies.append(o_dep)

    # create merged main
    merged_main = os.path.join(final_upheno_combo_dir,"upheno_main.owl")
    robot_merge(main_files, merged_main, TIMEOUT, robot_opts)
    seed = os.path.join(merged_main, upheno_combination_id + "_seed.txt")

    dependencies = list(set(dependencies))
    for dependency in dependencies:
        fn_dep = dependency + ".owl"
        o_dep = os.path.join(raw_ontologies_dir, fn_dep)
        module = os.path.join(final_upheno_combo_dir, upheno_combination_id + "_"+dependency+"_module.owl")
        robot_extract_seed(merged_main, seed, sparql_terms, TIMEOUT, robot_opts)
        robot_extract_module(merged_main, seed, module, TIMEOUT, robot_opts)











# Merge them for each pipeline
# Every combination of ontologies will get its own pattern directory, where all pattern tsv filed of species tsvs are merged together.



