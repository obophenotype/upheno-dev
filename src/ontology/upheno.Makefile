
DIR=../curation/tmp
ONTOLOGIES=hp mp wbphenotype xpo
ONTOLOGY_FILES = $(patsubst %, $(DIR)/%.owl, $(ONTOLOGIES))
OWLTOOLS=owltools

merged_ontology.owl: $(ONTOLOGY_FILES)
	$(ROBOT) merge $(patsubst %, -i %, $^) -o $@

inferred_ontology.owl: merged_ontology.owl
	$(ROBOT) reason -i $< --reasoner ELK --axiom-generators "EquivalentClass" -o $@

equivalent_class_table.csv: inferred_ontology.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/equivalent-classes-violation.sparql $@
	

# To get MP/HP mappings:
# ^http://purl.obolibrary.org/obo/[MH]P_[0-9]+[,]http://purl.obolibrary.org/obo/[MH]P_[0-9]+$
../curation/upheno-release/%/upheno_mapping_logical.csv: ../curation/upheno-release/%/upheno_$*_with_relations.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/cross-species-mappings.sparql $@

../curation/upheno-release/%/upheno_species_lexical.csv: ../curation/upheno-release/%/upheno_all_with_relations.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/phenotype-classes-labels.sparql $@	

../curation/upheno-release/%/upheno_mapping_lexical.csv: #../curation/upheno-release/all/upheno_species_lexical.csv ../curation/upheno-release/all/upheno_mapping_logical.csv
	python3 ../scripts/lexical_mapping.py $*
	echo "skip"

../curation/upheno-release/%/upheno_for_semantic_similarity_sub.owl: ../curation/upheno-release/%/upheno_mapping_lexical.csv
	java -jar ../scripts/upheno-assertmatches.jar ../curation/upheno-release/$*/upheno_$*_with_relations.owl $@ $<

../curation/upheno-release/%/upheno_for_semantic_similarity.owl: ../curation/upheno-release/%/upheno_for_semantic_similarity_sub.owl
	$(ROBOT) merge -i ../curation/upheno-release/$*/upheno_$*_with_relations.owl -i $< -o $@

../curation/upheno-release/%/upheno_phenodigm_similarity.tsv: ../curation/upheno-release/all/upheno_for_semantic_similarity.owl
	$(OWLTOOLS) $< --sim-save-phenodigm-class-scores -m 2.5 -x HP,MP -a $@

../curation/upheno-release/%/upheno_jaccard_similarity.tsv: ../curation/upheno-release/all/upheno_for_semantic_similarity.owl
	$(OWLTOOLS) $< --make-default-abox --fsim-compare-atts -p ../curation/upheno-sim.properties -o $@

sim: ../curation/upheno-release/all/upheno_jaccard_similarity.tsv ../curation/upheno-release/all/upheno_phenodigm_similarity.tsv

#../curation/upheno-release/%/upheno_all_with_relations.ttl: ../curation/upheno-release/%/upheno_all_with_relations.owl
#	$(ROBOT) convert -i $< -o $@

#ttl: ../curation/upheno-release/all/upheno_all_with_relations.ttl
	
