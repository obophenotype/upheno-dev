
DIR=../curation/tmp
ONTOLOGIES=hp mp wbphenotype xpo
ONTOLOGY_FILES = $(patsubst %, $(DIR)/%.owl, $(ONTOLOGIES))

merged_ontology.owl: $(ONTOLOGY_FILES)
	$(ROBOT) merge $(patsubst %, -i %, $^) -o $@

inferred_ontology.owl: merged_ontology.owl
	$(ROBOT) reason -i $< --reasoner ELK --axiom-generators "EquivalentClass" -o $@

equivalent_class_table.csv: inferred_ontology.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/equivalent-classes-violation.sparql $@