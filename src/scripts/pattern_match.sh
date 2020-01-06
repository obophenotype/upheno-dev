#!/bin/sh
set -e

ONTDIR=../scripts/pattern-matches-oneoff/ontologies/
TEMPLATEDIR=../scripts/pattern-matches-oneoff/patterns/
TSVDIR=../scripts/pattern-matches-oneoff/patterns/

cp ~/ws/human-phenotype-ontology/src/ontology/hp-edit.owl $ONTDIR
cp ~/ws/mammalian-phenotype-ontology/src/ontology/mp-edit.owl $ONTDIR
cp ~/ws/c-elegans-phenotype-ontology/src/ontology/components/wbphenotype-equivalent-axioms-subq.owl $ONTDIR

for o in ${ONTDIR}*.owl
do
	ONT=${o}
	sed -i '' '/^Import/d' ${ONT}
	for f in ${TEMPLATEDIR}*.yaml
	do
		TEMPLATE=${f}
		TSV="${f%.yaml}_$(basename $o).tsv"
		echo "RUNNING MATCH:"
		echo $TEMPLATE
		echo $TSV
		echo $ONT
		sh run.sh dosdp-tools query --ontology=$ONT --reasoner=elk --obo-prefixes=true --template=$TEMPLATE --outfile=$TSV
	done
done