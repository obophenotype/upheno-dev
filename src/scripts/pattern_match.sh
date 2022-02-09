#!/bin/bash
set -e

patterndir=$1
matchesdir=$2

ONTDIR=../scripts/pattern-matches/ontologies/
TEMPLATEDIR=../scripts/pattern-matches/$patterndir/
TSVDIR=../scripts/pattern-matches/$matchesdir/

ONTS="mp hp xpo wbphenotype"
#: "${DOWNLOAD:=false}"

DOWNLOAD=true

PATTERNS=""

mkdir -p $ONTDIR $TSVDIR

for f in ${TEMPLATEDIR}*.yaml
do
	PATTERNS="${PATTERNS} $(basename "$f" .yaml)"
done
PATTERNS="$(echo "${PATTERNS}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

echo "|$PATTERNS|"

if $DOWNLOAD; then
	for o in $ONTS
	do
		wget http://purl.obolibrary.org/obo/${o}.owl -O ${ONTDIR}${o}.owl
	done
fi

echo "\ndownloading: $TEMPLATEDIR, $PATTERNS"

for o in ${ONTDIR}*.owl
do
	ONT=${o}
	TSVONT=${TSVDIR}$(basename "$o" .owl)
	sh run.sh dosdp-tools query --ontology=$ONT --reasoner=elk --obo-prefixes=true --template=$TEMPLATEDIR --batch-patterns="${PATTERNS}" --outfile=$TSVDIR
done
