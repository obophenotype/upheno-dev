
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
MONARCH_OWLSIM_DATA=https://archive.monarchinitiative.org/latest/owlsim/data/
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

download_sources:
	if ! [ -f $(MP_G2P) ]; then wget $(URL_MP_G2P) -O $(MP_G2P); fi
	if ! [ -f $(MP_GL) ]; then wget $(URL_MP_GL) -O $(MP_GL); fi
	if ! [ -f $(HP_D2P) ]; then wget $(URL_HP_D2P) -O $(HP_D2P); fi
	if ! [ -f $(HP_DL) ]; then wget $(URL_HP_DL) -O $(HP_DL); fi
	if ! [ -f $(ZP_G2P) ]; then wget $(URL_ZP_G2P) -O $(ZP_G2P); fi
	if ! [ -f $(ZP_GL) ]; then wget $(URL_ZP_GL) -O $(ZP_GL); fi



#../curation/upheno-release/%/upheno_phenodigm_similarity.tsv: ../curation/upheno-release/all/upheno_for_semantic_similarity.owl
#	$(OWLTOOLS) $< --sim-save-phenodigm-class-scores -m 2.5 -x HP,MP -a $@

#../curation/upheno-release/%/upheno_jaccard_similarity.tsv: ../curation/upheno-release/all/upheno_for_semantic_similarity.owl
#	$(OWLTOOLS) $< --make-default-abox --fsim-compare-atts -p ../curation/upheno-sim.properties -o $@

#../curation/upheno-release/%/upheno_all_with_relations.ttl: ../curation/upheno-release/%/upheno_all_with_relations.owl
#	$(ROBOT) convert -i $< -o $@

#ttl: ../curation/upheno-release/all/upheno_all_with_relations.ttl
upheno_mapping_lexical_all: ../curation/upheno-release/all/upheno_species_lexical.csv ../curation/upheno-release/all/upheno_mapping_logical.csv
	python3 ../scripts/lexical_mapping.py all
	#echo "SKIP upheno_mapping_lexical_"

#.SECONDEXPANSION:
../curation/upheno-release/all/upheno_mapping_logical.csv: ../curation/upheno-release/all/upheno_all_with_relations.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/cross-species-mappings.sparql $@
	#echo "SKIP upheno_mapping_logical"

../curation/upheno-release/all/upheno_species_lexical.csv: ../curation/upheno-release/all/upheno_all_with_relations.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/phenotype-classes-labels.sparql $@
	#echo "SKIP upheno_species_lexical"

../curation/upheno-release/all/upheno_associated_entities.csv: ../curation/upheno-release/all/upheno_all_with_relations.owl
	#$(ROBOT) materialize --reasoner ELK -i $< --term "<http://purl.obolibrary.org/obo/UPHENO_0000001>" -o tmp/mat_upheno.owl
	$(ROBOT) query -i tmp/mat_upheno.owl -f csv --query ../sparql/phenotype_entity_associations.sparql $@

../curation/upheno-release/all/upheno_parentage.csv: ../curation/upheno-release/all/upheno_all_with_relations.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/phenotype_upheno_parents.sparql $@

../curation/upheno-release/all/upheno_lexical_data.csv: ../curation/upheno-release/all/upheno_all_with_relations.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/phenotype_upheno_lexical.sparql $@

../curation/upheno-release/all/upheno_xrefs.csv: ../curation/upheno-release/all/upheno_all_with_relations.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/phenotype_xrefs.sparql $@


../curation/upheno-release/all/upheno_labels.owl: ../curation/upheno-release/all/upheno_all_with_relations.owl
	$(ROBOT) filter -i $< \
		--term "http://purl.obolibrary.org/obo/UPHENO_0001001" \
		--select "self descendants annotations" \
		filter --term rdfs:label --trim false -o $@
	#echo "SKIP upheno_labels"
	
../curation/upheno-release/all/upheno_special_labels.owl: ../curation/upheno-release/all/upheno_old_metazoa.owl
	$(ROBOT) query -i $< --query ../sparql/construct_phenotype_iri_labels.sparql $@
	# echo "SKIP upheno_special_labels"

