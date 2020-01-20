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
from lib import uPhenoConfig
from upheno_prepare import prepare_phenotype_ontologies_for_matching

### Configuration
yaml.warnings({'YAMLLoadWarning': False})
upheno_config_file = sys.argv[1]
#upheno_config_file = os.path.join("/ws/upheno-dev/src/curation/upheno-config.yaml")
upheno_config = uPhenoConfig(upheno_config_file)
os.environ['ROBOT_JAVA_ARGS'] = upheno_config.get_robot_java_args()

TIMEOUT=str(upheno_config.get_external_timeout())
ws = upheno_config.get_working_directory()
robot_opts=upheno_config.get_robot_opts()

pattern_dir = os.path.join(ws,"curation/patterns-for-matching/")
matches_dir = os.path.join(ws,"curation/pattern-matches/")
phenotype_classes_sparql = os.path.join(ws, "sparql/phenotype_classes.sparql")

def get_defined_phenotypes(upheno_config,pattern_dir,matches_dir):
    defined = []
    for pattern in os.listdir(pattern_dir):
        if pattern.endswith(".yaml"):
            tsv_file_name = pattern.replace(".yaml",".tsv")
            for oid in upheno_config.get_phenotype_ontologies():
                tsv = os.path.join(matches_dir,oid,tsv_file_name)
                if os.path.exists(tsv):
                    print(tsv)
                    df = pd.read_csv(tsv, sep='\t')
                    defined.extent(df['defined_class'].tolist())
    return list(set(defined))
    
def get_all_phenotypes(upheno_config,stats_dir,ontology_dir):
    phenotypes = []
    for oid in upheno_config.get_phenotype_ontologies():
        phenotype_class_metadata = os.path.join(stats_dir,oid+"_phenotype_data.csv")
        if os.path.exists(phenotype_class_metadata):
            df = pd.read_csv(csv)
            phenotypes.append(df)
        else:
            print("{} does not exist!".format(phenotype_class_metadata))
    return pd.concat(phenotypes)


defined = get_defined_phenotypes(upheno_config,pattern_dir,matches_dir)
df_pheno = get_all_phenotypes()
df_pheno['upheno']=df_pheno['defined_class'].isin(defined)
print(df_pheno.groupby('upheno').count())

