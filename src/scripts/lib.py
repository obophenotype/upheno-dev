import glob
import logging
import os
import re
import urllib.request
from subprocess import check_call

import pandas as pd
import ruamel.yaml
import yaml
from sssom.context import get_converter
from sssom.parsers import from_sssom_dataframe
from sssom.writers import write_table, write_owl


class uPhenoConfig:
    def __init__(self, config_file):
        self.config = yaml.safe_load(open(config_file, "r"))

    def get_download_location(self, oid):
        return [t["mirror_from"] for t in self.config.get("sources") if t["id"] == oid][0]

    def get_source_ids(self):
        return [t["id"] for t in self.config.get("sources")]

    def get_anatomy_dependency(self, oid):
        return [t["anatomy"] for t in self.config.get("sources") if t["id"] == oid][0]

    def get_file_location(self, oid):
        return [t["file_path"] for t in self.config.get("sources") if t["id"] == oid][0]

    def get_phenotype_ontologies(self):
        return self.config.get("species_modules")

    def get_upheno_id_map(self):
        return self.config.get("upheno_id_map")

    def get_upheno_intermediate_layer_depth(self):
        return int(self.config.get("upheno_intermediate_layer_depth"))

    def get_remove_disjoints(self):
        return self.config.get("remove_disjoints")

    def get_blacklisted_upheno_ids(self):
        return self.config.get("blacklisted_upheno_iris")

    def get_upheno_axiom_blacklist(self):
        return self.config.get("upheno_axiom_blacklist")

    def get_dependencies(self, oid):
        dependencies = []
        dependencies.extend(self.config.get("common_dependencies"))
        # noinspection PyBroadException
        try:
            odeps = [t["dependencies"] for t in self.config.get("sources") if t["id"] == oid][0]
            dependencies.extend(odeps)
        except Exception:
            print("No dependencies for " + oid)

        return dependencies

    def get_taxon_label(self, oid):
        return [t["taxon_label"] for t in self.config.get("sources") if t["id"] == oid][0]

    def get_taxon(self, oid):
        return [t["taxon"] for t in self.config.get("sources") if t["id"] == oid][0]

    def get_prefix_iri(self, oid):
        return [t["prefix_iri"] for t in self.config.get("sources") if t["id"] == oid][0]

    def get_root_phenotype(self, oid):
        return [t["root"] for t in self.config.get("sources") if t["id"] == oid][0]

    # noinspection PyBroadException
    def get_xref_alignments(self, oid):
        alignments = []
        try:
            odeps = [t["xref_alignments"] for t in self.config.get("sources") if t["id"] == oid][0]
            alignments.extend(odeps)
        except Exception:
            print("No xref alignments for " + oid)

        return alignments

    def is_clean_dir(self):
        return self.config.get("clean")

    def is_overwrite_matches(self):
        return self.config.get("overwrite_matches")

    def is_overwrite_ontologies(self):
        return self.config.get("overwrite_ontologies")

    def is_match_owl_thing(self):
        return self.config.get("match_owl_thing")

    def is_skip_pattern_download(self):
        return self.config.get("skip_pattern_download")

    def is_overwrite_upheno_intermediate(self):
        return self.config.get("overwrite_upheno_intermediate")

    def is_allow_non_upheno_eq(self):
        return self.config.get("allow_non_upheno_eq")

    def is_inferred_class_hierarchy(self, oid):
        return [
            ("class_hierarchy" in t and t["class_hierarchy"] != "asserted")
            for t in self.config.get("sources")
            if t["id"] == oid
        ][0]

    def get_external_timeout(self):
        return str(self.config.get("timeout_external_processes"))

    def get_max_upheno_id(self):
        return int(self.config.get("max_upheno_id"))

    def get_min_upheno_id(self):
        return int(self.config.get("min_upheno_id"))

    def get_pattern_repos(self):
        return self.config.get("pattern_repos")

    def get_exclude_patterns(self):
        return self.config.get("exclude_patterns")

    def get_working_directory(self):
        return self.config.get("working_directory")

    def get_robot_opts(self):
        return self.config.get("robot_opts")

    def get_java_opts(self):
        return self.config.get("java_opts")

    def get_legal_fillers(self):
        return self.config.get("legal_fillers")

    def get_upheno_profiles(self):
        return [t["id"] for t in self.config.get("upheno_profiles")]

    def get_upheno_profile_components(self, oid):
        return [t["species_modules"] for t in self.config.get("upheno_profiles") if t["id"] == oid][
            0
        ]

    def get_instantiate_superclasses_pattern_vars(self):
        return self.config.get("instantiate_superclasses_pattern_vars")

    def get_robot_java_args(self):
        return self.config.get("robot_java_args")

    def get_taxon_restriction_table(self, ids):
        return [
            [t["root"], t["taxon"], t["taxon_label"], t["modifier"]]
            for t in self.config.get("sources")
            if t["id"] in ids
        ]

    def set_path_for_ontology(self, oid, path):
        for t in self.config.get("sources"):
            if t["id"] == oid:
                t["file_path"] = path


def cdir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def robot_extract_seed(ontology_path, seedfile, sparql_terms, timeout="60m", robot_opts="-v"):
    print("Extracting seed of " + ontology_path + " with " + sparql_terms)
    robot_query(ontology_path, seedfile, sparql_terms, timeout, robot_opts)


def robot_query(ontology_path, query_result, sparql_query, timeout="60m", robot_opts="-v"):
    print("Querying " + ontology_path + " with " + sparql_query)
    try:
        check_call(
            [
                "timeout",
                timeout,
                "robot",
                "query",
                robot_opts,
                "--use-graphs",
                "true",
                "-f",
                "csv",
                "-i",
                ontology_path,
                "--query",
                sparql_query,
                query_result,
            ]
        )
    except Exception as e:
        logging.error("An error occurred: %s", e)
        raise Exception("Querying {} with {} failed".format(ontology_path, sparql_query))


def robot_extract_module(
        ontology_path, seedfile, ontology_merged_path, timeout="60m", robot_opts="-v"
):
    print("Extracting module of " + ontology_path + " to " + ontology_merged_path)
    try:
        check_call(
            [
                "timeout",
                timeout,
                "robot",
                "extract",
                robot_opts,
                "-i",
                ontology_path,
                "-T",
                seedfile,
                "--method",
                "BOT",
                "--output",
                ontology_merged_path,
            ]
        )
    except Exception as e:
        logging.error("An error occurred: %s", e)
        raise Exception("Module extraction of " + ontology_path + " failed")


def robot_dump_disjoints(
        ontology_path, term_file, ontology_removed_path, timeout="60m", robot_opts="-v"
):
    print(
        "Removing disjoint class axioms from "
        + ontology_path
        + " and saving to "
        + ontology_removed_path
    )
    try:
        cmd = ["timeout", timeout, "robot", "remove", robot_opts, "-i", ontology_path]
        if term_file:
            cmd.extend(["--term-file", term_file])
        cmd.extend(["--axioms", "disjoint", "--output", ontology_removed_path])
        check_call(cmd)
    except Exception as e:
        logging.error("An error occurred: %s", e)
        raise Exception("Removing disjoint class axioms from " + ontology_path + " failed")


