#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 8 14:24:37 2018

@author: Nicolas Matentzoglu
"""

import os
import sys
import urllib.request
from shutil import copyfile
from subprocess import check_call

import pandas as pd
import yaml
from lib import cdir, dosdp_pattern_match, get_defined_phenotypes, list_files, uPhenoConfig

### Configuration
yaml.warnings({"YAMLLoadWarning": False})
upheno_config_file = sys.argv[1]
# upheno_config_file = os.path.join("/ws/upheno-dev/src/curation/upheno-config.yaml")
upheno_config = uPhenoConfig(upheno_config_file)
os.environ["ROBOT_JAVA_ARGS"] = upheno_config.get_robot_java_args()

TIMEOUT = upheno_config.get_external_timeout()
ws = upheno_config.get_working_directory()

# Data directories
pattern_dir = os.path.join(ws, "scripts/pattern-matches-oneoff/patterns")
matches_dir = os.path.join(ws, "scripts/pattern-matches-oneoff/matches")
real_patterns_dir = os.path.join(ws, "curation/patterns-for-matching/")
real_matches_dir = os.path.join(ws, "curation/pattern-matches/")
ontology_for_matching_dir = os.path.join(ws, "curation/ontologies-for-matching/")


def match_generic_patterns():
    global upheno_config, ontology_for_matching_dir, pattern_dir, matches_dir, TIMEOUT

    for oid in upheno_config.get_phenotype_ontologies():
        print(oid)
        fn = oid + ".owl"
        o = os.path.join(ontology_for_matching_dir, fn)
        for pattern in list_files(pattern_dir, "yaml"):
            pattern_path = os.path.join(pattern_dir, pattern)
            tsv = os.path.basename(pattern).replace(".yaml", ".tsv")
            tsv_path = os.path.join(matches_dir, tsv)
            dosdp_pattern_match(o, pattern_path, tsv_path, TIMEOUT)


def match_generic_patterns():
    global upheno_config, ontology_for_matching_dir, pattern_dir, matches_dir, TIMEOUT

    for oid in upheno_config.get_phenotype_ontologies():
        print(oid)
        fn = oid + ".owl"
        o = os.path.join(ontology_for_matching_dir, fn)
        matches_dir_byont = os.path.join(matches_dir, oid)
        cdir(matches_dir_byont)
        for pattern in list_files(pattern_dir, "yaml"):
            pattern_path = os.path.join(pattern_dir, pattern)
            tsv = os.path.basename(pattern).replace(".yaml", ".tsv")
            tsv_path = os.path.join(matches_dir_byont, tsv)
            if upheno_config.is_overwrite_matches() or not os.path.exists(tsv_path):
                dosdp_pattern_match(o, pattern_path, tsv_path, TIMEOUT)


def generate_pattern_suggestions():
    global upheno_config, pattern_dir, real_patterns_dir, matches_dir, real_matches_dir
    defined = get_defined_phenotypes(upheno_config, real_patterns_dir, real_matches_dir)
    print(str("http://purl.obolibrary.org/obo/MP_0000400" in defined))
    for pattern in list_files(pattern_dir, "yaml"):
        tsv = os.path.basename(pattern).replace(".yaml", ".tsv")
        df_pattern_list = []
        for oid in upheno_config.get_phenotype_ontologies():
            matches_dir_byont = os.path.join(matches_dir, oid)
            tsv_path = os.path.join(matches_dir_byont, tsv)
            if os.path.exists(tsv_path):
                print(tsv_path)
                df = pd.read_csv(tsv_path, sep="\t")
                df["o"] = oid
                print(df.head())
                if not df.empty:
                    df_pattern_list.append(df[~df["defined_class"].isin(defined)])
        if df_pattern_list:
            df_pattern = pd.concat(df_pattern_list)
            print(df_pattern.head())
            df_pattern["impact"] = df_pattern.groupby("pato_id")["pato_id"].transform("count")
            df_pattern.sort_values("impact", inplace=True, ascending=False)
            tsv_pattern_path = os.path.join(matches_dir, tsv)
            df_pattern.to_csv(tsv_pattern_path, sep="\t", index=False)


# match_generic_patterns()
generate_pattern_suggestions()