../curation/upheno-release/all/upheno_incl_lexical.owl: ../curation/upheno-release/all/upheno_all_with_relations.owl upheno_mapping_lexical_all
	$(ROBOT) template -i $< --merge-before --template ../curation/upheno-release/all/upheno_mapping_lexical_template.csv \
    annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ --output $@.tmp.owl && mv $@.tmp.owl $@
	#echo "SKIP upheno_species_lexical"
.PRECIOUS: ../curation/upheno-release/all/upheno_incl_lexical.owl

../curation/upheno-release/all/upheno_equivalence_model.owl: ../curation/upheno-release/all/upheno_incl_lexical.owl
	#echo "SKIP upheno_equivalence_model_semsim"
	$(ROBOT) query -i $< --update ../sparql/upheno-equivalence-model.ru --output $@.tmp.owl && mv $@.tmp.owl $@
.PRECIOUS: ../curation/upheno-release/all/upheno_equivalence_model.owl

../curation/upheno-release/all/upheno_equivalence_model_semsim.owl: ../curation/upheno-release/all/upheno_equivalence_model.owl ../curation/upheno-release/all/upheno_labels.owl
	#echo "SKIP upheno_equivalence_model_semsim"
	$(ROBOT) merge -i $< \
	  reason \
	    --reasoner ELK \
	  filter \
	    --term "http://purl.obolibrary.org/obo/UPHENO_0001001" \
	    --select "self descendants equivalents" \
		merge -i ../curation/upheno-release/all/upheno_labels.owl \
		annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ \
	    --output $@

../curation/upheno-release/all/upheno_lattice_model_subs.owl: ../curation/upheno-release/all/upheno_incl_lexical.owl ../curation/upheno-release/all/upheno_mapping_lexical.csv
	java -jar ../scripts/upheno-assertmatches.jar $< $@ ../curation/upheno-release/all/upheno_mapping_lexical.csv
	#echo "Skip upheno_lattice_model_subs"


../curation/upheno-release/all/upheno_lattice_model.owl: ../curation/upheno-release/all/upheno_incl_lexical.owl ../curation/upheno-release/all/upheno_lattice_model_subs.owl
	$(ROBOT) merge -i $< -i ../curation/upheno-release/all/upheno_lattice_model_subs.owl -o $@
	# echo "Skip upheno_lattice_model_subs"
.PRECIOUS: ../curation/upheno-release/all/upheno_lattice_model.owl

../curation/upheno-release/all/upheno_lattice_model_semsim.owl: ../curation/upheno-release/all/upheno_lattice_model.owl ../curation/upheno-release/all/upheno_labels.owl
	#echo "Skip upheno_lattice_model_semsim"
	$(ROBOT) merge -i $< \
		reason \
			--reasoner ELK \
		filter \
			--term "http://purl.obolibrary.org/obo/UPHENO_0001001" \
			--select "self descendants equivalents" \
		merge -i ../curation/upheno-release/all/upheno_labels.owl \
		annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ \
	    --output $@

../curation/upheno-release/all/upheno_old_metazoa.owl:
	$(ROBOT) merge --input-iri http://purl.obolibrary.org/obo/upheno/metazoa.owl -o $@
	#echo "skip upheno_old_metazoa"

../curation/upheno-release/all/upheno_old_metazoa_semsim.owl: ../curation/upheno-release/all/upheno_old_metazoa.owl ../curation/upheno-release/all/upheno_labels.owl ../curation/upheno-release/all/upheno_special_labels.owl
	#echo "SKIP upheno_old_metazoa_semsim"
	$(ROBOT) remove -i $< --axioms DisjointClasses \
	 remove --axioms DisjointUnion \
	 remove --axioms DifferentIndividuals \
	 remove --axioms NegativeObjectPropertyAssertion \
	 remove --axioms NegativeDataPropertyAssertion \
	 remove --axioms FunctionalObjectProperty \
	 remove --axioms InverseFunctionalObjectProperty \
	 remove --axioms ReflexiveObjectProperty \
	 remove --axioms IrrefexiveObjectProperty \
	 remove --axioms DisjointObjectProperties \
	 remove --axioms FunctionalDataProperty \
	 remove --axioms DisjointDataProperties \
	 remove --term owl:Nothing \
	 remove --axioms "annotation" \
	 reason --reasoner ELK \
	 filter \
	    --term "http://purl.obolibrary.org/obo/UPHENO_0001001" \
	    --select "self descendants equivalents" \
	 merge -i ../curation/upheno-release/all/upheno_labels.owl \
	 merge -i ../curation/upheno-release/all/upheno_special_labels.owl \
	 annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ \
	 -o $@