def robot_remove_terms(
        ontology_path, remove_list, ontology_removed_path, timeout="60m", robot_opts="-v"
):
    print("Removing terms from " + ontology_path + " and saving to " + ontology_removed_path)
    try:
        cmd = ["timeout", timeout, "robot", "remove", robot_opts, "-i", ontology_path]
        terms = []
        patterns = []
        for t in remove_list:
            if t.startswith("<"):
                patterns.append(t)
            elif t.startswith("http"):
                terms.append(t)
        for term in terms:
            cmd.extend(["--term", term])
        for pattern in patterns:
            cmd.extend(["remove", "--select", pattern])
        cmd.extend(["--output", ontology_removed_path])
        print(str(cmd))
        check_call(cmd)
    except Exception as e:
        logging.error("An error occurred: %s", e)
        raise Exception("Removing disjoint class axioms from " + ontology_path + " failed")


def robot_remove_mentions_of_nothing(
        ontology_path, ontology_removed_path, timeout="3600", robot_opts="-v"
):
    print(
        "Removing mentions of nothing from "
        + ontology_path
        + " and saving to "
        + ontology_removed_path
    )
    try:
        check_call(
            [
                "timeout",
                timeout,
                "robot",
                "remove",
                robot_opts,
                "-i",
                ontology_path,
                "--term",
                "http://www.w3.org/2002/07/owl#Nothing",
                "--axioms",
                "logical",
                "--preserve-structure",
                "false",
                "--output",
                ontology_removed_path,
            ]
        )
    except Exception as e:
        logging.error("An error occurred: %s", e)
        raise Exception("Removing mentions of nothing from " + ontology_path + " failed")


def remove_all_sources_of_unsatisfiability(o, blacklist_ontology, timeout, robot_opts):
    robot_dump_disjoints(o, None, o, timeout, robot_opts)
    robot_remove_mentions_of_nothing(o, o, timeout, robot_opts)
    robot_remove_axioms_that_could_cause_unsat(o, o, timeout, robot_opts)
    if os.path.exists(blacklist_ontology):
        robot_remove_upheno_blacklist_and_classify(o, o, blacklist_ontology, timeout, robot_opts)


def robot_remove_axioms_that_could_cause_unsat(
        ontology_path, ontology_removed_path, timeout="3600", robot_opts="-v"
):
    print(
        "Removing axioms that could cause unsat from "
        + ontology_path
        + " and saving to "
        + ontology_removed_path
    )
    try:
        check_call(
            [
                "timeout",
                timeout,
                "robot",
                "remove",
                robot_opts,
                "-i",
                ontology_path,
                "--axioms",
                '"DisjointClasses DisjointUnion DifferentIndividuals NegativeObjectPropertyAssertion NegativeDataPropertyAssertion FunctionalObjectProperty InverseFunctionalObjectProperty ReflexiveObjectProperty IrrefexiveObjectProperty ObjectPropertyDomain ObjectPropertyRange DisjointObjectProperties FunctionalDataProperty DataPropertyDomain DataPropertyRange DisjointDataProperties"',
                "--preserve-structure",
                "false",
                "--output",
                ontology_removed_path,
            ]
        )
    except Exception as e:
        logging.error("An error occurred: %s", e)
        raise Exception("Removing mentions of nothing from " + ontology_path + " failed")


def robot_remove_upheno_blacklist_and_classify(
        ontology_path, ontology_removed_path, blacklist_ontology, timeout="3600", robot_opts="-v"
):
    print(
        "Removing upheno blacklist axioms from "
        + ontology_path
        + " and saving to "
        + ontology_removed_path
    )
    try:
        check_call(
            [
                "timeout",
                timeout,
                "robot",
                "merge",
                robot_opts,
                "-i",
                ontology_path,
                "unmerge",
                "-i",
                blacklist_ontology,
                "reason",
                "--reasoner",
                "ELK",
                "--output",
                ontology_removed_path,
            ]
        )
    except Exception as e:
        logging.error("An error occurred: %s", e)
        raise Exception("Removing mentions of nothing from " + ontology_path + " failed")


def robot_merge(
        ontology_list,
        ontology_merged_path,
        timeout="3600",
        robot_opts="-v",
        ontologyiri="http://ontology.com/someuri.owl",
):
    print("Merging " + str(ontology_list) + " to " + ontology_merged_path)
    try:
        callstring = ["timeout", timeout, "robot", "merge", robot_opts]
        merge = " ".join(["--input " + s for s in ontology_list]).split(" ")
        callstring.extend(merge)
        callstring.extend(["annotate", "--ontology-iri", ontologyiri])
        callstring.extend(["--output", ontology_merged_path])
        check_call(callstring)
    except Exception as e:
        print(e)
        raise Exception("Merging of" + str(ontology_list) + " failed")


def list_files(directory, extension):
    return (f for f in os.listdir(directory) if f.endswith("." + extension))


def dosdp_pattern_match(ontology_path, pattern_string, patterndir, outdir, timeout="3600"):
    print("Matching " + ontology_path + " with patterns in " + patterndir)
    try:
        check_call(
            [
                "timeout",
                timeout,
                "dosdp-tools",
                "query",
                "--ontology=" + ontology_path,
                "--reasoner=elk",
                "--obo-prefixes=true",
                "--batch-patterns=" + pattern_string,
                "--template=" + patterndir,
                "--outfile=" + outdir,
            ]
        )
        print("Renaming the rq files generated by DOSDP tools to tsv..")
        for filename in os.listdir(outdir):
            infilename = os.path.join(outdir, filename)
            if not os.path.isfile(infilename):
                continue
            newname = infilename.replace(".rq", ".tsv")
            os.rename(infilename, newname)
    except Exception as e:
        print(e)
        raise Exception(
            "Matching "
            + str(ontology_path)
            + " for DOSDP patterns failed: "
            + pattern_string
            + " failed"
        )


def robot_prepare_ontology_for_dosdp(
        o, ontology_merged_path, sparql_terms_class_hierarchy, timeout="3600", robot_opts="-v"
):
    """
    :param o: Input ontology
    :param ontology_merged_path: Output Ontology
    :param sparql_terms_class_hierarchy: SPARQL query that extracts seed
    :param timeout: Java timeout parameter. String. Using timeout command line program.
    :param robot_opts: Additional ROBOT options
    :return: Take o, extracts a seed using sparql_terms_class_hierarchy,
    extracts class hierarchy, merges both to ontology_merged_path.
    """
    print("Preparing " + str(o) + " for DOSDP: " + ontology_merged_path)
    subclass_hierarchy = os.path.join(
        os.path.dirname(ontology_merged_path),
        "class_hierarchy_" + os.path.basename(ontology_merged_path),
    )
    subclass_hierarchy_seed = os.path.join(
        os.path.dirname(ontology_merged_path),
        "class_hierarchy_seed_" + os.path.basename(ontology_merged_path),
    )
    robot_extract_seed(
        o, subclass_hierarchy_seed, sparql_terms_class_hierarchy, timeout, robot_opts
    )
    robot_class_hierarchy(
        ontology_in_path=o,
        class_hierarchy_seed=subclass_hierarchy_seed,
        ontology_out_path=subclass_hierarchy,
        reason=True,
        remove_disjoint=False,
        timeout=timeout,
        robot_opts=robot_opts,
    )
    try:
        callstring = [
            "timeout",
            timeout,
            "robot",
            "merge",
            robot_opts,
            "-i",
            o,
            "-i",
            subclass_hierarchy,
        ]
        callstring.extend(
            [
                "remove",
                "--term",
                "rdfs:label",
                "--select",
                "complement",
                "--select",
                "annotation-properties",
                "--preserve-structure",
                "false",
            ]
        )
        callstring.extend(["--output", ontology_merged_path])
        check_call(callstring)
    except Exception as e:
        print(e)
        raise Exception("Preparing " + str(o) + " for DOSDP: " + ontology_merged_path + " failed")


