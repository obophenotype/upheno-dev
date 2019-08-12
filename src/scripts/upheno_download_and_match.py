#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 8 14:24:37 2018

@author: Nicolas Matentzoglu
"""

import os, shutil, sys
import ruamel.yaml
import urllib.request
import requests
import pandas as pd
import re
from subprocess import check_call,CalledProcessError
from lib import cdir, rm, uPhenoConfig, robot_extract_seed, robot_extract_module, robot_merge, robot_dump_disjoints, robot_remove_mentions_of_nothing

### Configuration

upheno_config_file = sys.argv[1]
#upheno_config_file = os.path.join("/ws/upheno-dev/src/curation/upheno-config.yaml")
upheno_config = uPhenoConfig(upheno_config_file)
os.environ['ROBOT_JAVA_ARGS'] = upheno_config.get_robot_java_args()

TIMEOUT=str(upheno_config.get_external_timeout())
ws = upheno_config.get_working_directory()
robot_opts=upheno_config.get_robot_opts()


pattern_dir = os.path.join(ws,"curation/patterns-for-matching/")
ontology_for_matching_dir = os.path.join(ws,"curation/ontologies-for-matching/")
matches_dir = os.path.join(ws,"curation/pattern-matches/")
module_dir = os.path.join(ws,"curation/tmp/")

cdir(pattern_dir)
cdir(matches_dir)
cdir(module_dir)
cdir(ontology_for_matching_dir)

sparql_dir = os.path.join(ws,"sparql/")
xref_pattern = os.path.join(ws,"patterns/dosdp-patterns/xrefToSubClass.yaml")
sparql_terms = os.path.join(sparql_dir, "terms.sparql")

java_taxon = os.path.join(ws,'scripts/upheno-taxon-restriction.jar')


### Configuration end

### Methods
##

# This function interprets xref as subclass axioms (A xref B, A subclass B), use sparingly
def robot_xrefs(oid, mapto, mapping_file):
    global TIMEOUT, xref_pattern, robot_opts, upheno_config, module_dir
    sparql_xrefs = os.path.join(sparql_dir, "%s_xrefs.sparql" % mapto)
    print(oid)
    print(mapto)
    ontology_path = upheno_config.get_file_location(oid)
    xref_table = os.path.join(module_dir, oid + ".tsv")

    try:
        # Extracting xrefs from ontology to table
        check_call(['timeout','-t', TIMEOUT, 'robot', 'query', robot_opts, '--use-graphs', 'true', '-f', 'tsv', '--input',
                    ontology_path, '--query', sparql_xrefs, xref_table])

        # Doing a bit of preprocessing on the SPARQL result: renaming columns, removing <> signs
        try:
            df = pd.read_csv(xref_table, sep='\t')
            df = df.rename(columns={'?defined_class': 'defined_class', '?xref': 'xref'})
            df['defined_class'] = df['defined_class'].str.replace('<', '')
            df['defined_class'] = df['defined_class'].str.replace('>', '')
            df['xref'] = df['xref'].str.replace('<', '')
            df['xref'] = df['xref'].str.replace('>', '')
            df.to_csv(xref_table, sep='\t', index=False)
        except pd.io.common.EmptyDataError:
            print(xref_table, " is empty and has been skipped.")

        # DOSDP generate the xrefs as subsumptions
        check_call(['timeout','-t', TIMEOUT, 'dosdp-tools','generate','--infile='+xref_table,'--template='+xref_pattern,'--obo-prefixes=true','--restrict-axioms-to=logical','--outfile='+mapping_file])
    except Exception as e:
        print(e.output)
        raise Exception("Xref generation of" + ontology_path + " failed")

    return mapping_file

def robot_convert_merge(ontology_url, ontology_merged_path):
    print("Convert/Merging "+ontology_url+" to "+ontology_merged_path)
    global TIMEOUT, robot_opts
    try:
        check_call(['timeout','-t',TIMEOUT,'robot', 'merge',robot_opts,'-I', ontology_url,'convert', '--output', ontology_merged_path])
    except Exception as e:
        print(e)
        raise Exception("Loading " + ontology_url + " failed")

def get_files_of_type_from_github_repo_dir(q,type):
    gh = "https://api.github.com/repos/"
    print("HI")
    print(q)
    print(type)
    #contents = urllib.request.urlopen().read()
    url = gh+q
    f = requests.get(url)
    contents = f.text
    raw = ruamel.yaml.load(contents)
    tsvs = []
    for e in raw:
        tsv = e['name']
        if tsv.endswith(type):
            tsvs.append(e['download_url'])
    return tsvs

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

def export_yaml(data,fn):
    with open(fn, 'w') as outfile:
        ruamel.yaml.dump(data, outfile)

def get_pattern_urls(upheno_pattern_repos):
    upheno_patterns = []
    for upheno_pattern_repo in upheno_pattern_repos:
        upheno_patterns.extend(get_upheno_pattern_urls(upheno_pattern_repo))
    return upheno_patterns

def download_patterns(upheno_pattern_repos, pattern_dir):
    upheno_patterns = get_pattern_urls(upheno_pattern_repos)
    filenames = []
    for url in upheno_patterns:
        x = urllib.request.urlopen(url).read()
        filename = os.path.basename(url)
        file_path = os.path.join(pattern_dir, filename)
        if not upheno_config.is_skip_pattern_download():
            try:
                y = ruamel.yaml.round_trip_load(x, preserve_quotes=True)
                print(file_path)
                if upheno_config.is_match_owl_thing():
                    for v in y['vars']:
                        vsv = re.sub("[']", "", y['vars'][v])
                        y['classes'][vsv] = "owl:Thing"


                with open(file_path, 'w') as outfile:
                    ruamel.yaml.round_trip_dump(y, outfile, explicit_start=True, width=5000)

            except Exception as exc:
                print(exc)

        if os.path.isfile(file_path):
            filenames.append(filename)

    return filenames

def prepare_phenotype_ontologies_for_matching(overwrite=True):
    global upheno_config, sparql_terms, ontology_for_matching_dir, TIMEOUT, robot_opts
    for id in upheno_config.get_phenotype_ontologies():
        print("Preparing %s" %id)
        filename = upheno_config.get_file_location(id)
        imports = []
        for dependency in upheno_config.get_dependencies(id):
            print("Dependency: "+dependency)
            imports.append(upheno_config.get_file_location(dependency))
        merged = os.path.join(module_dir, id + '-allimports-merged.owl')
        module = os.path.join(module_dir, id + '-allimports-module.owl')
        merged_pheno = os.path.join(ontology_for_matching_dir, id + '.owl')
        seed = os.path.join(module_dir, id + '_seed.txt')
        term_file = os.path.join(ws, "curation/disjoints_removal.txt")
        if overwrite or not os.path.exists(module):
            robot_extract_seed(filename, seed, sparql_terms, TIMEOUT, robot_opts)
            robot_merge(imports, merged, TIMEOUT, robot_opts)
            robot_extract_module(merged, seed, module, TIMEOUT, robot_opts)
        if overwrite or not os.path.exists(merged_pheno):
            ontology_for_matching = [module, filename]
            robot_merge(ontology_for_matching, merged_pheno, TIMEOUT, robot_opts)
            robot_dump_disjoints(merged_pheno,term_file,merged_pheno,TIMEOUT,robot_opts)
            robot_remove_mentions_of_nothing(merged_pheno,merged_pheno,TIMEOUT,robot_opts)

def classes_with_matches(oid, preserve_eq):
    o_matches_dir = os.path.join(matches_dir, oid)
    classes = []
    for file in os.listdir(o_matches_dir):
        if file.endswith(".tsv"):
            tsv = os.path.join(o_matches_dir, file)
            df = pd.read_csv(tsv, sep='\t')
            classes.extend(df['defined_class'])
    with open(preserve_eq, 'w') as f:
        for item in list(set(classes)):
            f.write("%s\n" % item)

def prepare_species_specific_phenotype_ontologies(overwrite=True):
    global upheno_config, module_dir, matches_dir, TIMEOUT, robot_opts

    for oid in upheno_config.get_source_ids():
        fn = oid + ".owl"
        o_base = os.path.join(module_dir, fn)
        o_base_taxon = os.path.join(module_dir, oid + "-taxon-restricted.owl")
        preserve_eq = os.path.join(module_dir, "preserve_eq_" + fn)
        rm(preserve_eq)

        if not upheno_config.is_allow_non_upheno_eq():
            classes_with_matches(oid,preserve_eq)

        if overwrite or not os.path.exists(o_base_taxon):
            add_taxon_restrictions(o_base, o_base_taxon, upheno_config.get_taxon(oid),
                                   upheno_config.get_taxon_label(oid),
                                   upheno_config.get_root_phenotype(oid),preserve_eq)



def match_patterns(upheno_config,pattern_files,matches_dir, overwrite=True):
    for pattern_path in pattern_files:
        for id in upheno_config.get_phenotype_ontologies():
            ontology_path = os.path.join(ontology_for_matching_dir,id+".owl")
            dosdp_pattern_match(ontology_path,pattern_path,matches_dir, overwrite)

def dosdp_pattern_match(ontology_path, pattern_path, matches_dir, overwrite=True):
    print("Matching " + ontology_path + " to " + pattern_path)
    global TIMEOUT
    try:
        oid = os.path.basename(ontology_path).replace(".owl","")
        pid = os.path.basename(pattern_path).replace(".yaml", ".tsv")
        outdir = os.path.join(matches_dir,oid)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        out_tsv = os.path.join(outdir,pid)
        if overwrite or not os.path.exists(out_tsv):
            check_call(['timeout','-t', TIMEOUT, 'dosdp-tools', 'query', '--ontology='+ontology_path, '--reasoner=elk', '--obo-prefixes=true', '--template='+pattern_path,'--outfile='+out_tsv])
        else:
            print("Match already made, bypassing.")
    except CalledProcessError as e:
        print(e.output)

def add_taxon_restrictions(ontology_path,ontology_out_path,taxon_restriction,taxon_label,root_phenotype,preserve_eq):
    print("Extracting fillers from "+ontology_path)
    global TIMEOUT,upheno_config, legal_iri_patterns_path, legal_pattern_vars_path
    try:
        check_call(['timeout','-t',TIMEOUT,'java', upheno_config.get_robot_java_args(), '-jar',java_taxon, ontology_path, ontology_out_path, taxon_restriction, taxon_label, root_phenotype, preserve_eq])
    except Exception as e:
        print(e.output)
        raise Exception("Appending taxon restrictions" + ontology_path + " failed")


def list_files(directory, extension):
    return (f for f in os.listdir(directory) if f.endswith('.' + extension))

def download_sources(dir,overwrite=True):
    global upheno_config
    for oid in upheno_config.get_source_ids():
        filename = os.path.join(dir,oid+".owl")
        url = upheno_config.get_download_location(oid)
        if url not in ['xref']:
            if overwrite or not os.path.exists(filename):
                robot_convert_merge(url, filename)
            print("%s downloaded successfully." % filename)
            upheno_config.set_path_for_ontology(oid, filename)
    for oid in upheno_config.get_source_ids():
        filename = os.path.join(dir, oid + ".owl")
        url = upheno_config.get_download_location(oid)
        if url in ['xref']:
            if overwrite or not os.path.exists(filename):
                id = oid.split("-")[0]
                xref = oid.split("-")[1]
                robot_xrefs(id, xref, filename)
            print("%s compiled successfully through xrefs." % filename)
            upheno_config.set_path_for_ontology(oid, filename)


### Methods end

if upheno_config.is_clean_dir():
    print("Cleanup..")
    shutil.rmtree(matches_dir)
    os.makedirs(matches_dir)
    shutil.rmtree(ontology_for_matching_dir)
    os.makedirs(ontology_for_matching_dir)
    shutil.rmtree(module_dir)
    os.makedirs(module_dir)


pattern_files = download_patterns(upheno_config.get_pattern_repos(), pattern_dir)
pattern_files = [os.path.join(pattern_dir,f) for f in os.listdir(pattern_dir) if os.path.isfile(os.path.join(pattern_dir, f)) and f.endswith('.yaml')]

print("ROBOT args: "+os.environ['ROBOT_JAVA_ARGS'])
download_sources(module_dir,upheno_config.is_overwrite_ontologies())

prepare_phenotype_ontologies_for_matching(upheno_config.is_overwrite_ontologies())

match_patterns(upheno_config,pattern_files, matches_dir, upheno_config.is_overwrite_matches())

prepare_species_specific_phenotype_ontologies(upheno_config.is_overwrite_ontologies())

