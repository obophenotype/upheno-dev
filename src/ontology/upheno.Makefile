
SSPOS = mp hp zp dpo wbphenotype xpo planp ddpheno fypo apo mgpo phipo

%.db: %.owl
	@rm -f $*.db
	@rm -f .template.db
	@rm -f .template.db.tmp
	@rm -f $*-relation-graph.tsv.gz
	RUST_BACKTRACE=full semsql make $*.db -P config/prefixes.csv
	@rm -f .template.db
	@rm -f .template.db.tmp
	@rm -f $*-relation-graph.tsv.gz
	@test -f $*.db || (echo "Error: File not found!" && exit 1)

.PRECIOUS: %.db

###############################
#### Mappings and reports #####
###############################

$(TMPDIR)/upheno-species-lexical.csv: upheno.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/phenotype-classes-labels.sparql $@

$(TMPDIR)/upheno-species-lexical-oak.sssom.tsv: upheno.db
	runoak -i sqlite:$< lexmatch -R config/upheno-match-rules.yaml -o $@

# Currently only the oak lexical match is used for the upheno-lexical.sssom.tsv
# Should this be a merge of the upheno-species-independent.sssom.tsv and oak lexical match?
$(MAPPINGDIR)/upheno-lexical.sssom.tsv: $(TMPDIR)/upheno-species-lexical-oak.sssom.tsv
	sssom filter $< -o $@ --predicate_id skos:exactMatch

$(TMPDIR)/upheno-mapping-logical.csv: upheno.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/cross-species-mappings.sparql $@
	#echo "SKIP $@"

$(REPORTDIR)/upheno-associated-entities.csv: upheno.owl
	# TODO replace with relationgraph
	#$(ROBOT) materialize --reasoner ELK -i $< --term "<http://purl.obolibrary.org/obo/UPHENO_0000001>" -o $(TMPDIR)/mat_upheno.owl
	#$(ROBOT) query -i tmp/mat_upheno.owl -f csv --query ../sparql/phenotype_entity_associations.sparql $@
	touch $@

$(TMPDIR)/oba.owl:
	wget -O $@ "http://purl.obolibrary.org/obo/oba.owl"

$(TMPDIR)/upheno-oba.owl: upheno.owl $(TMPDIR)/oba.owl $(COMPONENTSDIR)/upheno-haspart-characteristicofpartof-chain.owl
	$(ROBOT) merge -i upheno.owl -i $(TMPDIR)/oba.owl -i $(COMPONENTSDIR)/upheno-haspart-characteristicofpartof-chain.owl \
		remove --axioms DisjointClasses \
		remove --term rdfs:label --select complement --select annotation-properties \
		materialize --term BFO:0000051 \
		query --update ../sparql/pheno_trait.ru \
		reason reduce \
		query --update ../sparql/pheno_trait_materialise.ru -o $@

$(TMPDIR)/upheno-oba.json: $(TMPDIR)/upheno-oba.owl
	$(ROBOT) convert -i $(TMPDIR)/upheno-oba.owl -o $@

$(MAPPINGDIR)/upheno-oba.sssom.tsv: $(TMPDIR)/upheno-oba.json
	sssom parse $(TMPDIR)/upheno-oba.json -I obographs-json -C merged -F UPHENO:phenotypeToTrait -o $@

$(MAPPINGDIR)/upheno-oba.kgx: $(TMPDIR)/upheno-oba.json
	kgx transform --input-format obojson \
                  --output $@ \
                  --output-format tsv \
                  $(TMPDIR)/upheno-oba.json
	awk 'NR==1 || /UPHENO:phenotypeToTrait/' $(MAPPINGDIR)/upheno-oba.kgx_edges.tsv > $(TMPDIR)/upheno-oba.kgx_edges.tsv
	mv $(TMPDIR)/upheno-oba.kgx_edges.tsv $(MAPPINGDIR)/upheno-oba.kgx_edges.tsv
	rm $(MAPPINGDIR)/upheno-oba.kgx_nodes.tsv
	touch $@

