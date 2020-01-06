#!/usr/bin/env bash

set -e
data=/nfs/production3/spot/sw/dev/monarch/data/upheno-dev/src/scripts

cd $data
#singularity pull docker://obolibrary/odkfull
singularity shell --pwd $data docker://obolibrary/odkfull -c "python3 upheno_prepare.py ../curation/upheno-config.yaml"
singularity shell --pwd $data docker://obolibrary/odkfull -c "python3 upheno_create_profiles.py ../curation/upheno-config.yaml"