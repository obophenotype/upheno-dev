###############################
#### Mappings and reports #####
###############################

$(TMPDIR)/upheno_species_lexical.csv: upheno.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/phenotype-classes-labels.sparql $@

$(REPORTDIR)/upheno-mapping-all.csv \
$(REPORTDIR)/upheno-mapping-lexical.csv \
$(REPORTDIR)/upheno-mapping-lexical-template.csv: $(TMPDIR)/upheno_species_lexical.csv $(TMPDIR)/upheno_mapping_logical.csv
	python3 ../scripts/lexical_mapping.py all

$(REPORTDIR)/upheno-mapping-logical.csv: upheno.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/cross-species-mappings.sparql $@
	#echo "SKIP upheno_mapping_logical"

$(REPORTDIR)/upheno-associated-entities.csv: upheno.owl
	# TODO replace with relationgraph
	#$(ROBOT) materialize --reasoner ELK -i $< --term "<http://purl.obolibrary.org/obo/UPHENO_0000001>" -o $(TMPDIR)/mat_upheno.owl
	#$(ROBOT) query -i tmp/mat_upheno.owl -f csv --query ../sparql/phenotype_entity_associations.sparql $@
	touch $@

$(MAPPING_DIR)/upheno-oba.sssom.tsv: upheno.owl
	robot query -i $< --query ../sparql/pheno_trait.sparql $@
	sed -i 's/[?]//g' $@
	sed -i 's/<http:[/][/]purl[.]obolibrary[.]org[/]obo[/]/obo:/g' $@
	sed -i 's/>//g' $@

$(REPORTDIR)/upheno-eq-analysis.csv:
	python3 ../scripts/upheno_build.py upheno compute_upheno_statistics \
		--upheno-config ../curation/upheno-config.yaml \
		--patterns-directory ../curation/patterns-for-matching \
		--matches-directory ../curation/pattern-matches
	test -f $@

$(MAPPING_DIR)/upheno-species-independent.sssom.tsv:
	python3 ../scripts/upheno_build.py upheno create_species_independent_sssom_mappings \
		--upheno_id_map ../curation/upheno_id_map.txt \
		--patterns_dir ../curation/patterns-for-matching \
		--matches_dir ../curation/pattern-matches \
		--output $@

custom_reports: $(REPORTDIR)/upheno-associated-entities \
    $(REPORTDIR)/upheno-mapping-all \
    $(REPORTDIR)/upheno-mapping-lexical \
    $(REPORTDIR)/upheno-mapping-lexical-template \
    $(REPORTDIR)/upheno-eq-analysis

##########################################
####### uPheno release artefacts #########
##########################################

$(TMPDIR)/upheno-incl-lexical-match-equivalencies.owl: upheno.owl $(REPORTDIR)/upheno-mapping-lexical-template.csv
	$(ROBOT) template -i $< --merge-before --template $(REPORTDIR)/upheno-mapping-lexical-template.csv \
   		annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ --output $@.tmp.owl && mv $@.tmp.owl $@
.PRECIOUS: .$(TMPDIR)/upheno-incl-lexical-match-equivalencies.owl

upheno-equivalence-model.owl: $(TMPDIR)/upheno-incl-lexical-match-equivalencies.owl
	$(ROBOT) merge -i $< \
	  query --update ../sparql/upheno-equivalence-model.ru \
	  reason \
	    --reasoner ELK \
	  filter \
	    --term "http://purl.obolibrary.org/obo/UPHENO_0001001" \
	    --select "self descendants equivalents" \
		annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ \
	    --output $@

$(TMPDIR)/upheno-old-metazoa.owl:
	$(ROBOT) merge --input-iri http://purl.obolibrary.org/obo/upheno/metazoa.owl -o $@
.PRECIOUS: $(TMPDIR)/upheno-old-metazoa.owl

upheno-old-model.owl: $(TMPDIR)/upheno-old-metazoa.owl
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
	 annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ \
	 -o $@

###### uPheno pipeline