$(MAPPINGDIR)/uberon.sssom.tsv: mirror/uberon.owl
	if [ $(COMP) = true ] ; then $(ROBOT) sssom:xref-extract -i $< --mapping-file $@ --map-prefix-to-predicate "UBERON http://w3id.org/semapv/vocab/crossSpeciesExactMatch"; fi

$(REPORTDIR)/%_phenotype_data.csv: $(MIRRORDIR)/%.owl $(SPARQLDIR)/%_phenotypes.sparql
	$(ROBOT) query -f csv -i $< --query $(SPARQLDIR)/$*_phenotypes.sparql $@

$(REPORTDIR)/upheno-eq-analysis.csv: $(foreach n,$(SSPOS), $(REPORTDIR)/$(n)_phenotype_data.csv)
	python3 ../scripts/upheno_build.py compute-upheno-statistics \
		--upheno-config ../curation/upheno-config.yaml \
		--pattern-directory ../curation/patterns-for-matching \
		--matches-directory ../curation/pattern-matches \
		--stats-directory $(REPORTDIR)/
	test -f $@

# TODO missing dependency for "a change in a file in ../curation/pattern-matches" which
# is the true dependency here
$(MAPPINGDIR)/upheno-species-independent.sssom.tsv $(MAPPINGDIR)/upheno-species-independent.sssom.owl $(MAPPINGDIR)/uberon.sssom.owl: $(MAPPINGDIR)/uberon.sssom.tsv ../templates/obsolete.tsv ../curation/upheno_id_map.txt
	if [ $(COMP) = true ] ; then python3 ../scripts/upheno_build.py create-species-independent-sssom-mappings \
		--upheno-id-map ../curation/upheno_id_map.txt \
		--patterns-dir ../curation/patterns-for-matching \
		--anatomy-mappings $(MAPPINGDIR)/uberon.sssom.tsv \
		--matches-dir ../curation/pattern-matches \
		--obsolete-file-tsv ../templates/obsolete.tsv \
		--output-file-owl $(MAPPINGDIR)/upheno-species-independent.sssom.owl \
		--output-file-tsv $(MAPPINGDIR)/upheno-species-independent.sssom.tsv; fi

$(MAPPINGDIR)/upheno-cross-species.sssom.tsv: $(TMPDIR)/upheno-species-lexical.csv $(TMPDIR)/upheno-mapping-logical.csv
	mkdir -p $(TMPDIR)/cross-species/
	python3 ../scripts/upheno_build.py generate-cross-species-mappings --species-lexical $(TMPDIR)/upheno-species-lexical.csv -m $(TMPDIR)/upheno-mapping-logical.csv -o $(TMPDIR)/cross-species/
	sssom parse $(TMPDIR)/cross-species/upheno_custom_mapping.sssom.tsv --metadata config/upheno-cross-species.sssom.tsv -C merged -o $@

$(MAPPINGDIR)/%.sssom.owl: $(MAPPINGDIR)/%.sssom.tsv
	sssom convert -i $< -O owl -o $@

semsim/upheno-0.4.semsimian.tsv: upheno.db $(IMPORTDIR)/all_phenotype_terms.txt
	runoak --stacktrace -vvv -i semsimian:sqlite:upheno.db similarity -p i \
	--set1-file $(IMPORTDIR)/all_phenotype_terms.txt \
	--set2-file $(IMPORTDIR)/all_phenotype_terms.txt \
	--min-jaccard-similarity 0.4 -O csv -o $@

custom_reports: $(REPORTDIR)/upheno-associated-entities.csv \
    $(REPORTDIR)/upheno-eq-analysis.csv

##########################################
####### uPheno release artefacts #########
##########################################

