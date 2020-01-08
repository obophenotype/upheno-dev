#!/usr/bin/env bash

set -e
data=/nfs/production3/spot/sw/dev/monarch/data/upheno-dev/src/scripts

cd $data
#singularity pull docker://obolibrary/odkfull
singularity exec --pwd $data docker://obolibrary/odkfull python3 upheno_prepare.py ../curation/upheno-config.yaml
singularity exec --pwd $data docker://obolibrary/odkfull python3 upheno_create_profiles.py ../curation/upheno-config.yaml