def robot_upheno_release(
        ontology_list, ontology_merged_path, name, timeout="3600", robot_opts="-v", remove_terms=None
):
    print("Finalising  " + str(ontology_list) + " to " + ontology_merged_path + ", " + name)
    try:
        callstring = ["timeout", timeout, "robot", "merge", robot_opts]
        merge = " ".join(["--input " + s for s in ontology_list]).split(" ")
        callstring.extend(merge)
        callstring.extend(["remove", "--axioms", "disjoint", "--preserve-structure", "false"])
        callstring.extend(
            [
                "remove",
                "--term",
                "http://www.w3.org/2002/07/owl#Nothing",
                "--axioms",
                "logical",
                "--preserve-structure",
                "false",
            ]
        )
        if remove_terms:
            callstring.extend(["remove", "-T", remove_terms, "--preserve-structure", "false"])
        callstring.extend(["materialize", "--reasoner", "ELK", "--term", "BFO:0000051"])
        callstring.extend(["reason", "--reasoner", "ELK", "reduce", "--reasoner", "ELK"])
        callstring.extend(["--output", ontology_merged_path])
        check_call(callstring)
    except Exception as e:
        print(e)
        raise Exception("Finalising " + str(ontology_list) + " failed...")


def robot_upheno_component(component_file, remove_eqs, timeout="3600"):
    # robot remove --axioms "disjoint" --preserve-structure false reason
    # --reasoner ELK -o /data/upheno_pre-fixed_mp-hp.owl
    print("Preparing uPheno component  " + str(component_file))
    try:
        callstring = ["timeout", timeout, "robot", "merge", "-i", component_file]
        callstring.extend(
            ["remove", "-T", remove_eqs, "--axioms", "equivalent", "--preserve-structure", "false"]
        )
        callstring.extend(["--output", component_file])
        check_call(callstring)
    except Exception as e:
        print(e)
        raise Exception("Preparing uPheno component " + str(component_file) + " failed...")


def robot_children_list(o, query, outfile, timeout="3600", robot_opts="-v"):
    print("Extracting children from  " + str(o) + " using " + str(query))
    try:
        check_call(
            [
                "timeout",
                timeout,
                "robot",
                "query",
                robot_opts,
                "--use-graphs",
                "true",
                "-f",
                "csv",
                "-i",
                o,
                "--query",
                query,
                outfile,
            ]
        )

    except Exception as e:
        print(e)
        raise Exception("Preparing uPheno component " + str(o) + " failed...")


def get_defined_phenotypes(upheno_config, pattern_dir, matches_dir: str):
    defined = []
    for pattern in os.listdir(pattern_dir):
        if pattern.endswith(".yaml"):
            tsv_file_name = pattern.replace(".yaml", ".tsv")
            for oid in upheno_config.get_phenotype_ontologies():
                tsv = os.path.join(matches_dir, oid, tsv_file_name)
                if os.path.exists(tsv):
                    df = pd.read_csv(tsv, sep="\t")
                    defined.extend(df["defined_class"].tolist())
    return list(set(defined))


def robot_class_hierarchy(
        ontology_in_path,
        class_hierarchy_seed,
        ontology_out_path,
        reason=True,
        timeout="3600",
        robot_opts="-v",
        remove_disjoint=False,
):
    print(
        "Extracting class hierarchy from "
        + str(ontology_in_path)
        + " to "
        + ontology_out_path
        + "(Reason: "
        + str(reason)
        + ")"
    )
    try:
        callstring = ["timeout", timeout, "robot", "merge", robot_opts, "--input", ontology_in_path]
        if remove_disjoint:
            callstring.extend(["remove", "--axioms", "disjoint", "--preserve-structure", "false"])
            callstring.extend(
                [
                    "remove",
                    "--term",
                    "http://www.w3.org/2002/07/owl#Nothing",
                    "--axioms",
                    "logical",
                    "--preserve-structure",
                    "false",
                ]
            )

        if reason:
            callstring.extend(["reason", "--reasoner", "ELK"])

        callstring.extend(
            [
                "filter",
                "-T",
                class_hierarchy_seed,
                "--axioms",
                "subclass",
                "--preserve-structure",
                "false",
                "--trim",
                "false",
                "--output",
                ontology_out_path,
            ]
        )
        check_call(callstring)
    except Exception as e:
        print(e)
        raise Exception(
            "Extracting class hierarchy from "
            + str(ontology_in_path)
            + " to "
            + ontology_out_path
            + " failed"
        )


def dosdp_generate(pattern, tsv, outfile, restrict_logical=False, timeout="3600", ontology=None):
    try:
        callstring = [
            "timeout",
            timeout,
            "dosdp-tools",
            "generate",
            "--infile=" + tsv,
            "--template=" + pattern,
            "--obo-prefixes=true",
        ]
        if restrict_logical:
            callstring.extend(["--restrict-axioms-to=logical"])
        if ontology is not None:
            callstring.extend(["--ontology=" + ontology])
        callstring.extend(["--outfile=" + outfile])
        check_call(callstring)
    except Exception:
        raise Exception("Pattern generation failed: " + pattern + ", " + tsv + ", " + outfile + ".")


def dosdp_generate_all(pattern_names, data_dir, data_dir_owl, pattern_dir, restrict_logical=False, timeout="3600",
                       ontology=None):
    pattern_names_string = " ".join(pattern_names)

    try:
        callstring = [
            "timeout",
            timeout,
            "dosdp-tools",
            "generate",
            "--infile=" + data_dir,
            "--template=" + pattern_dir,
            "--batch-patterns=" + pattern_names_string,
            "--obo-prefixes=true",
        ]
        if restrict_logical:
            callstring.extend(["--restrict-axioms-to=logical"])
        if ontology is not None:
            callstring.extend(["--ontology=" + ontology])
        callstring.extend(["--outfile=" + data_dir_owl])
        print("Running: " + " ".join(callstring))
        check_call(callstring)
    except Exception:
        raise Exception("Pattern generation failed for: " + pattern_names_string + " in " + data_dir + ".")


def dosdp_extract_pattern_seed(tsv_files, seedfile):
    classes = []
    try:
        for tsv in tsv_files:
            print("TSV:" + tsv)
            df = pd.read_csv(tsv, sep="\t")
            print(tsv + " done")
            classes.extend(df["defined_class"])
        with open(seedfile, "w") as f:
            for item in list(set(classes)):
                f.write("%s\n" % item)
    except Exception as e:
        print(e)
        raise Exception("Extracting seed from all TSV files failed..")


def write_list_to_file(file_path, filelist):
    with open(file_path, "w") as f:
        for item in filelist:
            f.write("%s\n" % item)


def touch(path):
    with open(path, "a"):
        os.utime(path, None)


def rm(path):
    if os.path.isfile(path):
        os.remove(path)
    else:
        print("Error: %s file not found" % path)


def get_pattern_urls(upheno_pattern_repos):
    upheno_patterns = []
    for upheno_pattern_repo in upheno_pattern_repos:
        upheno_patterns.extend(get_upheno_pattern_urls(upheno_pattern_repo))
    return upheno_patterns


def get_id_columns(pattern_file):
    try:
        with open(pattern_file, "r") as stream:
            pattern_json = yaml.safe_load(stream)
            idcolumns = list(pattern_json["vars"].keys())
            return idcolumns
    except Exception as e:
        logging.error(f"Could not get id columns in {pattern_file}: {e}", exc_info=True)
        return None


