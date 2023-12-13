#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 8 14:24:37 2018

@author: Nicolas Matentzoglu
"""

import os
import re
import shutil
import sys
import urllib.request
import warnings
from subprocess import CalledProcessError, check_call

import pandas as pd
import requests
import ruamel.yaml
from lib import (
    cdir,
    dosdp_pattern_match,
    remove_all_sources_of_unsatisfiability,
    rm,
    robot_class_hierarchy,
    robot_dump_disjoints,
    robot_extract_module,
    robot_extract_seed,
    robot_merge,
    robot_query,
    robot_remove_axioms_that_could_cause_unsat,
    robot_remove_mentions_of_nothing,
    robot_remove_upheno_blacklist_and_classify,
    robot_upheno_component,
    touch,
    uPhenoConfig,
    write_list_to_file,
)

### Configuration
warnings.simplefilter("ignore", ruamel.yaml.error.UnsafeLoaderWarning)

upheno_config_file = sys.argv[1]
# upheno_config_file = os.path.join("/ws/upheno-dev/src/curation/upheno-config.yaml")
upheno_config = uPhenoConfig(upheno_config_file)
os.environ["ROBOT_JAVA_ARGS"] = upheno_config.get_robot_java_args()
os.environ["JAVA_OPTS"] = upheno_config.get_java_opts()

TIMEOUT = str(upheno_config.get_external_timeout())
ws = upheno_config.get_working_directory()
robot_opts = upheno_config.get_robot_opts()


pattern_dir = os.path.join(ws, "curation/patterns-for-matching/")
ontology_for_matching_dir = os.path.join(ws, "curation/ontologies-for-matching/")
matches_dir = os.path.join(ws, "curation/pattern-matches/")
stats_dir = os.path.join(ws, "curation/upheno-stats/")
module_dir = os.path.join(ws, "curation/tmp/")

cdir(pattern_dir)
cdir(matches_dir)
cdir(module_dir)
cdir(ontology_for_matching_dir)
cdir(stats_dir)

sparql_dir = os.path.join(ws, "sparql/")
xref_pattern = os.path.join(ws, "patterns/dosdp-patterns/xrefToSubClass.yaml")
sparql_terms = os.path.join(sparql_dir, "terms.sparql")

java_taxon = os.path.join(ws, "scripts/upheno-taxon-restriction.jar")


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
        check_call(
            [
                "timeout",
                TIMEOUT,
                "robot",
                "query",
                robot_opts,
                "--use-graphs",
                "true",
                "-f",
                "tsv",
                "--input",
                ontology_path,
                "--query",
                sparql_xrefs,
                xref_table,
            ]
        )

        # Doing a bit of preprocessing on the SPARQL result: renaming columns, removing <> signs
        try:
            df = pd.read_csv(xref_table, sep="\t")
            df = df.rename(columns={"?defined_class": "defined_class", "?xref": "xref"})
            df["defined_class"] = df["defined_class"].str.replace("<", "")
            df["defined_class"] = df["defined_class"].str.replace(">", "")
            df["xref"] = df["xref"].str.replace("<", "")
            df["xref"] = df["xref"].str.replace(">", "")
            df.to_csv(xref_table, sep="\t", index=False)
        except pd.io.common.EmptyDataError:
            print(xref_table, " is empty and has been skipped.")

        # DOSDP generate the xrefs as subsumptions
        check_call(
            [
                "timeout",
                TIMEOUT,
                "dosdp-tools",
                "generate",
                "--infile=" + xref_table,
                "--template=" + xref_pattern,
                "--obo-prefixes=true",
                "--restrict-axioms-to=logical",
                "--outfile=" + mapping_file,
            ]
        )
    except Exception as e:
        print(e.output)
        raise Exception("Xref generation of" + ontology_path + " failed")

    return mapping_file


def robot_convert_merge(ontology_url, ontology_merged_path):
    print("Convert/Merging " + ontology_url + " to " + ontology_merged_path)
    global TIMEOUT, robot_opts
    try:
        check_call(
            [
                "timeout",
                TIMEOUT,
                "robot",
                "merge",
                robot_opts,
                "-I",
                ontology_url,
                "convert",
                "--output",
                ontology_merged_path,
            ]
        )
    except Exception as e:
        print(e)
        raise Exception("Loading " + ontology_url + " failed")


def get_files_of_type_from_github_repo_dir(q, type):
    gh = "https://api.github.com/repos/"
    print(q)
    print(type)
    # contents = urllib.request.urlopen().read()
    url = gh + q
    f = requests.get(url)
    contents = f.text
    raw = ruamel.yaml.load(contents)
    tsvs = []
    for e in raw:
        tsv = e["name"]
        if tsv.endswith(type):
            tsvs.append(e["download_url"])
    return tsvs


def get_all_tsv_urls(tsvs_repos):
    tsvs = []

    for repo in tsvs_repos:
        ts = get_files_of_type_from_github_repo_dir(repo, ".tsv")
        tsvs.extend(ts)

    tsvs_set = set(tsvs)
    return tsvs_set


def get_upheno_pattern_urls(upheno_pattern_repo):
    upheno_patterns = get_files_of_type_from_github_repo_dir(upheno_pattern_repo, ".yaml")
    return upheno_patterns


def export_yaml(data, fn):
    with open(fn, "w") as outfile:
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
        print("Downloading " + url)
        filename = os.path.basename(url)
        file_path = os.path.join(pattern_dir, filename)
        if not upheno_config.is_skip_pattern_download():
            try:
                x = urllib.request.urlopen(url).read()
                y = ruamel.yaml.round_trip_load(x, preserve_quotes=True)
                print(file_path)
                if upheno_config.is_match_owl_thing():
                    for v in y["vars"]:
                        vsv = re.sub("[']", "", y["vars"][v])
                        y["classes"][vsv] = "owl:Thing"

                with open(file_path, "w") as outfile:
                    ruamel.yaml.round_trip_dump(y, outfile, explicit_start=True, width=5000)

            except Exception as exc:
                print(exc)

        if os.path.isfile(file_path):
            filenames.append(filename)
    return filenames


def prepare_all_imports_merged(config):
    imports = []
    merged = os.path.join(module_dir, "upheno-allimports-merged.owl")

    for id in config.get_phenotype_ontologies():
        for dependency in config.get_dependencies(id):
            imports.append(config.get_file_location(dependency))

    imports = list(set(imports))

    if config.is_overwrite_ontologies() or not os.path.exists(merged):
        robot_merge(imports, merged, TIMEOUT, robot_opts)
        remove_all_sources_of_unsatisfiability(
            merged, config.get_upheno_axiom_blacklist(), TIMEOUT, robot_opts
        )


def prepare_upheno_ontology_no_taxon_restictions(config):
    global ontology_for_matching_dir
    imports = []
    upheno_ontology_no_taxon_restictions = os.path.join(
        module_dir, "upheno_ontology_no_taxon_restictions.owl"
    )

    for id in upheno_config.get_phenotype_ontologies():
        imports.append(os.path.join(ontology_for_matching_dir, id + ".owl"))

    imports = list(set(imports))

    if config.is_overwrite_ontologies() or not os.path.exists(upheno_ontology_no_taxon_restictions):
        robot_merge(imports, upheno_ontology_no_taxon_restictions, TIMEOUT, robot_opts)
        remove_all_sources_of_unsatisfiability(
            upheno_ontology_no_taxon_restictions,
            config.get_upheno_axiom_blacklist(),
            TIMEOUT,
            robot_opts,
        )


def write_phenotype_sparql(phenotype_root, phenotype_query):
    sparql = []
    sparql.append("prefix owl: <http://www.w3.org/2002/07/owl#>")
    sparql.append("prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>")
    sparql.append("prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>")
    sparql.append("")
    sparql.append("SELECT ?s ?lab ?ldef WHERE ")
    sparql.append("{")
    sparql.append("?s rdfs:subClassOf* <{}> . ".format(phenotype_root))
    sparql.append("OPTIONAL { ?s rdfs:label ?lab }")
    sparql.append("OPTIONAL { ?s owl:equivalentClass [ rdf:type owl:Restriction ;")
    sparql.append("owl:onProperty <http://purl.obolibrary.org/obo/BFO_0000051> ;")
    sparql.append("owl:someValuesFrom ?ldef ] . }")
    sparql.append("}")
    outF = open(phenotype_query, "w")
    for line in sparql:
        outF.write(line + "\n")
    outF.close()


def prepare_phenotype_ontologies_for_matching(overwrite=True):
    global upheno_config, sparql_terms, ontology_for_matching_dir, TIMEOUT, robot_opts
    for id in upheno_config.get_phenotype_ontologies():
        print("Preparing %s" % id)
        filename = upheno_config.get_file_location(id)
        imports = []
        for dependency in upheno_config.get_dependencies(id):
            print("Dependency: " + dependency)
            imports.append(upheno_config.get_file_location(dependency))
        merged = os.path.join(module_dir, id + "-allimports-merged.owl")
        module = os.path.join(module_dir, id + "-allimports-module.owl")
        o_base_class_hierarchy = os.path.join(module_dir, id + "-class-hierarchy.owl")
        class_hierarchy_seed = os.path.join(module_dir, id + "-class-hierarchy.txt")
        phenotype_class_metadata = os.path.join(stats_dir, id + "_phenotype_data.csv")
        merged_pheno = os.path.join(ontology_for_matching_dir, id + ".owl")
        seed = os.path.join(module_dir, id + "_seed.txt")
        disjoints_term_file = os.path.join(module_dir, "disjoints_removal.txt")
        write_list_to_file(disjoints_term_file, upheno_config.get_remove_disjoints())
        phenotype_query = os.path.join(sparql_dir, id + "_phenotypes.sparql")
        write_phenotype_sparql(upheno_config.get_root_phenotype(id), phenotype_query)
        if overwrite or not os.path.exists(module):
            robot_extract_seed(filename, seed, sparql_terms, TIMEOUT, robot_opts)
            robot_merge(imports, merged, TIMEOUT, robot_opts)
            robot_extract_module(merged, seed, module, TIMEOUT, robot_opts)
        if overwrite or not os.path.exists(merged_pheno):
            ontology_for_matching = [module, filename]
            robot_merge(ontology_for_matching, merged_pheno, TIMEOUT, robot_opts)
            remove_all_sources_of_unsatisfiability(
                merged_pheno, upheno_config.get_upheno_axiom_blacklist(), TIMEOUT, robot_opts
            )
        if overwrite or not os.path.exists(o_base_class_hierarchy):
            sparql_terms_class_hierarchy = os.path.join(sparql_dir, id + "_terms.sparql")
            robot_extract_seed(
                filename, class_hierarchy_seed, sparql_terms_class_hierarchy, TIMEOUT, robot_opts
            )
            robot_class_hierarchy(
                merged_pheno,
                class_hierarchy_seed,
                o_base_class_hierarchy,
                upheno_config.is_inferred_class_hierarchy(id),
            )
        if overwrite or not os.path.exists(phenotype_class_metadata):
            robot_query(
                merged_pheno, phenotype_class_metadata, phenotype_query, TIMEOUT, robot_opts
            )


def classes_with_matches(oid, preserve_eq):
    global matches_dir
    o_matches_dir = os.path.join(matches_dir, oid)
    classes = []
    for file in os.listdir(o_matches_dir):
        if file.endswith(".tsv"):
            tsv = os.path.join(o_matches_dir, file)
            df = pd.read_csv(tsv, sep="\t")
            classes.extend(df["defined_class"])
    write_list_to_file(preserve_eq, list(set(classes)))


def prepare_species_specific_phenotype_ontologies(config):
    global upheno_config, module_dir, matches_dir, TIMEOUT, robot_opts

    for oid in upheno_config.get_phenotype_ontologies():
        fn = oid + ".owl"
        o_base = os.path.join(module_dir, fn)
        o_base_taxon = os.path.join(module_dir, oid + "-upheno-component.owl")
        preserve_eq = os.path.join(module_dir, "preserve_eq_" + fn)
        if os.path.exists(preserve_eq):
            rm(preserve_eq)

        if not upheno_config.is_allow_non_upheno_eq():
            classes_with_matches(oid, preserve_eq)
        else:
            touch(preserve_eq)

        if config.is_overwrite_ontologies() or not os.path.exists(o_base_taxon):
            add_taxon_restrictions(
                o_base,
                o_base_taxon,
                upheno_config.get_taxon(oid),
                upheno_config.get_taxon_label(oid),
                upheno_config.get_prefix_iri(oid),
                preserve_eq,
            )
            remove_eqs_file = os.path.join(module_dir, oid + "-upheno-component_eq_remove.txt")
            remove_eqs = [upheno_config.get_root_phenotype(oid)]
            write_list_to_file(remove_eqs_file, remove_eqs)
            remove_all_sources_of_unsatisfiability(
                o_base_taxon, config.get_upheno_axiom_blacklist(), TIMEOUT, robot_opts
            )
            robot_upheno_component(o_base_taxon, remove_eqs_file)

def postprocess_modified_patterns(upheno_config, pattern_files, matches_dir):
    patterns = []
    delete_files = []
    delete_files.extend(pattern_files)
    
    for pattern_path in pattern_files:
        pid = os.path.basename(pattern_path).replace(".yaml", "")
        patterns.append(pid)
    
    for id in upheno_config.get_phenotype_ontologies():
        oid_matches_path = os.path.join(matches_dir, id)
        for pattern in patterns:
            # Load both the modified and unm modified tsv files
            # merge them and write them back to the unmodified file
            unmodified_tsv_path = os.path.join(oid_matches_path, pattern + ".tsv")
            modified_tsv_path = os.path.join(oid_matches_path, pattern + "-modification.tsv")
            if not os.path.exists(modified_tsv_path):
                continue
            if not os.path.exists(unmodified_tsv_path):
                continue
            df_unmodified = pd.read_csv(unmodified_tsv_path, sep="\t")
            df_modified = pd.read_csv(modified_tsv_path, sep="\t")
            df_combined = pd.concat([df_unmodified, df_modified])
            # Remove duplicate rows
            df_final = df_combined.drop_duplicates()
            df_final.to_csv(unmodified_tsv_path, sep="\t", index=False)
            delete_files.append(modified_tsv_path)
    
    # Delete the modified tsv files and their corresponding patterns:
    for file_path in delete_files:
        if os.path.exists(file_path):
            os.remove(file_path)


            
        

def match_patterns(upheno_config, pattern_files, matches_dir, pattern_dir, overwrite=True):
    patterns = []
    for pattern_path in pattern_files:
        pid = os.path.basename(pattern_path).replace(".yaml", "")
        patterns.append(pid)
    # pattern_string = " ".join(patterns)
    # pattern_string = pattern_string.strip()
    # Splitting the string in two to avoid Memory Overflow
    length = len(patterns)
    middle_index = length // 2
    first_half = patterns[:middle_index]
    second_half = patterns[middle_index:]
    pattern_string1 = " ".join(first_half)
    pattern_string2 = " ".join(second_half)

    for id in upheno_config.get_phenotype_ontologies():
        ontology_path = os.path.join(ontology_for_matching_dir, id + ".owl")
        oid = os.path.basename(ontology_path).replace(".owl", "")
        outdir = os.path.join(matches_dir, oid)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        if overwrite or not os.path.exists(outdir):
            dosdp_pattern_match(ontology_path, pattern_string1, pattern_dir, outdir, TIMEOUT)
            dosdp_pattern_match(ontology_path, pattern_string2, pattern_dir, outdir, TIMEOUT)
        else:
            print("Matches for ({}) already made, bypassing.".format(outdir))
    
    postprocess_modified_patterns = [
        os.path.join(pattern_dir, f)
        for f in os.listdir(pattern_dir)
        if os.path.isfile(os.path.join(pattern_dir, f)) and f.endswith("-modification.yaml")
        ]

    postprocess_modified_patterns(upheno_config, postprocess_modified_patterns, matches_dir)


def add_taxon_restrictions(
    ontology_path, ontology_out_path, taxon_restriction, taxon_label, root_phenotype, preserve_eq
):
    print("Extracting fillers from " + ontology_path)
    global TIMEOUT, upheno_config, legal_iri_patterns_path, legal_pattern_vars_path
    try:
        check_call(
            [
                "timeout",
                TIMEOUT,
                "java",
                upheno_config.get_robot_java_args(),
                "-jar",
                java_taxon,
                ontology_path,
                ontology_out_path,
                taxon_restriction,
                taxon_label,
                root_phenotype,
                preserve_eq,
            ]
        )
    except Exception as e:
        print(e.output)
        raise Exception("Appending taxon restrictions" + ontology_path + " failed")


def download_sources(dir, overwrite=True):
    global upheno_config
    for oid in upheno_config.get_source_ids():
        filename = os.path.join(dir, oid + ".owl")
        url = upheno_config.get_download_location(oid)
        if url not in ["xref"]:
            if overwrite or not os.path.exists(filename):
                robot_convert_merge(url, filename)
            print("%s downloaded successfully." % filename)
            upheno_config.set_path_for_ontology(oid, filename)
    for oid in upheno_config.get_source_ids():
        filename = os.path.join(dir, oid + ".owl")
        url = upheno_config.get_download_location(oid)
        if url in ["xref"]:
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
    shutil.rmtree(stats_dir)
    os.makedirs(stats_dir)


print("### Download patterns ###")
pattern_files = download_patterns(upheno_config.get_pattern_repos(), pattern_dir)
pattern_files = [
    os.path.join(pattern_dir, f)
    for f in os.listdir(pattern_dir)
    if os.path.isfile(os.path.join(pattern_dir, f)) and f.endswith(".yaml")
]

print("### Download sources ###")
print("ROBOT args: " + os.environ["ROBOT_JAVA_ARGS"])
download_sources(module_dir, upheno_config.is_overwrite_ontologies())

print("### Preparing phenotype ontologies for matching ###")
prepare_phenotype_ontologies_for_matching(upheno_config.is_overwrite_ontologies())

print("### Matching phenotype ontologies against uPheno patterns ###")
match_patterns(
    upheno_config, pattern_files, matches_dir, pattern_dir, upheno_config.is_overwrite_matches()
)

print("### Prepare phenotype ontology components for integration in uPheno ###")
prepare_species_specific_phenotype_ontologies(upheno_config)

print("### Prepare master import file with all imports merged ###")
prepare_all_imports_merged(upheno_config)

print("### Prepare master uPheno with no taxon restrictions for relation computation ###")
prepare_upheno_ontology_no_taxon_restictions(upheno_config)
