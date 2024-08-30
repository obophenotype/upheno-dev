###############################
#### Mappings and reports #####
###############################

$(TMPDIR)/upheno-species-lexical.csv: upheno.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/phenotype-classes-labels.sparql $@

$(REPORTDIR)/upheno-mapping-all.csv \
$(REPORTDIR)/upheno-mapping-lexical.csv \
$(REPORTDIR)/upheno-mapping-lexical-template.csv: $(TMPDIR)/upheno-species-lexical.csv $(TMPDIR)/upheno-mapping-logical.csv
	python3 ../scripts/lexical_mapping.py all

$(TMPDIR)/upheno-mapping-logical.csv: upheno.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/cross-species-mappings.sparql $@
	#echo "SKIP $@"

$(REPORTDIR)/upheno-associated-entities.csv: upheno.owl
	# TODO replace with relationgraph
	#$(ROBOT) materialize --reasoner ELK -i $< --term "<http://purl.obolibrary.org/obo/UPHENO_0000001>" -o $(TMPDIR)/mat_upheno.owl
	#$(ROBOT) query -i tmp/mat_upheno.owl -f csv --query ../sparql/phenotype_entity_associations.sparql $@
	touch $@

$(MAPPINGDIR)/upheno-oba.sssom.tsv: upheno.owl
	robot query -i $< --query ../sparql/pheno_trait.sparql $@
	sed -i 's/[?]//g' $@
	sed -i 's/<http:[/][/]purl[.]obolibrary[.]org[/]obo[/]/obo:/g' $@
	sed -i 's/>//g' $@

$(MAPPINGDIR)/uberon.sssom.tsv: mirror/uberon.owl
	$(ROBOT) sssom:xref-extract -i $< --mapping-file $@ --map-prefix-to-predicate "UBERON http://w3id.org/semapv/vocab/crossSpeciesExactMatch"

$(REPORTDIR)/upheno-eq-analysis.csv:
	python3 ../scripts/upheno_build.py upheno compute_upheno_statistics \
		--upheno-config ../curation/upheno-config.yaml \
		--patterns-directory ../curation/patterns-for-matching \
		--matches-directory ../curation/pattern-matches
	test -f $@

$(MAPPINGDIR)/upheno-species-independent.sssom.tsv $(MAPPINGDIR)/upheno-species-independent.sssom.owl $(MAPPINGDIR)/uberon.sssom.owl:
	python3 ../scripts/upheno_build.py create-species-independent-sssom-mappings \
		--upheno-id-map ../curation/upheno_id_map.txt \
		--patterns-dir ../curation/patterns-for-matching \
		--anatomy-mappings $(MAPPINGDIR)/uberon.sssom.tsv \
		--matches-dir ../curation/pattern-matches \
		--obsolete-file-tsv ../templates/obsolete.tsv \
		--output-file-owl $(MAPPINGDIR)/upheno-species-independent.sssom.owl \
		--output-file-tsv $(MAPPINGDIR)/upheno-species-independent.sssom.tsv

$(MAPPINGDIR)/%.sssom.owl: $(MAPPINGDIR)/%.sssom.tsv
	sssom convert -i $< -O owl -o $@


custom_reports: $(REPORTDIR)/upheno-associated-entities.csv \
    $(REPORTDIR)/upheno-mapping-all.csv \
    $(REPORTDIR)/upheno-mapping-lexical.csv \
    $(REPORTDIR)/upheno-mapping-lexical-template.csv \
    $(REPORTDIR)/upheno-eq-analysis.csv

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

$(EDIT_PREPROCESSED): $(SRC)
	$(ROBOT) merge -i $< -i imports/merged_import.owl convert --format ofn --output $@

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

upheno-curated.owl: upheno-basic.owl
	$(ROBOT) merge -i upheno-basic.owl \
		query --update ../sparql/rearrange-upheno.ru \
		reduce \
		query --update ../sparql/rearrange-upheno-top.ru \
		annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ \
		convert -f ofn -o $@

upheno-composite.owl: upheno-basic.owl
	$(ROBOT) merge -i upheno-basic.owl \
		query --update ../sparql/rearrange-upheno.ru \
		reduce \
		query --update ../sparql/rearrange-upheno-top.ru \
		annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ \
		convert -f ofn -o $@

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
	test -f ../curation/upheno-release-prepare/all/upheno_layer.owl

############################
###### Components ##########
############################

$(TEMPLATEDIR)/phenotypes-without-patterns.tsv:
	wget "https://docs.google.com/spreadsheets/d/e/2PACX-1vQOEhF0ffls_ALgYT3eLazW2Cn0PdgEozGK7chOaS6Z3g28abWhmy-sz086Xl0c7A-fndEPAEKxPNjv/pub?gid=1901003626&single=true&output=tsv" -O $@