upheno:
	####### Step 0: Housekeeping ########
	$(MAKE) update_patterns -B

	####### Step 1: download sources and match patterns ########
	$(MAKE) upheno_prepare -B

	####### Step 2: uPheno intermediate layer and species-profiles ########
	$(MAKE) upheno_create_profiles -B

upheno_prepare: ../curation/upheno-config.yaml
	# In this first part of the pipeline, the following steps are executed 
	# (comprehensive configuration of the pipeline can be found in ../curation/upheno-config.yaml)

	# 1. Download all patterns from a set of specified repositories (see config file 'pattern_repos'.)
	#    Optionally, pattern fillers can be replaced by owl:Thing, so that logical definitions with unaligned fillers but 
	#    otherwise matching patterns are considered positive matches
	# 2. Download all source ontologies (see config file: 'sources')
	#    Ontologies are merged and converted two OWL using ROBOT.
	#    For bridge ontologies, a special mode 'xref', allows to try and exploit xrefs directly to construct 
	#    a subclass-of alignment; these should be replaced by proper alignments over time.
	# 3. Prepare phenotype ontologies for matching.
	#    Phenotype ontologies with all their imports (a special imports module) are merged. Taxon restrictions
	#    are introduced and labels rewritten.
	# 4. Match patterns: All patterns as downloaded in step 1.1 are matched agains all phenotype ontologies.
	#    This results in one tsv file with matches per phenotype ontology and pattern.
	python ../scripts/upheno_prepare.py ../curation/upheno-config.yaml

upheno_create_profiles: ../curation/upheno-config.yaml
	# 1. Extract uPheno fillers from pattern matches (step 1.4). The primary bearer is filled up, 
	#    i.e. every class between the pattern filler and a particular species specific filler class is instantiated
	#    (minus a blacklist)
	# 2. For every profile (config 'upheno_combinations'), create a new directory, then compile all patterns 
	#    from the previous step using dosdp. Add taxon restrictions 
	python ../scripts/upheno_create_profiles.py ../curation/upheno-config.yaml
	test -f ../curation/curation/upheno-release-prepare/all/upheno_layer.owl

############################
###### Components ##########
############################

$(TEMPLATEDIR)/phenotypes-without-patterns.tsv:
	wget "https://docs.google.com/spreadsheets/d/e/2PACX-1vQOEhF0ffls_ALgYT3eLazW2Cn0PdgEozGK7chOaS6Z3g28abWhmy-sz086Xl0c7A-fndEPAEKxPNjv/pub?gid=1901003626&single=true&output=tsv" -O $@

$(TEMPLATEDIR)/phenotype-alignments.tsv:
	wget "https://docs.google.com/spreadsheets/d/e/2PACX-1vQOEhF0ffls_ALgYT3eLazW2Cn0PdgEozGK7chOaS6Z3g28abWhmy-sz086Xl0c7A-fndEPAEKxPNjv/pub?gid=1305526284&single=true&output=tsv" -O $@

$(COMPONENTSDIR)/upheno-species-neutral.owl:
	$(ROBOT) merge -i ../curation/curation/upheno-release-prepare/all/upheno_layer.owl \
		annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ \
		convert -f ofn -o $@

####################################
###### Import preparation ##########
####################################

ifeq ($(strip $(MERGE_MIRRORS)),true)
$(MIRRORDIR)/merged.owl: $(ALL_MIRRORS)
	$(ROBOT) merge $(patsubst %, -i %, $^) \
		remove --axioms disjoint --preserve-structure false remove --term http://www.w3.org/2002/07/owl#Nothing --axioms logical --preserve-structure false \
		remove -T config/terms_to_remove.txt --preserve-structure false \
		convert --format ofn --output $@
.PRECIOUS: $(MIRRORDIR)/merged.owl
endif


debug_fillers:
	python3 ../scripts/upheno_build.py add-upheno-ids-to-fillers \
		--upheno-config ../curation/upheno-config.yaml \
		--patterns-directory ../curation/patterns-for-matching \
		--fillers-directory ../curation/upheno-fillers \
		--tmp-directory ../curation/tmp