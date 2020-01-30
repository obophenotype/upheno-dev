LABEL=$1
ONT=$2
robot explain --input $ONT --reasoner ELK \
  --axiom "'$LABEL' EquivalentTo owl:Nothing" \
  --output unsat_explanation.ofn 
mv unsat_explanation.ofn ../curation/tmp/unsat.owl
#example sh explain.sh "vagal root" ../curation/upheno-release-prepare/mp-hp/upheno_pre_mp-hp.owl