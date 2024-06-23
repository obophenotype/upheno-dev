#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 8 14:24:37 2018

@author: Nicolas Matentzoglu
"""

import os
import sys

import yaml

from lib import (
    cdir,
    dosdp_generate,
    dosdp_generate_all,
    get_taxon_restriction_table,
    export_merged_tsvs_for_combination,
    robot_merge,
    create_upheno_core_manual_phenotypes,
    robot_prepare_ontology_for_dosdp,
    uPhenoConfig,
    compute_upheno_fillers,
    generate_rewritten_patterns,
)

# Configuration
yaml.warnings({"YAMLLoadWarning": False})
upheno_config_file = sys.argv[1]
upheno_config = uPhenoConfig(config_file=upheno_config_file)
os.environ["ROBOT_JAVA_ARGS"] = upheno_config.get_robot_java_args()

timeout = upheno_config.get_external_timeout()
ws = upheno_config.get_working_directory()
robot_opts = upheno_config.get_robot_opts()

blacklisted_upheno_ids = []
overwrite_dosdp_upheno = upheno_config.is_overwrite_upheno_intermediate()


# Data directories
original_pattern_dir = os.path.join(ws, "curation/patterns-for-matching/")
upheno_preprocessed_patterns_dir = os.path.join(ws, "curation/changed-patterns/")
sspo_matches_dir = os.path.join(ws, "curation/pattern-matches/")

upheno_profiles_dir = os.path.join(ws, "curation/upheno-profiles/")
raw_ontologies_dir = os.path.join(ws, "curation/tmp/")
upheno_prepare_dir = os.path.join(ws, "curation/upheno-release-prepare/")
ontology_for_matching_dir = os.path.join(ws, "curation/ontologies-for-matching/")
upheno_fillers_dir = os.path.join(ws, "curation/upheno-fillers/")

upheno_patterns_data_manual_dir = os.path.join(ws, "patterns/data/default/")
upheno_patterns_main_dir = os.path.join(ws, "patterns/dosdp-patterns/")

upheno_ontology_dir = os.path.join(ws, "ontology/")

cdir(upheno_fillers_dir)
cdir(original_pattern_dir)
cdir(upheno_preprocessed_patterns_dir)
cdir(sspo_matches_dir)
cdir(raw_ontologies_dir)
cdir(upheno_prepare_dir)
cdir(ontology_for_matching_dir)

# Files
java_fill = os.path.join(ws, "scripts/upheno-filler-pipeline.jar")
java_relationships = os.path.join(ws, "scripts/upheno-relationship-augmentation.jar")
sparql_terms = os.path.join(ws, "sparql/terms.sparql")
sparql_uberon_terms = os.path.join(ws, "sparql/uberon_terms.sparql")
phenotype_classes_sparql = os.path.join(ws, "sparql/phenotype_classes.sparql")
terms_without_labels_sparql = os.path.join(ws, "sparql/terms_without_labels.sparql")
phenotype_pattern = os.path.join(ws, "patterns/dosdp-patterns/phenotype.yaml")
phenotype_pattern_taxon = os.path.join(ws, "patterns/dosdp-patterns/phenotype_taxon.yaml")
phenotype_pattern_taxon_modified = os.path.join(
    ws, "patterns/dosdp-patterns/phenotype_taxon_modified.yaml"
)
allimports_merged = os.path.join(raw_ontologies_dir, "upheno-allimports-merged.owl")
allimports_dosdp = os.path.join(raw_ontologies_dir, "upheno-allimports-dosdp.owl")
upheno_components_dir = os.path.join(upheno_ontology_dir, "components/")
upheno_core_ontology = os.path.join(upheno_prepare_dir, "upheno-core.owl")
upheno_extra_axioms_ontology = os.path.join(upheno_components_dir, "upheno-extra.owl")
upheno_relations_ontology = os.path.join(upheno_components_dir, "upheno-relations.owl")
upheno_species_neutral_mappings_tsv = os.path.join(upheno_prepare_dir, "upheno-species-independent.sssom.tsv")
upheno_species_neutral_mappings_owl = os.path.join(upheno_prepare_dir, "upheno-species-independent.sssom.owl")

# generated Files

java_opts = upheno_config.get_robot_java_args()

print("### Generate change patterns ###")
generate_rewritten_patterns(upheno_patterns_main_dir=upheno_patterns_main_dir,
                            pattern_dir=original_pattern_dir,
                            upheno_patterns_dir=upheno_preprocessed_patterns_dir)

print("### Preparing a dictionary for DOSDP extraction from the all imports merged ontology.")
# Used to loop up labels in the pattern generation process, so maybe I don't need anything other than rdfs:label?
if upheno_config.is_overwrite_ontologies() or not os.path.exists(allimports_dosdp):
    robot_prepare_ontology_for_dosdp(
        allimports_merged, allimports_dosdp, sparql_terms, timeout=timeout, robot_opts=robot_opts
    )

print("### Loading the existing ID map, the blacklist for uPheno IDs and determining next available uPheno ID.")
java_fill = os.path.join(ws, "scripts/upheno-filler-pipeline.jar")
compute_upheno_fillers(upheno_config=upheno_config,
                       raw_ontologies_dir=raw_ontologies_dir,
                       upheno_fillers_dir=upheno_fillers_dir,
                       java_fill=java_fill,
                       ontology_for_matching_dir=ontology_for_matching_dir,
                       sspo_matches_dir=sspo_matches_dir,
                       original_pattern_dir=original_pattern_dir)

print("Generating uPheno core (part of uPheno common to all profiles).")
# Extra axioms, upheno relations, the manually curated intermediate phenotypes part of the upheno repo
manual_tsv_files = (
    []
)  # the tsv files are generally being kept track of to generate seeds for the profile import modules later
upheno_core_manual_phenotypes = create_upheno_core_manual_phenotypes(
    manual_tsv_files, allimports_dosdp, timeout=timeout,
    overwrite_dosdp_upheno=overwrite_dosdp_upheno,
    upheno_patterns_dir=upheno_preprocessed_patterns_dir,
    upheno_prepare_dir=upheno_prepare_dir,
    upheno_patterns_data_manual_dir=upheno_patterns_data_manual_dir,
)

upheno_core_parts = [upheno_extra_axioms_ontology, upheno_relations_ontology]
upheno_core_parts.extend(upheno_core_manual_phenotypes)

if overwrite_dosdp_upheno or not os.path.exists(upheno_core_ontology):
    robot_merge(ontology_list=upheno_core_parts,
                ontology_merged_path=upheno_core_ontology,
                timeout=timeout,
                robot_opts=robot_opts)

print("Generating uPheno profiles..")
upheno_combination_id = "all"

print("Generating profile: " + upheno_combination_id)
oids = upheno_config.get_upheno_profile_components(upheno_combination_id)
profile_dir = os.path.join(upheno_prepare_dir, upheno_combination_id)
cdir(profile_dir)
final_upheno_combo_dir = os.path.join(upheno_prepare_dir, upheno_combination_id)
final_upheno_profile_release_dir = os.path.join(upheno_prepare_dir, upheno_combination_id)
cdir(final_upheno_combo_dir)
cdir(final_upheno_profile_release_dir)

print("Merge all tsvs from the ontologies participating in this profiles together")
export_merged_tsvs_for_combination(profile_dir, oids,
                                   pattern_dir=original_pattern_dir,
                                   upheno_fillers_dir=upheno_fillers_dir)

print("Create all top level phenotypes relevant to this profile (SSPO top level classes)")
upheno_top_level_phenotypes_ontology = os.path.join(
    final_upheno_combo_dir, "upheno_top_level_phenotypes.owl"
)
upheno_top_level_phenotypes_modified_ontology = os.path.join(
    final_upheno_combo_dir, "upheno_top_level_phenotypes_modified.owl"
)
upheno_top_level_phenotypes_non_modified_ontology = os.path.join(
    final_upheno_combo_dir, "upheno_top_level_phenotypes_non_modified.owl"
)
phenotype_tsv = os.path.join(final_upheno_combo_dir, "upheno_top_level_phenotypes.tsv")
phenotype_modified_tsv = os.path.join(
    final_upheno_combo_dir, "upheno_top_level_phenotypes_modified.tsv"
)
if overwrite_dosdp_upheno or not os.path.exists(upheno_top_level_phenotypes_ontology):
    df_tr = get_taxon_restriction_table(oids, upheno_config)
    df_tr["modifier"] = df_tr["modifier"].astype(str)
    df_tr_no_modifier = df_tr[df_tr["modifier"] == "False"]
    print(str(df_tr_no_modifier[["defined_class", "bearer", "modifier"]]))
    df_tr_modifier = df_tr[df_tr["modifier"] != "False"]
    print(str(df_tr_modifier[["defined_class", "bearer", "modifier"]]))
    df_tr_no_modifier.to_csv(phenotype_tsv, sep="\t", index=False)
    df_tr_modifier.to_csv(phenotype_modified_tsv, sep="\t", index=False)
    dosdp_generate(
        phenotype_pattern_taxon,
        phenotype_tsv,
        upheno_top_level_phenotypes_non_modified_ontology,
        restrict_logical=True,
        timeout=timeout,
        ontology=allimports_dosdp,
    )
    dosdp_generate(
        phenotype_pattern_taxon_modified,
        phenotype_modified_tsv,
        upheno_top_level_phenotypes_modified_ontology,
        restrict_logical=True,
        timeout=timeout,
        ontology=allimports_dosdp,
    )
    robot_merge(
        [
            upheno_top_level_phenotypes_non_modified_ontology,
            upheno_top_level_phenotypes_modified_ontology,
        ],
        upheno_top_level_phenotypes_ontology,
        timeout,
        robot_opts,
    )
# upheno_intermediate_ontologies contains all the files that will be merged together to form the
# intermediate (i.e. uPheno) layer of this profile, including the core, top-level and upheno-class component
upheno_intermediate_ontologies = [upheno_top_level_phenotypes_ontology, upheno_core_ontology]

# These TSVs are purely kept for bookkeeping and to generate the seed in the end for the profile imports module
tsvs = [phenotype_tsv]
tsvs.extend(manual_tsv_files)

# For all tsvs, generate the dosdp instances and drop them in the combo directory
print("Profile: Generate uPheno intermediate layer")
pattern_names = []
for pattern in os.listdir(upheno_preprocessed_patterns_dir):
    if pattern.endswith(".yaml"):
        pattern_file = os.path.join(upheno_preprocessed_patterns_dir, pattern)
        tsv_file_name = pattern.replace(".yaml", ".tsv")
        pattern_name = pattern.replace(".yaml", "")
        tsv_file = os.path.join(profile_dir, tsv_file_name)
        if os.path.exists(tsv_file):
            tsvs.append(tsv_file)
            pattern_names.append(pattern_name)
            outfile = os.path.join(final_upheno_combo_dir, pattern.replace(".yaml", ".owl"))
            upheno_intermediate_ontologies.append(outfile)

first_pattern = os.path.join(final_upheno_combo_dir, pattern_names[0] + ".owl")
if overwrite_dosdp_upheno or not os.path.exists(first_pattern):
    dosdp_generate_all(pattern_names, profile_dir,
                       final_upheno_combo_dir,
                       upheno_preprocessed_patterns_dir,
                       False,
                       timeout,
                       ontology=allimports_dosdp)

print(
    "Profile: Collect all ontologies (taxon restricted versions) and their dependencies as needed by this profile."
)
species_components = []
for oid in oids:
    fn = oid + ".owl"
    o_base_taxon = os.path.join(raw_ontologies_dir, oid + "-upheno-component.owl")
    o_base_class_hierarchy = os.path.join(raw_ontologies_dir, oid + "-class-hierarchy.owl")
    species_components.append(o_base_taxon)
    species_components.append(o_base_class_hierarchy)

# create merged main
upheno_layer_ontology = os.path.join(final_upheno_combo_dir, "upheno_layer.owl")
upheno_species_components_ontology = os.path.join(
    final_upheno_combo_dir, "upheno_species_components.owl"
)
upheno_species_components_dependencies_ontology = os.path.join(
    final_upheno_combo_dir, "upheno_species_components_dependencies.owl"
)
upheno_species_components_dependencies_seed = os.path.join(
    final_upheno_combo_dir, upheno_combination_id + "_seed.txt"
)
upheno_species_components_dependencies_pattern_seed = os.path.join(
    final_upheno_combo_dir, upheno_combination_id + "_pattern_seed.txt"
)
upheno_profile_prepare_ontology = os.path.join(
    final_upheno_combo_dir, "upheno_pre_" + upheno_combination_id + ".owl"
)
upheno_profile_ontology = os.path.join(
    final_upheno_profile_release_dir, "upheno_" + upheno_combination_id + ".owl"
)
upheno_profile_ontology_with_relations = os.path.join(
    final_upheno_profile_release_dir, "upheno_" + upheno_combination_id + "_with_relations.owl"
)
# print(upheno_intermediate_ontologies)

print("Profile: Create upheno intermediate layer")
if overwrite_dosdp_upheno or not os.path.exists(upheno_layer_ontology):
    robot_merge(upheno_intermediate_ontologies, upheno_layer_ontology, timeout, robot_opts)
