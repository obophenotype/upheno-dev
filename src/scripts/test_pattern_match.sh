#!/bin/sh

dosdp-tools query --ontology=../curation/ontologies-for-matching/mp.owl --reasoner=elk --obo-prefixes=true --template=../curation/patterns-for-matching/abnormalAnatomicalEntity.yaml --outfile=../curation/pattern-matches/mp/abnormalAnatomicalEntity.tsv