$(TEMPLATEDIR)/phenotype-alignments.tsv:
	wget "https://docs.google.com/spreadsheets/d/e/2PACX-1vQOEhF0ffls_ALgYT3eLazW2Cn0PdgEozGK7chOaS6Z3g28abWhmy-sz086Xl0c7A-fndEPAEKxPNjv/pub?gid=1305526284&single=true&output=tsv" -O $@

$(TEMPLATEDIR)/phenotype-top-level.tsv:
	wget "https://docs.google.com/spreadsheets/d/e/2PACX-1vQOEhF0ffls_ALgYT3eLazW2Cn0PdgEozGK7chOaS6Z3g28abWhmy-sz086Xl0c7A-fndEPAEKxPNjv/pub?gid=627170903&single=true&output=tsv" -O $@

$(COMPONENTSDIR)/upheno-species-neutral.owl:
	$(ROBOT) merge -i ../curation/upheno-release-prepare/all/upheno_layer.owl \
		annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ \
		convert -f ofn -o $@

$(COMPONENTSDIR)/upheno-bridge.owl: $(SRC) $(MAPPINGDIR)/upheno-species-independent.sssom.owl
	$(ROBOT) merge -i $(SRC) -i $(MAPPINGDIR)/upheno-species-independent.sssom.owl \
		query --query $(SPARQLDIR)/construct-upheno-bridge.sparql tmp/bridge.ttl
	$(ROBOT) merge -i tmp/bridge.ttl \
		annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ \
		convert -f ofn -o $@

####################################
###### Import preparation ##########
####################################

ifeq ($(strip $(MERGE_MIRRORS)),true)
$(MIRRORDIR)/merged.owl: $(ALL_MIRRORS)
	$(ROBOT) merge $(patsubst %, -i %, $(ALL_MIRRORS)) \
		remove --axioms disjoint --preserve-structure false remove --term http://www.w3.org/2002/07/owl#Nothing --axioms logical --preserve-structure false \
		remove -T config/terms_to_remove.txt --preserve-structure false \
		query --update ../sparql/rm_declarations.ru \
		convert --format ofn --output $@
.PRECIOUS: $(MIRRORDIR)/merged.owl
endif

$(REPORTDIR)/obsolete_filler_classes.tsv: $(MIRRORDIR)/merged.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/obsolete_filler_classes.sparql $@

add_upheno_ids_to_fillers:
	python3 ../scripts/upheno_build.py add-upheno-ids-to-fillers \
		--upheno-config ../curation/upheno-config.yaml \
		--patterns-directory ../curation/patterns-for-matching \
		--fillers-directory ../curation/upheno-fillers \
		--output-directory ../patterns/data/automatic \
		--tmp-directory ../curation/tmp

merge_modified_patterns:
	python3 ../scripts/upheno_build.py postprocess-modified-patterns \
		--upheno-config ../curation/upheno-config.yaml \
		--patterns-directory ../curation/patterns-for-matching \
		--fillers-directory ../curation/upheno-fillers

FILE_TO_OBSOLETE_URL="https://docs.google.com/spreadsheets/d/e/2PACX-1vQOEhF0ffls_ALgYT3eLazW2Cn0PdgEozGK7chOaS6Z3g28abWhmy-sz086Xl0c7A-fndEPAEKxPNjv/pub?gid=368192736&single=true&output=tsv"

tmp/to_obsolete.tsv:
	#wget $(FILE_TO_OBSOLETE_URL) -O $@
	touch $@

obsolete_fillers:
	#$(MAKE) $(REPORTDIR)/obsolete_filler_classes.tsv tmp/to_obsolete.tsv IMP=false MIR=false -B
	python3 ../scripts/upheno_build.py obsolete-classes-from-tsvs \
		--obsoleted-template ../templates/obsolete.tsv \
		--obsolete-fillers-file $(REPORTDIR)/obsolete_filler_classes.tsv \
		--to-obsolete-entities-file tmp/to_obsolete.tsv \
		--upheno-id-map ../curation/upheno_id_map.txt \
		--dosdp-tsv-directory ../patterns/data/automatic


base_report:
	$(MAKE) IMP=false PAT=false MIR=false upheno-base.owl -B
	$(ROBOT) report -i upheno-base.owl $(REPORT_LABEL) $(REPORT_PROFILE_OPTS) --fail-on $(REPORT_FAIL_ON) --print 5 -o tmp/$@.tsv
