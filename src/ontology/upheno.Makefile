
TMPDIR=../curation/tmp
ONTOLOGIES=hp mp wbphenotype xpo
ONTOLOGY_FILES = $(patsubst %, $(TMPDIR)/%.owl, $(ONTOLOGIES))
OWLTOOLS=OWLTOOLS_MEMORY=150G owltools --no-logging 

merged_ontology.owl: $(ONTOLOGY_FILES)
	$(ROBOT) merge $(patsubst %, -i %, $^) -o $@

inferred_ontology.owl: merged_ontology.owl
	$(ROBOT) reason -i $< --reasoner ELK --axiom-generators "EquivalentClass" -o $@

equivalent_class_table.csv: inferred_ontology.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/equivalent-classes-violation.sparql $@
	

# To get MP/HP mappings:
# ^http://purl.obolibrary.org/obo/[MH]P_[0-9]+[,]http://purl.obolibrary.org/obo/[MH]P_[0-9]+$

# OWLSIM DATA
MONARCH_OWLSIM_DATA=https://raw.githubusercontent.com/monarch-initiative/monarch-owlsim-data/master/data
URL_MP_G2P=$(MONARCH_OWLSIM_DATA)/Mus_musculus/Mm_gene_phenotype.txt
URL_MP_GL=$(MONARCH_OWLSIM_DATA)/Mus_musculus/Mm_gene_labels.txt
URL_HP_D2P=$(MONARCH_OWLSIM_DATA)/Homo_sapiens/Hs_disease_phenotype.txt
URL_HP_DL=$(MONARCH_OWLSIM_DATA)/Homo_sapiens/Hs_disease_labels.txt
URL_ZP_G2P=$(MONARCH_OWLSIM_DATA)/Danio_rerio/Dr_gene_phenotype.txt
URL_ZP_GL=$(MONARCH_OWLSIM_DATA)/Danio_rerio/Dr_gene_labels.txt
MP_G2P=$(TMPDIR)/Mm_gene_phenotype.txt
MP_GL=$(TMPDIR)/Mm_gene_labels.txt
HP_D2P=$(TMPDIR)/Hs_disease_phenotype.txt
HP_DL=$(TMPDIR)/Hs_disease_labels.txt
ZP_G2P=$(TMPDIR)/Dr_gene_phenotype.txt
ZP_GL=$(TMPDIR)/Dr_gene_labels.txt

download_sources: directories
	if ! [ -f $(MP_G2P) ]; then wget $(URL_MP_G2P) -O $(MP_G2P); fi
	if ! [ -f $(MP_GL) ]; then wget $(URL_MP_GL) -O $(MP_GL); fi
	if ! [ -f $(HP_D2P) ]; then wget $(URL_HP_D2P) -O $(HP_D2P); fi
	if ! [ -f $(HP_DL) ]; then wget $(URL_HP_DL) -O $(HP_DL); fi
	if ! [ -f $(ZP_G2P) ]; then wget $(URL_ZP_G2P) -O $(ZP_G2P); fi
	if ! [ -f $(ZP_GL) ]; then wget $(URL_ZP_GL) -O $(ZP_GL); fi

../curation/upheno-release/%/upheno_mapping_lexical.csv: ../curation/upheno-release/all/upheno_species_lexical.csv ../curation/upheno-release/all/upheno_mapping_logical.csv
	python3 ../scripts/lexical_mapping.py $*

../curation/upheno-release/%/upheno_for_semantic_similarity_sub.owl: ../curation/upheno-release/%/upheno_mapping_lexical.csv
	java -jar ../scripts/upheno-assertmatches.jar ../curation/upheno-release/$*/upheno_$*_with_relations.owl $@ $<

../curation/upheno-release/%/upheno_for_semantic_similarity.owl: ../curation/upheno-release/%/upheno_for_semantic_similarity_sub.owl
	$(ROBOT) merge -i ../curation/upheno-release/$*/upheno_$*_with_relations.owl -i $< \
		reason --reasoner ELK --remove-redundant-subclass-axioms false \
		filter --select "self parents" --axioms "SubClassOf EquivalentClasses" --trim false --preserve-structure false -o tmp_$@
	$(OWLTOOLS) tmp_$@ $(MP_G2P) $(HP_D2P) $(ZP_G2P) --merge-imports-closure --load-instances $(MP_G2P) --load-labels $(MP_GL) --merge-support-ontologies -o $@
	rm tmp_$@

../curation/upheno-release/%/upheno_phenodigm_similarity.tsv: ../curation/upheno-release/all/upheno_for_semantic_similarity.owl
	$(OWLTOOLS) $< --sim-save-phenodigm-class-scores -m 2.5 -x HP,MP -a $@

../curation/upheno-release/%/upheno_jaccard_similarity.tsv: ../curation/upheno-release/all/upheno_for_semantic_similarity.owl
	$(OWLTOOLS) $< --make-default-abox --fsim-compare-atts -p ../curation/upheno-sim.properties -o $@

sim: download_sources ../curation/upheno-release/all/upheno_phenodigm_similarity.tsv

#../curation/upheno-release/%/upheno_all_with_relations.ttl: ../curation/upheno-release/%/upheno_all_with_relations.owl
#	$(ROBOT) convert -i $< -o $@

#ttl: ../curation/upheno-release/all/upheno_all_with_relations.ttl
	
.SECONDEXPANSION:
../curation/upheno-release/%/upheno_mapping_logical.csv: ../curation/upheno-release/$$*/upheno_$$*_with_relations.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/cross-species-mappings.sparql $@

../curation/upheno-release/%/upheno_species_lexical.csv: ../curation/upheno-release/$$*/upheno_$$*_with_relations.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/phenotype-classes-labels.sparql $@