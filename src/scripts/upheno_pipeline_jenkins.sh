#!/bin/sh

set -e

# Author: Nicolas Matentzoglu, European Bioinformatics Institute (EMBL-EBI)
# Monarch Initiative, https://monarchinitiative.org

ls -l ../sparql
ls -l ../ontology
pwd
python3 upheno_prepare.py ../curation/upheno-config.yaml
python3 upheno_create_profiles.py ../curation/upheno-config.yaml

