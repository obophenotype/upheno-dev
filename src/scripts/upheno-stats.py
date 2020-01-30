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
from lib import uPhenoConfig, get_defined_phenotypes

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
stats_dir = os.path.join(ws,"curation/upheno-stats/")
matches_dir = os.path.join(ws,"curation/pattern-matches/")



def get_all_phenotypes(upheno_config,stats_dir):
    phenotypes = []
    for oid in upheno_config.get_phenotype_ontologies():
        phenotype_class_metadata = os.path.join(stats_dir,oid+"_phenotype_data.csv")
        if os.path.exists(phenotype_class_metadata):
            try:
                df = pd.read_csv(phenotype_class_metadata)
                df['o']=oid
                phenotypes.append(df)
            except:
                print("{} could not be loaded..".format(phenotype_class_metadata))
        else:
            print("{} does not exist!".format(phenotype_class_metadata))
    return pd.concat(phenotypes)


defined = get_defined_phenotypes(upheno_config,pattern_dir,matches_dir)
df_pheno = get_all_phenotypes(upheno_config,stats_dir)
df_pheno['upheno']=df_pheno['s'].isin(defined)
df_pheno['eq']=df_pheno['ldef'].notna()
df_pheno.drop_duplicates(inplace=True)

print("Summary: ")
print(df_pheno.head())
print(df_pheno.describe())
print("")
print("How many uPheno conformant classes?")
print(df_pheno[['s','upheno']].groupby('upheno').count())
print("")
print("How many classes with EQs?")
print(df_pheno[['s','eq']].groupby('eq').count())
print("")
print("How many uPheno conformant classes that do not have EQs (bug!!)?")
print(df_pheno[df_pheno['upheno'] & (~df_pheno['eq'])])
print(df_pheno[df_pheno['upheno']][['s','eq']].groupby('eq').count())