# $(MAPPINGDIR)/upheno-cross-species.sssom.tsv is a dependency here because that goal
# is responsible for generating $(TMPDIR)/cross-species/upheno_lexical_mapping.robot.template.tsv as well
$(TMPDIR)/upheno-incl-lexical-match-equivalencies.owl: upheno.owl $(MAPPINGDIR)/upheno-cross-species.sssom.tsv
	$(ROBOT) template -i $< --merge-before --template $(TMPDIR)/cross-species/upheno_lexical_mapping.robot.template.tsv \
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
		convert -f owl -o $@

upheno-base-with-bridge.owl: upheno-base.owl $(COMPONENTSDIR)/upheno-bridge.owl
	$(ROBOT) merge -i upheno-base.owl -i $(COMPONENTSDIR)/upheno-bridge.owl \
		annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ \
		convert -f owl -o $@

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
	wget "https://docs.google.com/spreadsheets/d/1TDDGUKLME28ZLE5YayXNOwAkBD7jDoAgLPuTkYoMAs0/pub?gid=1901003626&single=true&output=tsv" -O $@

$(TEMPLATEDIR)/phenotype-alignments.tsv:
	wget "https://docs.google.com/spreadsheets/d/1TDDGUKLME28ZLE5YayXNOwAkBD7jDoAgLPuTkYoMAs0/pub?gid=1305526284&single=true&output=tsv" -O $@

$(TEMPLATEDIR)/phenotype-top-level.tsv:
	wget "https://docs.google.com/spreadsheets/d/1TDDGUKLME28ZLE5YayXNOwAkBD7jDoAgLPuTkYoMAs0/pub?gid=627170903&single=true&output=tsv" -O $@

$(TEMPLATEDIR)/root-alignments.tsv:
	wget "https://docs.google.com/spreadsheets/d/1TDDGUKLME28ZLE5YayXNOwAkBD7jDoAgLPuTkYoMAs0/pub?gid=1260598340&single=true&output=tsv" -O $@

$(TEMPLATEDIR)/axiom-injections.tsv:
	wget "https://docs.google.com/spreadsheets/d/e/2PACX-1vRx0gi2I-Ks14LGNibiy6YzW-3A45_jZOnYsBNmaIjF3M8vrXboJwBYle525RXVscXhGGlOzGe05VhX/pub?gid=1825106877&single=true&output=tsv" -O $@

$(COMPONENTSDIR)/upheno-species-neutral.owl:
	$(ROBOT) merge -i ../curation/upheno-release-prepare/all/upheno_layer.owl \
		annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ \
		convert -f ofn -o $@

$(COMPONENTSDIR)/upheno-bridge.owl: $(SRC) $(MAPPINGDIR)/upheno-species-independent.sssom.owl
	$(ROBOT) merge -i $(SRC) -i $(MAPPINGDIR)/upheno-species-independent.sssom.owl \
		query --query $(SPARQLDIR)/construct-upheno-bridge.sparql tmp/bridge.ttl
	$(ROBOT) merge -i tmp/bridge.ttl -i $(MAPPINGDIR)/upheno-species-independent.sssom.owl \
		annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ \
		convert -f ofn -o $@

####################################
###### Import preparation ##########
####################################

# go has to be relaxed before it can be merged
mirror-go: | $(TMPDIR)
	curl -L $(OBOBASE)/go/go-base.owl --create-dirs -o $(TMPDIR)/go-download.owl --retry 4 --max-time 400 && \
	$(ROBOT) relax -i $(TMPDIR)/go-download.owl convert -o $(TMPDIR)/$@.owl


$(IMPORTDIR)/all_phenotype_terms.txt: mirror/merged.owl
	$(ROBOT) query -f csv -i $< --query ../sparql/all_phenotype_terms.sparql $@
	sed -i 's/[?]//g' $@
	sed -i 's/http:[/][/]purl[.]obolibrary[.]org[/]obo[/]//g' $@
	sed -i 's/_/:/g' $@
	