def create_upheno_sssom(upheno_id_map, patterns_dir, matches_dir, output_file_tsv, output_file_owl):
    all_pattern_matches_map = dict()

    for pattern_match_tsv in glob.glob(matches_dir + "/**/*.tsv"):
        pattern_name = os.path.basename(pattern_match_tsv).split(".")[0]
        df = pd.read_csv(pattern_match_tsv, sep='\t')
        if pattern_name in all_pattern_matches_map:
            all_pattern_matches_map[pattern_name] = pd.concat([all_pattern_matches_map[pattern_name], df])
        else:
            all_pattern_matches_map[pattern_name] = df

    cache_pattern_file_to_idcolumn = dict()

    df = pd.read_csv(upheno_id_map, sep='\t')

    sssom = []

    converter = get_converter()

    for index, row in df.iterrows():
        tokens = row['id'].split('-')
        fillers = tokens[:-1]
        pattern_name = tokens[-1].split('.')[0]
        pattern_file = pattern_name + ".yaml"
        id_columns = cache_pattern_file_to_idcolumn.get(pattern_file)
        if id_columns is None:
            id_columns = get_id_columns(os.path.join(patterns_dir, pattern_file))
            cache_pattern_file_to_idcolumn[pattern_file] = id_columns
        if id_columns is None:
            continue
        # print(tokens)
        # print(pattern_file)
        # print(id_columns)
        # print(fillers)
        tsv_df = all_pattern_matches_map[pattern_name]
        # filtered = tsv[lambda df: filter_row(df, id_columns, fillers) ]

        mask = pd.Series(True, index=tsv_df.index)
        for col, filler in zip(id_columns, fillers):
            mask = mask & (tsv_df[col] == filler)
        subset_df = tsv_df[mask]

        # print(subset_df)

        upheno_id = row['defined_class']

        for index2, row2 in subset_df.iterrows():
            species_specific_id = row2['defined_class']
            sssom.append([
                converter.compress(upheno_id),
                "semapv:crossSpeciesExactMatch",
                converter.compress(species_specific_id),
                "semapv:LogicalMatching"
            ])

    df_out = pd.DataFrame(sssom, columns=['subject_id', 'predicate_id', 'object_id', 'mapping_justification'])

    meta = dict()
    meta['mapping_set_id'] = 'https://data.monarchinitiative.org/mappings/upheno/upheno-species-independent.sssom.tsv'
    msdf = from_sssom_dataframe(df_out, prefix_map=converter, meta=meta)
    msdf.clean_prefix_map()
    write_table(msdf, open(output_file_tsv, "w"))
    write_owl(msdf, open(output_file_owl, "w"))


def filter_row(df, id_columns, fillers):
    n = 0
    while n < len(id_columns):
        column = id_columns[n]
        filler = fillers[n]
        if df[column] != filler:
            return False
    return True


def download_patterns(upheno_pattern_repos, pattern_dir, upheno_config):
    upheno_patterns = get_pattern_urls(upheno_pattern_repos)
    exclude_patterns = upheno_config.get_exclude_patterns()
    filenames = []
    for url in upheno_patterns:
        filename = os.path.basename(url)
        file_path = os.path.join(pattern_dir, filename)
        print("Downloading " + filename + " from " + url + " to " + pattern_dir)
        # we exclude the inheres_in patterns because they are superceded by the modified 
        # inheres_in_part_of patterns
        # 
        if filename in exclude_patterns:
            continue
        if not upheno_config.is_skip_pattern_download():
            # try:
            print(file_path)
            x = urllib.request.urlopen(url).read()
            yamlr = ruamel.yaml.YAML()
            yamlr.preserve_quotes = True

            # Load the YAML data from a string
            y = yamlr.load(x)
            if upheno_config.is_match_owl_thing():
                for v in y["vars"]:
                    vsv = re.sub("'", "", y["vars"][v])
                    y["classes"][vsv] = "owl:Thing"

            yamlr.explicit_start = True
            yamlr.width = 5000

            with open(file_path, "w") as outfile:
                yamlr.dump(y, outfile)

            # generate inheres_in matches for any inheres_in_part_of patterns
            #
            if "RO:0002314" in y["relations"].values():  # inheres in part of
                new_pattern = y.copy()
                new_pattern["relations"] = {}
                for k, v in y["relations"].items():
                    if v == "RO:0002314":
                        new_pattern["relations"][k] = "RO:0000052"
                    else:
                        new_pattern["relations"][k] = v
                new_file_path = os.path.splitext(file_path)[0] + "-modified.yaml"
                with open(new_file_path, "w") as outfile:
                    yamlr.dump(new_pattern, outfile)
                    filenames.append(new_file_path)

        # except Exception as exc:
        # print(exc)

        if os.path.isfile(file_path):
            filenames.append(filename)
    return filenames


def get_files_of_type_from_github_repo_dir(q, extension):
    import requests
    gh = "https://api.github.com/repos/"
    print(q)
    print(extension)
    # contents = urllib.request.urlopen().read()
    url = gh + q
    f = requests.get(url)
    contents = f.text
    raw = yaml.safe_load(contents)
    tsvs = []
    for e in raw:
        tsv = e["name"]
        if tsv.endswith(extension):
            tsvs.append(e["download_url"])
    return tsvs


def get_all_tsv_urls(tsvs_repos):
    tsvs = []

    for repo in tsvs_repos:
        ts = get_files_of_type_from_github_repo_dir(repo, ".tsv")
        tsvs.extend(ts)

    tsvs_set = set(tsvs)
    return tsvs_set


def get_upheno_pattern_urls(upheno_pattern_repo):
    upheno_patterns = get_files_of_type_from_github_repo_dir(upheno_pattern_repo, ".yaml")
    return upheno_patterns


def export_yaml(data, fn):
    with open(fn, "w") as outfile:
        yaml.dump(data, outfile)


def get_all_patterns_as_yml(pattern_directory_path):
    all_configs = []
    for pattern_file_path in glob.glob(pattern_directory_path + '*.yaml'):
        with open(pattern_file_path, 'r') as pattern_file:
            y = yaml.safe_load(pattern_file)
            all_configs.append(y)
    return all_configs


def print_if_changed(original, new):
    if original != new:
        # print(f"{original}: {new}")
        pass


def update_text(original_text, replacements):
    first_capital = original_text[0].isupper()
    new_text = original_text
    for old, new in replacements.items():
        new_text = new_text.replace(old, new)
    new_text = re.sub(r'\s+', ' ', new_text).strip()
    if first_capital:
        new_text = new_text[0].upper() + new_text[1:]
    return new_text


def process_text(slot, pattern, changes, replacements):
    if slot:
        if 'text' in pattern[slot]:
            original_text = pattern[slot]['text']
        else:
            print(f"XXX: {slot} does not have a text field. Skipping.")
            return
    else:
        original_text = pattern['text']
    new_text = update_text(original_text, replacements)
    if original_text != new_text:
        print(f"{original_text}\t{new_text}")
        changes[original_text] = new_text
        if slot:
            pattern[slot]['text'] = new_text
        else:
            pattern['text'] = new_text
    else:
        print(f"{original_text}\tTODO")


def change_pattern(pattern_yaml, replacements, changes):
    pattern_yaml['description'] = ""
    if 'abnormal' in pattern_yaml['classes']:
        pattern_yaml['classes']['abnormal'] = 'PATO:0000460'

    process_text('name', pattern_yaml, changes, replacements)
    updated_name = pattern_yaml['name']['text']
    print(updated_name)
    if updated_name.startswith("changed "):
        phenotype_name = updated_name.replace("changed ", "") + " phenotype"

        if updated_name != phenotype_name:
            print(f"{updated_name}\t{phenotype_name}")
            pattern_yaml['name']['text'] = phenotype_name

    process_text('def', pattern_yaml, changes, replacements)

    if 'annotations' in pattern_yaml:
        for annotation in pattern_yaml['annotations']:
            if annotation['annotationProperty'] == 'exact_synonym':
                process_text(None, annotation, changes, replacements)


