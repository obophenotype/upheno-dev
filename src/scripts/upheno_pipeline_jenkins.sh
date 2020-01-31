#!/bin/sh

set -e

# Author: Nicolas Matentzoglu, European Bioinformatics Institute (EMBL-EBI)
# Monarch Initiative, https://monarchinitiative.org

pwd
ls -l ../ontology
ls -l ../curation
#echo "REMOVING ALLIMPORTSMERGED.OWL REMOVEREMOVEREMOVE"
#sh explain.sh "nurse cell" ../curation/tmp/upheno-allimports-merged.owl ../curation/tmp/ex_nursecell.owl
#sh explain.sh "adult intestinal epithelium" ../curation/tmp/upheno-allimports-merged.owl ../curation/tmp/ex_adultintestinal.owl
#rm -f ../curation/tmp/upheno-allimports-merged.owl
#rm -f ../curation/tmp/upheno-allimports-dosdp.owl
python3 upheno_prepare.py ../curation/upheno-config.yaml
python3 upheno_create_profiles.py ../curation/upheno-config.yaml
python3 upheno-stats.py ../curation/upheno-config.yaml

