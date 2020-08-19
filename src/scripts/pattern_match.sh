#!/bin/sh
set -e

ONTDIR=../scripts/pattern-matches-oneoff/ontologies/
TEMPLATEDIR=../scripts/pattern-matches-oneoff/upheno_patterns/
TSVDIR=../scripts/pattern-matches-oneoff/matches/

ONTS="mp hp xpo wbphenotype zp"
DOWNLOAD=false

PATTERNS=""

for f in ${TEMPLATEDIR}*.yaml
do
	PATTERNS="${PATTERNS} $(basename "$f" .yaml)"
done
PATTERNS="$(echo -e "${PATTERNS}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

echo "|$PATTERNS|"

if $DOWNLOAD; then
	for o in $ONTS
	do
		wget http://purl.obolibrary.org/obo/${o}.owl -O ${ONTDIR}${o}.owl
	done
fi

for o in ${ONTDIR}*.owl
do
	ONT=${o}
	TSVONT=${TSVDIR}$(basename "$o" .owl)
	mkdir $TSVONT
	sh run.sh dosdp-tools query --ontology=$ONT --reasoner=elk --obo-prefixes=true --template=$TEMPLATEDIR --batch-patterns="${PATTERNS}" --outfile=$TSVONT
done