def update_abnormal_patterns_to_changed(all_configs, replacements):
    updated_patterns = []
    changes = {}
    for pattern in all_configs:
        change_pattern(pattern, replacements=replacements, changes=changes)
        updated_patterns.append(pattern)
    return updated_patterns, changes


def write_patterns_to_file(updated_patterns, changed_pattern_directory_path):
    for pattern in updated_patterns:
        with open(changed_pattern_directory_path + pattern['pattern_name'] + '.yaml', 'w') as pattern_file:
            yaml.dump(pattern, pattern_file, default_flow_style=False)


def get_taxon_restriction_table(ids, upheno_config):
    d = upheno_config.get_taxon_restriction_table(ids)
    df = pd.DataFrame.from_records(d)
    df.columns = ["defined_class", "taxon", "taxon_label", "modifier"]
    df["bearer"] = "owl:Thing"
    return df


def is_blacklisted(upheno_id, blacklisted_upheno_ids):
    return upheno_id in blacklisted_upheno_ids


def generate_id(i, id_gen, upheno_prefix):
    if isinstance(i, str) and i.startswith(upheno_prefix):
        return i
    return next(id_gen)


def id_generator(startid, maxid, upheno_prefix, blacklisted_upheno_ids):
    current_id = startid
    while current_id <= maxid:
        upheno_id = upheno_prefix + str(current_id).zfill(7)
        if upheno_id not in blacklisted_upheno_ids:
            yield upheno_id
        current_id += 1
    raise ValueError(f"The ID space has been exhausted (maximum {maxid}). Order a new one!")


def add_upheno_id(df, pattern, upheno_map, blacklisted_upheno_ids, startid, maxid, upheno_prefix):
    if "defined_class" in df.columns:
        df = df.drop(["defined_class"], axis=1)
    df = df.drop_duplicates()
    df = df.reindex(sorted(df.columns), axis=1)
    df["pattern"] = pattern
    df["id"] = df.apply(lambda row: "-".join(row.astype(str)), axis=1)
    df = pd.merge(df, upheno_map, on="id", how="left")

    id_gen = id_generator(
        startid=startid,
        maxid=maxid,
        upheno_prefix=upheno_prefix,
        blacklisted_upheno_ids=blacklisted_upheno_ids
    )

    # Update the DataFrame
    df["defined_class"] = [
        generate_id(i=i, id_gen=id_gen, upheno_prefix=upheno_prefix) for i in df["defined_class"]
    ]

    upheno_map = pd.concat([upheno_map, df[["id", "defined_class"]]], ignore_index=True)
    df = df.drop(["pattern", "id"], axis=1)
    df = df.drop_duplicates()
    return df, upheno_map


def extract_upheno_fillers(
        ontology_path, oid_pattern_matches_dir, oid_upheno_fillers_dir, pattern_dir, depth, java_fill,
        timeout, java_opts,
        legal_iri_patterns_path, legal_pattern_vars_path
):
    print("Extracting fillers from " + ontology_path)
    try:
        check_call(
            [
                "timeout",
                timeout,
                "java",
                java_opts,
                "-jar",
                java_fill,
                ontology_path,
                oid_pattern_matches_dir,
                pattern_dir,
                oid_upheno_fillers_dir,
                legal_iri_patterns_path,
                legal_pattern_vars_path,
                str(depth),
            ]
        )
    except Exception:
        logging.exception("Error occured")
        raise Exception("Filler extraction of" + ontology_path + " failed")


def augment_upheno_relationships(ontology_path, out_dir, phenotype_list, timeout, java_opts, java_relationships):
    print("Extracting upheno relationships for " + ontology_path)
    try:
        check_call(
            [
                "timeout",
                timeout,
                "java",
                java_opts,
                "-jar",
                java_relationships,
                ontology_path,
                out_dir,
                phenotype_list,
            ]
        )
    except Exception:
        logging.exception("Error during augment_upheno_relationships")
        raise Exception("Extracting upheno relationships for " + ontology_path + " failed")


def extract_upheno_fillers_for_all_ontologies(oids, ontology_for_matching_dir,
                                              pattern_dir,
                                              matches_dir,
                                              upheno_fillers_dir,
                                              upheno_config,
                                              legal_iri_patterns_path,
                                              legal_pattern_vars_path,
                                              java_opts,
                                              java_fill,
                                              timeout):
    depth = upheno_config.get_upheno_intermediate_layer_depth()
    for oid in oids:
        oid_pattern_matches_dir = os.path.join(matches_dir, oid)
        oid_upheno_fillers_dir = os.path.join(upheno_fillers_dir, oid)
        ontology_file = os.path.join(ontology_for_matching_dir, oid + ".owl")
        extract_upheno_fillers(
            ontology_file, oid_pattern_matches_dir, oid_upheno_fillers_dir, pattern_dir, depth,
            java_fill=java_fill,
            legal_iri_patterns_path=legal_iri_patterns_path,
            legal_pattern_vars_path=legal_pattern_vars_path,
            java_opts=java_opts,
            timeout=timeout
        )


def add_upheno_ids_to_fillers_and_filter_out_bfo(pattern_dir,
                                                 upheno_map,
                                                 blacklisted_upheno_ids,
                                                 upheno_fillers_dir,
                                                 upheno_config,
                                                 upheno_prefix):
    minid = upheno_config.get_min_upheno_id()
    maxid = upheno_config.get_max_upheno_id()

    for pattern in os.listdir(pattern_dir):
        if pattern.endswith(".yaml"):
            tsv_file_name = pattern.replace(".yaml", ".tsv")
            for oid in upheno_config.get_phenotype_ontologies():
                tsv = os.path.join(upheno_fillers_dir, oid, tsv_file_name)
                if os.path.exists(tsv):
                    print(tsv)
                    # noinspection PyTypeChecker
                    df = pd.read_csv(tsv, sep="\t")
                    tsv_name = os.path.basename(tsv)

                    # Update the highest id from the last runs
                    startid = get_highest_id(upheno_map["defined_class"], upheno_prefix)
                    
                    if startid < minid:
                        startid = minid
                    df, upheno_map = add_upheno_id(
                        df=df,
                        pattern=tsv_name.replace(".tsv$", ""),
                        upheno_map=upheno_map,
                        blacklisted_upheno_ids=blacklisted_upheno_ids,
                        startid=startid,
                        maxid=maxid, upheno_prefix=upheno_prefix
                    )
                    # filter out "independent continuant" locations
                    if 'location' in df.columns:
                        df = df[~df["location"].str.startswith("http://purl.obolibrary.org/obo/BFO_")]
                    # noinspection PyTypeChecker
                    df.to_csv(tsv, sep="\t", index=False)

    return upheno_map


def replace_owl_thing_in_tsvs(pattern_dir, upheno_config, upheno_fillers_dir):
    for pattern in os.listdir(pattern_dir):
        if pattern.endswith(".yaml"):
            tsv_file_name = pattern.replace(".yaml", ".tsv")
            for oid in upheno_config.get_phenotype_ontologies():
                tsv = os.path.join(upheno_fillers_dir, oid, tsv_file_name)
                if os.path.exists(tsv):
                    # noinspection PyTypeChecker
                    print("Replace owl:thing in " + tsv)
                    # noinspection PyTypeChecker
                    df = pd.read_csv(tsv, sep="\t")
                    df = df.replace("http://www.w3.org/2002/07/owl#Thing", "owl:Thing")
                    # noinspection PyTypeChecker
                    df.to_csv(tsv, sep="\t", index=False)


