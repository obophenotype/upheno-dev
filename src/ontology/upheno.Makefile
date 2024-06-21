
TMPDIR=../curation/tmp

#ttl: ../curation/upheno-release/all/upheno_all_with_relations.ttl
upheno_mapping_lexical_all: ../curation/upheno-release/all/upheno_species_lexical.csv ../curation/upheno-release/all/upheno_mapping_logical.csv
	python3 ../scripts/lexical_mapping.py all
	#echo "SKIP upheno_mapping_lexical_"

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


ml: ../curation/upheno-release/all/upheno_xrefs.csv ../curation/upheno-release/all/upheno_parentage.csv ../curation/upheno-release/all/upheno_associated_entities.csv ../curation/upheno-release/all/upheno_lexical_data.csv

## Reports:
UPHENO_RELEASE_FILE_ANALYSIS=../curation/upheno-release/all/upheno_all_with_relations.owl

reports: reports/phenotype_trait.sssom.tsv

reports/phenotype_trait.sssom.tsv: $(UPHENO_RELEASE_FILE_ANALYSIS)
	robot query -i $< --query ../sparql/pheno_trait.sparql $@
	sed -i 's/[?]//g' $@
	sed -i 's/<http:[/][/]purl[.]obolibrary[.]org[/]obo[/]/obo:/g' $@
	sed -i 's/>//g' $@

###### uPheno pipeline

upheno:
	####### Step 1: download sources and match patterns ########
	$(MAKE) ../curation/pattern-matches/README.md

	####### Step 2: uPheno intermediate layer and species-profiles ########
	$(MAKE) ../curation/upheno-release/all/upheno_all_with_relations.owl

	####### Step 3: uPheno mappings ########
	$(MAKE) ../mappings/upheno-species-independent.sssom.tsv

	####### Step 4: uPheno stats ########
	$(MAKE) ../curation/upheno-stats/pheno_eq_analysis.csv

	####### Step 5: uPheno similarity experiments ########
	$(MAKE) o reports
	@echo "Release successfully completed, ready to deploy."


../curation/pattern-matches/README.md: ../curation/upheno-config.yaml
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



../curation/upheno-release/all/upheno_all_with_relations.owl: ../curation/upheno-config.yaml
	# 1. Extract uPheno fillers from pattern matches (step 1.4). The primary bearer is filled up, 
	#    i.e. every class between the pattern filler and a particular species specific filler class is instantiated
	#    (minus a blacklist)
	# 2. For every profile (config 'upheno_combinations'), create a new directory, then compile all patterns 
	#    from the previous step using dosdp. Add taxon restrictions 
	python ../scripts/upheno_create_profiles.py ../curation/upheno-config.yaml

../curation/upheno-stats/pheno_eq_analysis.csv:
	python ../scripts/upheno-stats.py ../curation/upheno-config.yaml

../mappings/upheno-species-independent.sssom.tsv:
	python3 ../scripts/upheno_build.py upheno create_species_independent_sssom_mappings --upheno_id_map ../curation/upheno_id_map.txt --patterns_dir ../curation/patterns-for-matching --matches_dir ../curation/pattern-matches --output $@

############################
###### Components ###########
############################

$(TEMPLATEDIR)/phenotype-alignments.tsv:
	wget "https://docs.google.com/spreadsheets/d/e/2PACX-1vQOEhF0ffls_ALgYT3eLazW2Cn0PdgEozGK7chOaS6Z3g28abWhmy-sz086Xl0c7A-fndEPAEKxPNjv/pub?gid=1305526284&single=true&output=tsv" -O $@

$(TEMPLATEDIR)/phenotype-alignments.tsv:
	wget "https://docs.google.com/spreadsheets/d/e/2PACX-1vQOEhF0ffls_ALgYT3eLazW2Cn0PdgEozGK7chOaS6Z3g28abWhmy-sz086Xl0c7A-fndEPAEKxPNjv/pub?gid=1901003626&single=true&output=tsv" -O $@

$(COMPONENTSDIR)/upheno-species-neutral.owl:
	$(ROBOT) merge -i ../curation/upheno-release/all/upheno_all_with_relations.owl \
		annotate --ontology-iri $(ONTBASE)/$@ --version-iri $(ONTBASE)/releases/$(TODAY)/$@ -o $@