$(IMPORTDIR)/merged_terms_combined.txt: $(ALL_TERMS_COMBINED) $(IMPORTDIR)/all_phenotype_terms.txt
	if [ $(IMP) = true ]; then cat $^ | grep -v ^# | sort | uniq >  $@; fi

ALL_MIRRORS = $(patsubst %, $(MIRRORDIR)/%.owl, $(IMPORTS))
ifeq ($(strip $(MERGE_MIRRORS)),true)
$(MIRRORDIR)/merged.owl: $(ALL_MIRRORS)
	$(ROBOT) merge $(patsubst %, -i %, $(ALL_MIRRORS)) \
		upheno:extract-upheno-relations \
			--root-phenotype UPHENO:0001001 \
			--root-phenotype MP:0000001 \
			--root-phenotype HP:0000118 \
			--root-phenotype WBPhenotype:0000886 \
			--root-phenotype XPO:00000000 \
			--root-phenotype XPO:0000000 \
			--root-phenotype PLANP:00000000 \
			--root-phenotype ZP:0000000 \
			--root-phenotype FBcv:0001347 \
			--root-phenotype FYPO:0000001 \
			--root-phenotype DDPHENO:0010000 \
			--root-phenotype PHIPO:0000505 \
			--root-phenotype MGPO:0001001 \
			--root-phenotype APO:0000017 \
			--relation UPHENO:0000003 --relation UPHENO:0000001 \
		remove --axioms disjoint --preserve-structure false remove --term http://www.w3.org/2002/07/owl#Nothing --axioms logical --preserve-structure false \
		remove --term RO:0000052 --term RO:0002314 --axioms tbox --preserve-structure false \
		remove --axioms equivalent --preserve-structure false \
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

download_patterns:
	python3 ../scripts/upheno_build.py download-patterns \
		--upheno-config ../curation/upheno-config.yaml \
		--pattern-directory ../curation/patterns-for-matching

preprocess_dosdp_patterns:
	python3 ../scripts/upheno_build.py preprocess-dosdp-patterns \
		--patterns-directory ../curation/patterns-for-matching/ \
		--processed-patterns-directory ../curation/changed-patterns/

update_dosdp_patterns_for_generation:
	rm -rf ../patterns/dosdp-patterns/*.yaml
	cp ../curation/changed-patterns/*.yaml ../patterns/dosdp-patterns/
	cp ../patterns/dosdp-patterns-curated/*.yaml ../patterns/dosdp-patterns/

full_patterns_pipeline:
	#$(MAKE) download_patterns -B
	$(MAKE) preprocess_dosdp_patterns -B
	$(MAKE) update_dosdp_patterns_for_generation -B

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

#################################
## Patterns managed on GDocs ####
#################################

abnormalCellularComponent=https://docs.google.com/spreadsheets/d/e/2PACX-1vRx0gi2I-Ks14LGNibiy6YzW-3A45_jZOnYsBNmaIjF3M8vrXboJwBYle525RXVscXhGGlOzGe05VhX/pub?gid=1218954488&single=true&output=tsv

$(PATTERNDIR)/data/automatic/abnormalCellularComponent.tsv:
	wget "$(abnormalCellularComponent)" -O $@

prepare_release:
	@echo "WARNING WARNING WARNING: DO NOT USE THIS COMMAND, use sh prepare_release.sh instead!"

.PHONY: prepare_release_customised
prepare_release_customised: all_odk
	rsync -R $(RELEASE_ASSETS) $(RELEASEDIR) &&\
	mkdir -p $(RELEASEDIR)/patterns && cp -rf $(PATTERN_RELEASE_FILES) $(RELEASEDIR)/patterns &&\
	rm -f $(CLEANFILES) &&\
	echo "Release files are now in $(RELEASEDIR) - now you should commit, push and make a release \
        on your git hosting site such as GitHub or GitLab"

.PHONY: prepare_release_fast
prepare_release_fast:
	$(MAKE) prepare_release_customised IMP=false PAT=false MIR=false COMP=false