def export_merged_tsvs_for_combination(merged_tsv_dir, oids, pattern_dir, upheno_fillers_dir):
    for pattern in os.listdir(pattern_dir):
        tsv_file_name = pattern.replace(".yaml", ".tsv")
        merged_tsv_path = os.path.join(merged_tsv_dir, tsv_file_name)

        merged = []
        for oid in oids:
            tsv_file = os.path.join(upheno_fillers_dir, oid, tsv_file_name)
            if os.path.exists(tsv_file):
                # print(tsv_file)
                # noinspection PyTypeChecker
                otsv = pd.read_csv(tsv_file, sep="\t")
                merged.append(otsv)
        if merged:
            appended_data = pd.concat(merged, axis=0)
            appended_data.drop_duplicates().to_csv(merged_tsv_path, sep="\t", index=False)


def get_highest_id(ids, upheno_prefix):
    x = [i.replace(upheno_prefix, "").lstrip("0") for i in ids]
    x = [s for s in x if s != ""]
    if len(x) == 0:
        x = [
            0,
        ]
    x = [int(i) for i in x]
    return max(x)


def create_upheno_core_manual_phenotypes(manual_tsv_files, allimports_dosdp,
                                         upheno_patterns_data_manual_dir,
                                         timeout,
                                         upheno_prepare_dir,
                                         upheno_patterns_dir,
                                         overwrite_dosdp_upheno):
    ontologies = []
    pattern_names = []
    for pattern_tsv in os.listdir(upheno_patterns_data_manual_dir):
        if pattern_tsv.endswith(".tsv"):
            print(pattern_tsv)
            pattern_tsv_file = os.path.join(upheno_patterns_data_manual_dir, pattern_tsv)
            manual_tsv_files.append(pattern_tsv_file)
            pattern_file_name = pattern_tsv.replace(".tsv", ".yaml")
            pattern_name = pattern_file_name.replace(".yaml", "")
            pattern_names.append(pattern_name)
            pattern_ontology_name = pattern_tsv.replace(".tsv", ".owl")
            ontology_file = os.path.join(upheno_prepare_dir, pattern_ontology_name)
            ontologies.append(ontology_file)

    first_pattern = os.path.join(upheno_patterns_dir, pattern_names[0] + ".owl")
    if overwrite_dosdp_upheno or not os.path.exists(first_pattern):
        dosdp_generate_all(pattern_names,
                           upheno_patterns_data_manual_dir,
                           upheno_patterns_data_manual_dir,
                           upheno_patterns_dir,
                           False,
                           timeout,
                           ontology=allimports_dosdp)

    return ontologies


# This function interprets xref as subclass axioms (A xref B, A subclass B), use sparingly
def robot_xrefs(oid, mapto, mapping_file, timeout, xref_pattern, robot_opts, upheno_config,
                module_dir: str, sparql_dir):
    sparql_xrefs = os.path.join(sparql_dir, "%s_xrefs.sparql" % mapto)
    print(oid)
    print(mapto)
    ontology_path = upheno_config.get_file_location(oid)
    xref_table = os.path.join(module_dir, oid + ".tsv")

    try:
        # Extracting xrefs from ontology to table
        check_call(
            [
                "timeout",
                timeout,
                "robot",
                "query",
                robot_opts,
                "--use-graphs",
                "true",
                "-f",
                "tsv",
                "--input",
                ontology_path,
                "--query",
                sparql_xrefs,
                xref_table,
            ]
        )

        # Doing a bit of preprocessing on the SPARQL result: renaming columns, removing <> signs
        try:
            df = pd.read_csv(xref_table, sep="\t")
            df = df.rename(columns={"?defined_class": "defined_class", "?xref": "xref"})
            df["defined_class"] = df["defined_class"].str.replace("<", "")
            df["defined_class"] = df["defined_class"].str.replace(">", "")
            df["xref"] = df["xref"].str.replace("<", "")
            df["xref"] = df["xref"].str.replace(">", "")
            df.to_csv(xref_table, sep="\t", index=False)
        except pd.errors.EmptyDataError:
            print(xref_table, " is empty and has been skipped.")

        # DOSDP generate the xrefs as subsumptions
        check_call(
            [
                "timeout",
                timeout,
                "dosdp-tools",
                "generate",
                "--infile=" + xref_table,
                "--template=" + xref_pattern,
                "--obo-prefixes=true",
                "--restrict-axioms-to=logical",
                "--outfile=" + mapping_file,
            ]
        )
    except Exception as e:
        logging.exception(f"Error during ROBOT xref.. {e}")
        raise Exception("Xref generation of" + ontology_path + " failed")

    return mapping_file


def robot_convert_merge(ontology_url, ontology_merged_path, timeout, robot_opts):
    print("Convert/Merging " + ontology_url + " to " + ontology_merged_path)
    try:
        check_call(
            [
                "timeout",
                timeout,
                "robot",
                "merge",
                robot_opts,
                "-I",
                ontology_url,
                "convert",
                "--output",
                ontology_merged_path,
            ]
        )
    except Exception as e:
        print(e)
        raise Exception("Loading " + ontology_url + " failed")


def prepare_all_imports_merged(config, module_dir, timeout, robot_opts):
    imports = []
    merged = os.path.join(module_dir, "upheno-allimports-merged.owl")

    for oid in config.get_phenotype_ontologies():
        for dependency in config.get_dependencies(oid):
            imports.append(config.get_file_location(dependency))

    imports = list(set(imports))

    if config.is_overwrite_ontologies() or not os.path.exists(merged):
        robot_merge(imports, merged, timeout, robot_opts)
        remove_all_sources_of_unsatisfiability(
            merged, config.get_upheno_axiom_blacklist(), timeout, robot_opts
        )


def prepare_upheno_ontology_no_taxon_restictions(config, ontology_for_matching_dir, module_dir,
                                                 upheno_config, timeout, robot_opts):
    imports = []
    upheno_ontology_no_taxon_restictions = os.path.join(
        module_dir, "upheno_ontology_no_taxon_restictions.owl"
    )

    for oid in upheno_config.get_phenotype_ontologies():
        imports.append(os.path.join(ontology_for_matching_dir, oid + ".owl"))

    imports = list(set(imports))

    if config.is_overwrite_ontologies() or not os.path.exists(upheno_ontology_no_taxon_restictions):
        robot_merge(imports, upheno_ontology_no_taxon_restictions, timeout, robot_opts)
        remove_all_sources_of_unsatisfiability(
            upheno_ontology_no_taxon_restictions,
            config.get_upheno_axiom_blacklist(),
            timeout,
            robot_opts,
        )


def write_phenotype_sparql(phenotype_root, phenotype_query):
    sparql = ["prefix owl: <http://www.w3.org/2002/07/owl#>",
              "prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>",
              "prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
              "", "SELECT ?s ?lab ?ldef WHERE ",
              "{",
              "?s rdfs:subClassOf* <{}> . ".format(phenotype_root),
              "OPTIONAL { ?s rdfs:label ?lab }",
              "OPTIONAL { ?s owl:equivalentClass [ rdf:type owl:Restriction ;",
              "owl:onProperty <http://purl.obolibrary.org/obo/BFO_0000051> ;", "owl:someValuesFrom ?ldef ] . }", "}"]
    out_file = open(phenotype_query, "w")
    for line in sparql:
        out_file.write(line + "\n")
    out_file.close()


