# uPheno 2.0 Pipeline

The uPheno 2 pipeline does the following:

1. Matches all existing uPheno patterns against all species-specific phenotype ontologies
2. Computing intermediate classes for all matches and exports dosdp instance TSV files
3. Assigns uPheno IDs to all classes generated above. Previously generated UPHENO ids are preserved

The pipeline can be run like this:

```
cd src/scripts
sh upheno_pipeline.sh
``` 

Detailed documentation can be found in `upheno_pipeline.sh`.
There are a few java dependencies of the uPheno 2 pipeline which can be found [here](https://github.com/monarch-ebi-dev/phenotype.utils).