SIMCUTOFF=0.5
../curation/upheno-release/all/upheno_%_jaccard.tsv: ../curation/upheno-release/all/upheno_%_semsim.owl
	java -jar ../scripts/upheno-semanticsimilarity.jar $< ../curation/tmp/mp-class-hierarchy.txt ../curation/tmp/hp-class-hierarchy.txt "http://purl.obolibrary.org/obo/UPHENO_0001001" $@ nm $(SIMCUTOFF)

o: ../curation/upheno-release/all/upheno_old_metazoa_semsim.owl ../curation/upheno-release/all/upheno_lattice_model_semsim.owl ../curation/upheno-release/all/upheno_equivalence_model_semsim.owl

sim: ../curation/upheno-release/all/upheno_old_metazoa_jaccard.tsv ../curation/upheno-release/all/upheno_lattice_model_jaccard.tsv ../curation/upheno-release/all/upheno_equivalence_model_jaccard.tsv

ml: ../curation/upheno-release/all/upheno_xrefs.csv ../curation/upheno-release/all/upheno_parentage.csv ../curation/upheno-release/all/upheno_associated_entities.csv ../curation/upheno-release/all/upheno_lexical_data.csv

t:
	$(ROBOT) filter -I https://raw.githubusercontent.com/monarch-ebi-dev/ontologies/master/small_insulin_test.owl \
		merge -I https://raw.githubusercontent.com/monarch-ebi-dev/ontologies/master/smalltest.owl -o rm_test.owl


conf: ../../modules/upheno_all_pattern_conformance.owl

tmp/patterns:
	rm -r $@
	mkdir $@


../../modules/upheno_all_pattern_conformance.owl: $(PATTERNS) tmp/patterns
	python3 ../scripts/create_pattern_conformance_module.py

#RELDIR=../curation/upheno-release
RELDIR=../curation/upheno-stats ../curation/pattern-matches ../curation/upheno-release
BUCKETDIR=../curation/s3
#aws s3 
# we now use S3 directly

S3_VERSION=2020-05-17

prepare_upload:
	mkdir -p $(BUCKETDIR)/ 
	rm -rf $(BUCKETDIR)/*
	mkdir -p $(BUCKETDIR)/current/ 
	mkdir -p $(BUCKETDIR)/$(S3_VERSION)/
	cp -r $(RELDIR) $(BUCKETDIR)/current/
	cp -r $(RELDIR) $(BUCKETDIR)/$(S3_VERSION)/
	cp ../curation/upheno_id_map.txt $(BUCKETDIR)/current/
	cp ../curation/upheno_id_map.txt $(BUCKETDIR)/$(S3_VERSION)/

deploy:
	aws s3 sync --exclude "*.DS_Store*" $(BUCKETDIR)/current s3://bbop-ontologies/upheno/current --acl public-read
	aws s3 sync --exclude "*.DS_Store*" $(BUCKETDIR)/$(S3_VERSION) s3://bbop-ontologies/upheno/$(S3_VERSION) --acl public-read

## Set yourself up for AWS:


## Reports:
UPHENO_RELEASE_FILE_ANALYSIS=../curation/upheno-release/all/upheno_all_with_relations.owl

reports: reports/phenotype_trait.sssom.tsv

reports/phenotype_trait.sssom.tsv: $(UPHENO_RELEASE_FILE_ANALYSIS)
	robot query -i $< --query ../sparql/pheno_trait.sparql $@