def prepare_phenotype_ontologies_for_matching(overwrite,
                                              upheno_config,
                                              sparql_terms,
                                              ontology_for_matching_dir, stats_dir,
                                              sparql_dir, module_dir, timeout, robot_opts):
    for oid in upheno_config.get_phenotype_ontologies():
        print("Preparing %s" % oid)
        filename = upheno_config.get_file_location(oid)
        imports = []
        for dependency in upheno_config.get_dependencies(oid):
            print("Dependency: " + dependency)
            imports.append(upheno_config.get_file_location(dependency))
        merged = os.path.join(module_dir, oid + "-allimports-merged.owl")
        module = os.path.join(module_dir, oid + "-allimports-module.owl")
        o_base_class_hierarchy = os.path.join(module_dir, oid + "-class-hierarchy.owl")
        class_hierarchy_seed = os.path.join(module_dir, oid + "-class-hierarchy.txt")
        phenotype_class_metadata = os.path.join(stats_dir, oid + "_phenotype_data.csv")
        merged_pheno = os.path.join(ontology_for_matching_dir, oid + ".owl")
        seed = os.path.join(module_dir, oid + "_seed.txt")
        disjoints_term_file = os.path.join(module_dir, "disjoints_removal.txt")
        write_list_to_file(disjoints_term_file, upheno_config.get_remove_disjoints())
        phenotype_query = os.path.join(sparql_dir, oid + "_phenotypes.sparql")
        write_phenotype_sparql(upheno_config.get_root_phenotype(oid), phenotype_query)
        if overwrite or not os.path.exists(module):
            robot_extract_seed(filename, seed, sparql_terms, timeout, robot_opts)
            robot_merge(imports, merged, timeout, robot_opts)
            robot_extract_module(merged, seed, module, timeout, robot_opts)
        if overwrite or not os.path.exists(merged_pheno):
            ontology_for_matching = [module, filename]
            robot_merge(ontology_for_matching, merged_pheno, timeout, robot_opts)
            remove_all_sources_of_unsatisfiability(
                merged_pheno, upheno_config.get_upheno_axiom_blacklist(), timeout, robot_opts
            )
        if overwrite or not os.path.exists(o_base_class_hierarchy):
            sparql_terms_class_hierarchy = os.path.join(sparql_dir, oid + "_terms.sparql")
            robot_extract_seed(
                filename, class_hierarchy_seed, sparql_terms_class_hierarchy, timeout, robot_opts
            )
            robot_class_hierarchy(
                merged_pheno,
                class_hierarchy_seed,
                o_base_class_hierarchy,
                upheno_config.is_inferred_class_hierarchy(oid),
            )
        if overwrite or not os.path.exists(phenotype_class_metadata):
            robot_query(
                merged_pheno, phenotype_class_metadata, phenotype_query, timeout, robot_opts
            )


# noinspection PyTypeChecker
def classes_with_matches(oid, preserve_eq, matches_dir):
    o_matches_dir = os.path.join(matches_dir, oid)
    classes = []
    for file in os.listdir(o_matches_dir):
        if file.endswith(".tsv"):
            tsv = os.path.join(o_matches_dir, file)
            df = pd.read_csv(tsv, sep="\t")
            classes.extend(df["defined_class"])
    write_list_to_file(preserve_eq, list(set(classes)))


def prepare_species_specific_phenotype_ontologies(upheno_config, module_dir, matches_dir,
                                                  timeout,
                                                  java_taxon,
                                                  robot_opts):
    for oid in upheno_config.get_phenotype_ontologies():
        fn = oid + ".owl"
        o_base = os.path.join(module_dir, fn)
        o_base_taxon = os.path.join(module_dir, oid + "-upheno-component.owl")
        preserve_eq = os.path.join(module_dir, "preserve_eq_" + fn)
        if os.path.exists(preserve_eq):
            rm(preserve_eq)

        if not upheno_config.is_allow_non_upheno_eq():
            classes_with_matches(oid, preserve_eq, matches_dir=matches_dir)
        else:
            touch(preserve_eq)

        if upheno_config.is_overwrite_ontologies() or not os.path.exists(o_base_taxon):
            add_taxon_restrictions(
                o_base,
                o_base_taxon,
                upheno_config.get_taxon(oid),
                upheno_config.get_taxon_label(oid),
                upheno_config.get_prefix_iri(oid),
                preserve_eq,
                timeout=timeout,
                java_taxon=java_taxon,
                upheno_config=upheno_config
            )
            remove_eqs_file = os.path.join(module_dir, oid + "-upheno-component_eq_remove.txt")
            remove_eqs = [upheno_config.get_root_phenotype(oid)]
            write_list_to_file(remove_eqs_file, remove_eqs)
            remove_all_sources_of_unsatisfiability(
                o_base_taxon, upheno_config.get_upheno_axiom_blacklist(), timeout, robot_opts
            )
            robot_upheno_component(o_base_taxon, remove_eqs_file)


def postprocess_modified_patterns(upheno_config, pattern_files, matches_dir: str):
    patterns = []
    delete_files = []
    delete_files.extend(pattern_files)

    for pattern_path in pattern_files:
        pid = os.path.basename(pattern_path).replace(".yaml", "")
        patterns.append(pid)

    for oid in upheno_config.get_phenotype_ontologies():
        oid_matches_path = os.path.join(matches_dir, oid)
        for pattern in patterns:
            # Load both the modified and unm modified tsv files
            # merge them and write them back to the unmodified file
            unmodified_tsv_path = os.path.join(oid_matches_path, str(pattern + ".tsv"))
            modified_tsv_path = os.path.join(oid_matches_path, str(pattern + "-modification.tsv"))
            if not os.path.exists(modified_tsv_path):
                continue
            if not os.path.exists(unmodified_tsv_path):
                continue
            df_unmodified = pd.read_csv(unmodified_tsv_path, sep="\t")
            df_modified = pd.read_csv(modified_tsv_path, sep="\t")
            df_combined = pd.concat([df_unmodified, df_modified])
            # Remove duplicate rows
            df_final = df_combined.drop_duplicates()
            df_final.to_csv(unmodified_tsv_path, sep="\t", index=False)
            delete_files.append(modified_tsv_path)

    # Delete the modified tsv files and their corresponding patterns:
    for file_path in delete_files:
        if os.path.exists(file_path):
            os.remove(file_path)


def match_patterns(upheno_config, matches_dir, pattern_dir, ontology_for_matching_dir, timeout,
                   overwrite=True):
    pattern_files = [
        os.path.join(pattern_dir, f)
        for f in os.listdir(pattern_dir)
        if os.path.isfile(os.path.join(pattern_dir, f)) and f.endswith(".yaml")
    ]
    patterns = []
    for pattern_path in pattern_files:
        pid = str(os.path.basename(pattern_path).replace(".yaml", ""))
        patterns.append(pid)
    # pattern_string = " ".join(patterns)
    # pattern_string = pattern_string.strip()
    # Splitting the string in two to avoid Memory Overflow
    length = len(patterns)
    middle_index = length // 2
    first_half = patterns[:middle_index]
    second_half = patterns[middle_index:]
    pattern_string1 = " ".join(first_half)
    pattern_string2 = " ".join(second_half)

    for oid in upheno_config.get_phenotype_ontologies():
        ontology_path = os.path.join(ontology_for_matching_dir, oid + ".owl")
        oid = os.path.basename(ontology_path).replace(".owl", "")
        outdir = os.path.join(matches_dir, oid)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        if overwrite or not os.path.exists(outdir):
            dosdp_pattern_match(ontology_path, pattern_string1, pattern_dir, outdir, timeout)
            dosdp_pattern_match(ontology_path, pattern_string2, pattern_dir, outdir, timeout)
        else:
            print("Matches for ({}) already made, bypassing.".format(outdir))

    modified_patterns_to_process = [
        os.path.join(pattern_dir, f)
        for f in os.listdir(pattern_dir)
        if os.path.isfile(os.path.join(pattern_dir, f)) and f.endswith("-modification.yaml")
    ]

    postprocess_modified_patterns(upheno_config, modified_patterns_to_process, matches_dir)


