#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 8 14:24:37 2018

@author: Nicolas Matentzoglu
"""

import os
import sys

import pandas as pd
import yaml

from create_sssom import create_upheno_sssom
from lib import (
    cdir,
    dosdp_extract_pattern_seed,
    dosdp_generate,
    dosdp_generate_all,
    get_taxon_restriction_table,
    remove_all_sources_of_unsatisfiability,
    robot_children_list,
    robot_extract_module,
    robot_extract_seed,
    export_merged_tsvs_for_combination,
    augment_upheno_relationships,
    robot_merge,
    create_upheno_core_manual_phenotypes,
    extract_upheno_fillers_for_all_ontologies,
    add_upheno_ids_to_fillers_and_filter_out_bfo,
    replace_owl_thing_in_tsvs,
    robot_prepare_ontology_for_dosdp,
    robot_query,
    robot_remove_terms,
    robot_upheno_release,
    uPhenoConfig,
    get_highest_id,
    write_list_to_file,
    get_all_patterns_as_yml,
    update_abnormal_patterns_to_changed,
    write_patterns_to_file,
)

# Configuration
yaml.warnings({"YAMLLoadWarning": False})
upheno_config_file = sys.argv[1]
# upheno_config_file = os.path.join("/ws/upheno-dev/src/curation/upheno-config.yaml")
upheno_config = uPhenoConfig(config_file=upheno_config_file)
os.environ["ROBOT_JAVA_ARGS"] = upheno_config.get_robot_java_args()

timeout = upheno_config.get_external_timeout()
ws = upheno_config.get_working_directory()
robot_opts = upheno_config.get_robot_opts()
maxid = upheno_config.get_max_upheno_id()
minid = upheno_config.get_min_upheno_id()
startid = minid
blacklisted_upheno_ids = []
overwrite_dosdp_upheno = upheno_config.is_overwrite_upheno_intermediate()

# globals
upheno_prefix = "http://purl.obolibrary.org/obo/UPHENO_"

# Data directories
# upheno_filler_data_file = os.path.join(ws,"curation/upheno_fillers.yml")
# upheno_filler_ontologies_list = os.path.join(ws,"curation/ontologies.txt")
# phenotype_ontologies_list = os.path.join(ws,"curation/phenotype_ontologies.tsv")
pattern_dir = os.path.join(ws, "curation/patterns-for-matching/")
matches_dir = os.path.join(ws, "curation/pattern-matches/")
upheno_fillers_dir = os.path.join(ws, "curation/upheno-fillers/")
upheno_profiles_dir = os.path.join(ws, "curation/upheno-profiles/")
raw_ontologies_dir = os.path.join(ws, "curation/tmp/")
upheno_prepare_dir = os.path.join(ws, "curation/upheno-release-prepare/")
upheno_release_dir = os.path.join(ws, "curation/upheno-release/")
ontology_for_matching_dir = os.path.join(ws, "curation/ontologies-for-matching/")
upheno_patterns_data_manual_dir = os.path.join(ws, "patterns/data/default/")
upheno_patterns_dir = os.path.join(ws, "curation/changed-patterns/")
upheno_patterns_main_dir = os.path.join(ws, "patterns/dosdp-patterns/")
upheno_ontology_dir = os.path.join(ws, "ontology/")

cdir(pattern_dir)
cdir(matches_dir)
cdir(upheno_fillers_dir)
cdir(raw_ontologies_dir)
cdir(upheno_prepare_dir)
cdir(ontology_for_matching_dir)

# Files
upheno_id_map = os.path.join(ws, "curation/upheno_id_map.txt")
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
legal_iri_patterns_path = os.path.join(raw_ontologies_dir, "legal_fillers.txt")
legal_pattern_vars_path = os.path.join(raw_ontologies_dir, "legal_pattern_vars.txt")
blacklisted_upheno_ids_path = os.path.join(raw_ontologies_dir, "blacklisted_upheno_iris.txt")

write_list_to_file(file_path=legal_iri_patterns_path, filelist=upheno_config.get_legal_fillers())
write_list_to_file(
    file_path=legal_pattern_vars_path, filelist=upheno_config.get_instantiate_superclasses_pattern_vars()
)
write_list_to_file(file_path=blacklisted_upheno_ids_path, filelist=upheno_config.get_blacklisted_upheno_ids())

java_opts = upheno_config.get_robot_java_args()

replacements = {
    "Abnormal change": "UHAUIYHIUHIUH",
    "abnormal bending": "bending",
    "Any abnormality ": "Any change ",
    "Abnormal(ly) arrested (of)": "Arrested",
    "abnormal closing": "closing",
    "abnormal coiling": "coiling",
    "abnormal decreased": "decreased",
    "abnormal increased": "increased",
    "abnormal duplication": "duplication",
    "abnormal fusion": "fusion",
    "abnormal incomplete": "incomplete",
    "abnormal opening": "opening",
    "thickness abnormality": "thickness phenotype",
    "body abnormally": "body",
    "Abnormal ability": "Ability",
    "A deviation from the normal": "Changed",
    "A morphological abnormality": "Changed morphology",
    "Abnormal accumulation": "Accumulation",
    "Abnormal dilation": "Dilation",
    "Abnormal local accumulation": "Local accumulation",
    "An abnormality": "A change",
    "Abnormality of ": "Changed ",
    "Abnormal morphological asymmetry": "Morphological asymmetry",
    "Abnormal proliferation": "proliferation",
    "Abnormal prominence": "prominence",
    "abnormal decrease": "decrease",
    "An abnormal development": "Changed development",
    "An abnormal reduction": "A reduction",
    "An abnormal ": "A changed ",
    "functional abnormality of": "functional change of",
    "An abnormality ": "A change ",
    "abnormality of": "changed",
    "an abnormal ": "a changed ",
    "abnormally curled": "curling",
    "abnormal ": "changed ",
    "Abnormal ": "Changed ",
    "An abnormally": "",
    "abnormally ": "",
    "Abnormally ": "",
    "UHAUIYHIUHIUH": "Phenotypic change"
}

all_configs_main = get_all_patterns_as_yml(upheno_patterns_main_dir)
all_configs_upheno = get_all_patterns_as_yml(pattern_dir)
all_configs_main.extend(all_configs_upheno)
updated_patterns, changes = update_abnormal_patterns_to_changed(all_configs_main, replacements)
write_patterns_to_file(updated_patterns, upheno_patterns_dir)

# Run

print("Preparing a dictionary for DOSDP extraction from the all imports merged ontology.")
# Used to loop up labels in the pattern generation process, so maybe I don't need anything other than rdfs:label?
if upheno_config.is_overwrite_ontologies() or not os.path.exists(allimports_dosdp):
    robot_prepare_ontology_for_dosdp(
        allimports_merged, allimports_dosdp, sparql_terms, timeout=timeout, robot_opts=robot_opts
    )

print(
    "Loading the existing ID map, the blacklist for uPheno IDs and determining next available uPheno ID."
)
upheno_map = pd.read_csv(upheno_config.get_upheno_id_map(), sep="\t")
startid = get_highest_id(upheno_map["defined_class"], upheno_prefix)
if startid < minid:
    startid = minid

print(startid)

# Do not use these Upheno IDs
with open(blacklisted_upheno_ids_path) as f:
    blacklisted_upheno_ids = f.read().splitlines()

# print(blacklisted_upheno_ids)

print(
    "Compute the uPheno fillers for all individual ontologies, including the assignment of the ids. "
    "The actual intermediate layer is produced, by profile, at a later stage."
)
extract_upheno_fillers_for_all_ontologies(oids=upheno_config.get_phenotype_ontologies(),
                                          java_fill=java_fill,
                                          ontology_for_matching_dir=ontology_for_matching_dir,
                                          matches_dir=matches_dir,
                                          pattern_dir=pattern_dir,
                                          upheno_config=upheno_config,
                                          upheno_fillers_dir=upheno_fillers_dir,
                                          java_opts=java_opts,
                                          legal_iri_patterns_path=legal_iri_patterns_path,
                                          legal_pattern_vars_path=legal_pattern_vars_path,
                                          timeout=timeout)

add_upheno_ids_to_fillers_and_filter_out_bfo(pattern_dir=pattern_dir,
                                             upheno_map=upheno_map,
                                             blacklisted_upheno_ids=blacklisted_upheno_ids,
                                             maxid=maxid,
                                             startid=startid,
                                             upheno_config=upheno_config,
                                             upheno_fillers_dir=upheno_fillers_dir,
                                             upheno_prefix=upheno_prefix)
upheno_map = upheno_map.drop_duplicates()
upheno_map.sort_values("defined_class", inplace=True)
upheno_map.to_csv(upheno_id_map, sep="\t", index=False)
# sys.exit("Intermediadte test stop")

print(
    "Rewriting owl:Thing in DOSDP files (should be unnecessary, "
    "review https://github.com/INCATools/dosdp-tools/issues/154)."
)
replace_owl_thing_in_tsvs(pattern_dir, upheno_config=upheno_config, upheno_fillers_dir=upheno_fillers_dir)

# Output the species independent mappings as an SSSOM file.
create_upheno_sssom(upheno_id_map, upheno_patterns_dir, matches_dir, upheno_species_neutral_mappings_tsv,
                    upheno_species_neutral_mappings_owl)

print("Generating uPheno core (part of uPheno common to all profiles).")
# Extra axioms, upheno relations, the manually curated intermediate phenotypes part of the upheno repo
manual_tsv_files = (
    []
)  # the tsv files are generally being kept track of to generate seeds for the profile import modules later
upheno_core_parts = [upheno_extra_axioms_ontology, upheno_relations_ontology]
upheno_core_manual_phenotypes = create_upheno_core_manual_phenotypes(
    manual_tsv_files, allimports_dosdp, timeout=timeout,
    overwrite_dosdp_upheno=overwrite_dosdp_upheno,
    upheno_patterns_dir=upheno_patterns_dir,
    upheno_prepare_dir=upheno_prepare_dir,
    upheno_patterns_data_manual_dir=upheno_patterns_data_manual_dir,
)

upheno_core_parts.extend(upheno_core_manual_phenotypes)
if overwrite_dosdp_upheno or not os.path.exists(upheno_core_ontology):
    robot_merge(upheno_core_parts, upheno_core_ontology, timeout, robot_opts)

print("Generating uPheno profiles..")
# Generate uPheno profiles
for upheno_combination_id in upheno_config.get_upheno_profiles():
    print("Generating profile: " + upheno_combination_id)
    oids = upheno_config.get_upheno_profile_components(upheno_combination_id)
    profile_dir = os.path.join(upheno_profiles_dir, upheno_combination_id)
    cdir(profile_dir)
    final_upheno_combo_dir = os.path.join(upheno_prepare_dir, upheno_combination_id)
    final_upheno_profile_release_dir = os.path.join(upheno_release_dir, upheno_combination_id)
    cdir(final_upheno_combo_dir)
    cdir(final_upheno_profile_release_dir)

    print("Merge all tsvs from the ontologies participating in this profiles together")
    export_merged_tsvs_for_combination(profile_dir, oids,
                                       pattern_dir=pattern_dir,
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
    for pattern in os.listdir(upheno_patterns_dir):
        if pattern.endswith(".yaml"):
            pattern_file = os.path.join(upheno_patterns_dir, pattern)
            tsv_file_name = pattern.replace(".yaml", ".tsv")
            pattern_name = pattern.replace(".yaml", "")
            pattern_names.append(pattern_name)
            tsv_file = os.path.join(profile_dir, tsv_file_name)
            if os.path.exists(tsv_file):
                tsvs.append(tsv_file)
                outfile = os.path.join(final_upheno_combo_dir, pattern.replace(".yaml", ".owl"))
                upheno_intermediate_ontologies.append(outfile)

    first_pattern = os.path.join(final_upheno_combo_dir, pattern_names[0] + ".owl")
    if overwrite_dosdp_upheno or not os.path.exists(first_pattern):
        dosdp_generate_all(pattern_names, profile_dir, final_upheno_combo_dir, upheno_patterns_dir, False, timeout,
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

    print("Profile: Prepare upheno species specific layer")
    if upheno_config.is_overwrite_ontologies() or not os.path.exists(
            upheno_species_components_ontology
    ):
        robot_merge(
            ontology_list=species_components,
            ontology_merged_path=upheno_species_components_ontology,
            timeout=timeout,
            robot_opts=robot_opts,
            ontologyiri="http://upheno.com/upheno_species_components.owl",
        )

    print("#####")
    print("TSVS: " + str(tsvs))
    print("#####")

    print("Profile: Prepare dependency layer (module from all merged dependencies/imports)")
    if overwrite_dosdp_upheno or not os.path.exists(upheno_species_components_dependencies_seed):
        robot_extract_seed(
            upheno_species_components_ontology,
            upheno_species_components_dependencies_seed,
            sparql_terms,
            timeout,
            robot_opts,
        )
    if overwrite_dosdp_upheno or not os.path.exists(
            upheno_species_components_dependencies_pattern_seed
    ):
        dosdp_extract_pattern_seed(tsvs, upheno_species_components_dependencies_pattern_seed)
    if overwrite_dosdp_upheno or not os.path.exists(
            upheno_species_components_dependencies_ontology
    ):
        robot_extract_module(
            allimports_merged,
            upheno_species_components_dependencies_seed,
            upheno_species_components_dependencies_ontology,
            timeout,
            robot_opts,
        )

    print("Profile: Preparing the full profile ontology (Step 1: Merging all associated OWL files)")
    upheno_profile = [upheno_species_components_ontology, upheno_species_components_dependencies_ontology,
                      upheno_layer_ontology]

    if overwrite_dosdp_upheno or not os.path.exists(upheno_profile_prepare_ontology):
        robot_merge(upheno_profile, upheno_profile_prepare_ontology, timeout, robot_opts)
        robot_remove_terms(
            ontology_path=upheno_profile_prepare_ontology,
            remove_list=upheno_config.get_remove_blacklist(),
            ontology_removed_path=upheno_profile_prepare_ontology,
            timeout=timeout,
            robot_opts=robot_opts,
        )
        remove_all_sources_of_unsatisfiability(
            upheno_profile_prepare_ontology,
            upheno_config.get_upheno_axiom_blacklist(),
            timeout,
            robot_opts,
        )
        # TODO: Review this step!

    print(
        "Profile: Preparing the full profile ontology (Step 2: Creating the release file (reasoning, labelling etc))"
    )
    if overwrite_dosdp_upheno or not os.path.exists(upheno_profile_ontology):
        remove_terms = os.path.join(
            final_upheno_combo_dir, "upheno_removed_classes_without_labels.txt"
        )
        robot_query(
            upheno_profile_prepare_ontology,
            remove_terms,
            terms_without_labels_sparql,
            timeout,
            robot_opts,
        )
        robot_upheno_release(
            [upheno_profile_prepare_ontology],
            upheno_profile_ontology,
            upheno_combination_id,
            timeout,
            robot_opts,
            remove_terms,
        )
    # sys.exit("Stopping just after generating first round.")

    print("Profile: Creating uPheno addons - compute extra relations.")
    upheno_ontology_no_taxon_restictions = os.path.join(
        raw_ontologies_dir, "upheno_ontology_no_taxon_restictions.owl"
    )
    upheno_phenotype_list = os.path.join(final_upheno_combo_dir, "upheno_phenotype_list.txt")
    upheno_has_phenotypic_orthologue = os.path.join(
        final_upheno_combo_dir, "upheno_has_phenotypic_orthologue.owl"
    )
    upheno_has_phenotype_affecting = os.path.join(
        final_upheno_combo_dir, "upheno_has_phenotype_affecting.owl"
    )

    if overwrite_dosdp_upheno or not os.path.exists(upheno_phenotype_list):
        robot_children_list(
            upheno_profile_ontology, phenotype_classes_sparql, upheno_phenotype_list
        )
    if overwrite_dosdp_upheno or not os.path.exists(upheno_has_phenotypic_orthologue):
        augment_upheno_relationships(
            upheno_ontology_no_taxon_restictions,
            final_upheno_combo_dir,
            upheno_phenotype_list,
            java_opts=java_opts,
            java_relationships=java_relationships,
            timeout=timeout
        )

    print(
        "Profile: Creating uPheno addons - merge extra relations into augmented upheno release file."
    )
    if overwrite_dosdp_upheno or not os.path.exists(upheno_profile_ontology_with_relations):
        robot_upheno_release(
            [
                upheno_profile_ontology,
                upheno_has_phenotypic_orthologue,
                upheno_has_phenotype_affecting,
            ],
            upheno_profile_ontology_with_relations,
            upheno_combination_id,
            timeout,
            robot_opts,
        )