def add_taxon_restrictions(
        ontology_path, ontology_out_path, taxon_restriction, taxon_label, root_phenotype, preserve_eq, timeout,
        upheno_config,
        java_taxon
):
    print("Extracting fillers from " + ontology_path)
    try:
        check_call(
            [
                "timeout",
                timeout,
                "java",
                upheno_config.get_robot_java_args(),
                "-jar",
                java_taxon,
                ontology_path,
                ontology_out_path,
                taxon_restriction,
                taxon_label,
                root_phenotype,
                preserve_eq,
            ]
        )
    except Exception as e:
        logging.exception(f"Error occurred {e}")
        raise Exception("Appending taxon restrictions" + ontology_path + " failed")


def download_sources(module_dir, upheno_config, xref_pattern, robot_opts, timeout, sparql_dir, overwrite=True):
    for oid in upheno_config.get_source_ids():
        filename = os.path.join(module_dir, oid + ".owl")
        url = upheno_config.get_download_location(oid)
        if url not in ["xref"]:
            if overwrite or not os.path.exists(filename):
                robot_convert_merge(url, filename, robot_opts=robot_opts, timeout=timeout)
            print("%s downloaded successfully." % filename)
            upheno_config.set_path_for_ontology(oid, filename)
    for oid in upheno_config.get_source_ids():
        filename = os.path.join(module_dir, oid + ".owl")
        url = upheno_config.get_download_location(oid)
        if url in ["xref"]:
            if overwrite or not os.path.exists(filename):
                oid = oid.split("-")[0]
                xref = oid.split("-")[1]
                robot_xrefs(oid, xref, filename, timeout, xref_pattern, robot_opts,
                            upheno_config,
                            module_dir,
                            sparql_dir=sparql_dir)
            print("%s compiled successfully through xrefs." % filename)
            upheno_config.set_path_for_ontology(oid, filename)


def get_all_phenotypes(upheno_config, stats_dir: str):
    phenotypes = []
    for oid in upheno_config.get_phenotype_ontologies():
        phenotype_class_metadata = os.path.join(stats_dir, oid + "_phenotype_data.csv")
        if os.path.exists(phenotype_class_metadata):
            df = pd.read_csv(phenotype_class_metadata)
            df["o"] = oid
            phenotypes.append(df)
        else:
            print("{} does not exist!".format(phenotype_class_metadata))
    return pd.concat(phenotypes)


def compute_upheno_stats(upheno_config, pattern_dir, matches_dir, stats_dir):
    defined = get_defined_phenotypes(upheno_config, pattern_dir, matches_dir)
    df_pheno = get_all_phenotypes(upheno_config, stats_dir)
    df_pheno["upheno"] = df_pheno["s"].isin(defined)
    df_pheno["eq"] = df_pheno["ldef"].notna()
    df_pheno.drop_duplicates(inplace=True)

    print("Summary: ")
    print(df_pheno.head())
    print(df_pheno.describe())
    print("")
    print("How many uPheno conformant classes?")
    print(df_pheno[["s", "upheno"]].groupby("upheno").count())
    print("")
    print("How many classes with EQs?")
    print(df_pheno[["s", "eq"]].groupby("eq").count())
    print("")
    print("How many uPheno conformant classes that do not have EQs (bug!!)?")
    print(df_pheno[df_pheno["upheno"] & (~df_pheno["eq"])])
    print(df_pheno[df_pheno["upheno"]][["s", "eq"]].groupby("eq").count())
    df_pheno.to_csv(os.path.join(stats_dir, "upheno-eq-analysis.csv"))


def generate_rewritten_patterns(upheno_patterns_main_dir, pattern_dir, upheno_patterns_dir):
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


def compute_upheno_fillers(
        upheno_config: uPhenoConfig,
        raw_ontologies_dir,
        upheno_fillers_dir,
        original_pattern_dir,
        java_fill,
        ontology_for_matching_dir,
        sspo_matches_dir):
    upheno_prefix = "http://purl.obolibrary.org/obo/UPHENO_"
    upheno_id_map = upheno_config.get_upheno_id_map()
    upheno_map = pd.read_csv(upheno_id_map, sep="\t")
    java_opts = upheno_config.get_robot_java_args()
    timeout = upheno_config.get_external_timeout()

    blacklisted_upheno_ids_path = os.path.join(raw_ontologies_dir, "blacklisted_upheno_iris.txt")
    write_list_to_file(file_path=blacklisted_upheno_ids_path, filelist=upheno_config.get_blacklisted_upheno_ids())

    legal_iri_patterns_path = os.path.join(raw_ontologies_dir, "legal_fillers.txt")
    legal_pattern_vars_path = os.path.join(raw_ontologies_dir, "legal_pattern_vars.txt")

    write_list_to_file(file_path=legal_iri_patterns_path, filelist=upheno_config.get_legal_fillers())
    write_list_to_file(file_path=legal_pattern_vars_path,
                       filelist=upheno_config.get_instantiate_superclasses_pattern_vars())

    # Do not use these Upheno IDs
    with open(blacklisted_upheno_ids_path) as f:
        blacklisted_upheno_ids = f.read().splitlines()

    print(
        "Compute the uPheno fillers for all individual ontologies, including the assignment of the ids. "
        "The actual intermediate layer is produced, by profile, at a later stage."
    )
    extract_upheno_fillers_for_all_ontologies(oids=upheno_config.get_phenotype_ontologies(),
                                              java_fill=java_fill,
                                              ontology_for_matching_dir=ontology_for_matching_dir,
                                              matches_dir=sspo_matches_dir,
                                              pattern_dir=original_pattern_dir,
                                              upheno_config=upheno_config,
                                              upheno_fillers_dir=upheno_fillers_dir,
                                              java_opts=java_opts,
                                              legal_iri_patterns_path=legal_iri_patterns_path,
                                              legal_pattern_vars_path=legal_pattern_vars_path,
                                              timeout=timeout)

    add_upheno_ids_to_fillers_and_filter_out_bfo(pattern_dir=original_pattern_dir,
                                                 upheno_map=upheno_map,
                                                 blacklisted_upheno_ids=blacklisted_upheno_ids,
                                                 upheno_config=upheno_config,
                                                 upheno_fillers_dir=upheno_fillers_dir,
                                                 upheno_prefix=upheno_prefix)
    upheno_map = upheno_map.drop_duplicates()
    upheno_map.sort_values("defined_class", inplace=True)
    upheno_map.to_csv(upheno_id_map, sep="\t", index=False)

    # TODO: Rewriting owl:Thing in DOSDP files (should be unnecessary, "
    # review https://github.com/INCATools/dosdp-tools/issues/154).
    replace_owl_thing_in_tsvs(original_pattern_dir, upheno_config=upheno_config, upheno_fillers_dir=upheno_fillers_dir)
