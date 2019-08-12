import yaml
import os
from subprocess import check_call

class uPhenoConfig:
    def __init__(self, config_file):
        self.config = yaml.load(open(config_file, 'r'))

    def get_download_location(self, id):
        return [t['mirror_from'] for t in self.config.get("sources") if t['id'] == id][0]

    def get_source_ids(self):
        return [t['id'] for t in self.config.get("sources")]

    def get_anatomy_dependency(self, id):
        return [t['anatomy'] for t in self.config.get("sources") if t['id'] == id][0]

    def get_file_location(self, id):
        return [t['file_path'] for t in self.config.get("sources") if t['id'] == id][0]

    def get_phenotype_ontologies(self):
        return self.config.get("species_modules")

    def get_dependencies(self, id):
        dependencies = []
        dependencies.extend(self.config.get("common_dependencies"))
        try:
            odeps = [t['dependencies'] for t in self.config.get("sources") if t['id'] == id][0]
            dependencies.extend(odeps)
        except:
            print("No dependencies for "+id)

        return dependencies

    def get_taxon_label(self, id):
        return [t['taxon_label'] for t in self.config.get("sources") if t['id'] == id][0]

    def get_taxon(self, id):
        return [t['taxon'] for t in self.config.get("sources") if t['id'] == id][0]

    def get_root_phenotype(self, id):
        return [t['root'] for t in self.config.get("sources") if t['id'] == id][0]

    def get_xref_alignments(self, id):
        alignments = []
        try:
            odeps = [t['xref_alignments'] for t in self.config.get("sources") if t['id'] == id][0]
            alignments.extend(odeps)
        except:
            print("No xref alignments for "+id)

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

    def is_allow_non_upheno_eq(self):
        return self.config.get("allow_non_upheno_eq")

    def get_external_timeout(self):
        return str(self.config.get("timeout_external_processes"))

    def get_pattern_repos(self):
        return self.config.get("pattern_repos")

    def get_working_directory(self):
        return self.config.get("working_directory")

    def get_robot_opts(self):
        return self.config.get("robot_opts")

    def get_legal_fillers(self):
        return self.config.get("legal_fillers")

    def get_instantiate_superclasses_pattern_vars(self):
        return self.config.get("instantiate_superclasses_pattern_vars")

    def get_robot_java_args(self):
        return self.config.get("robot_java_args")

    def set_path_for_ontology(self, id, path):
        for t in self.config.get("sources"):
            if t['id'] == id:
                t['file_path'] = path


def cdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# ROBOT wrappers
def robot_extract_seed(ontology_path,seedfile,sparql_terms, TIMEOUT="60m", robot_opts="-v"):
    print("Extracting seed of "+ontology_path+" with "+sparql_terms)
    try:
        check_call(['timeout','-t',TIMEOUT,'robot', 'query',robot_opts,'--use-graphs','true','-f','csv','-i', ontology_path,'--query', sparql_terms, seedfile])
    except Exception as e:
        print(e.output)
        raise Exception("Seed extraction of" + ontology_path + " failed")

def robot_extract_module(ontology_path,seedfile, ontology_merged_path, TIMEOUT="60m", robot_opts="-v"):
    print("Extracting module of "+ontology_path+" to "+ontology_merged_path)
    try:
        check_call(['timeout','-t',TIMEOUT,'robot', 'extract',robot_opts,'-i', ontology_path,'-T', seedfile,'--method','BOT', '--output', ontology_merged_path])
    except Exception as e:
        print(e.output)
        raise Exception("Module extraction of " + ontology_path + " failed")

def robot_dump_disjoints(ontology_path,term_file, ontology_removed_path, TIMEOUT="60m", robot_opts="-v"):
    print("Removing disjoint class axioms from "+ontology_path+" and saving to "+ontology_removed_path)
    try:
        check_call(['timeout','-t',TIMEOUT,'robot', 'remove',robot_opts,'-i', ontology_path,'--term-file',term_file,'--axioms','disjoint', '--output', ontology_removed_path])
    except Exception as e:
        print(e.output)
        raise Exception("Removing disjoint class axioms from " + ontology_path + " failed")

def robot_remove_mentions_of_nothing(ontology_path, ontology_removed_path, TIMEOUT="60m", robot_opts="-v"):
    print("Removing mentions of nothing from "+ontology_path+" and saving to "+ontology_removed_path)
    try:
        check_call(['timeout','-t',TIMEOUT,'robot', 'remove',robot_opts,'-i', ontology_path,'--term','http://www.w3.org/2002/07/owl#Nothing', '--axioms','logical','--preserve-structure', 'false', '--output', ontology_removed_path])
    except Exception as e:
        print(e.output)
        raise Exception("Removing mentions of nothing from " + ontology_path + " failed")

def robot_merge(ontology_list, ontology_merged_path, TIMEOUT="60m", robot_opts="-v"):
    print("Merging " + str(ontology_list) + " to " + ontology_merged_path)
    try:
        callstring = ['timeout','-t', TIMEOUT, 'robot', 'merge', robot_opts]
        merge = " ".join(["--input " + s for s in ontology_list]).split(" ")
        callstring.extend(merge)
        callstring.extend(['--output', ontology_merged_path])
        check_call(callstring)
    except Exception as e:
        print(e)
        raise Exception("Merging of" + str(ontology_list) + " failed")


def dosdp_generate(pattern,tsv,outfile, TIMEOUT="60m"):
    try:
        check_call(
            ['timeout','-t', TIMEOUT, 'dosdp-tools', 'generate', '--infile=' + tsv, '--template=' + pattern,
             '--obo-prefixes=true', '--restrict-axioms-to=logical', '--outfile=' + outfile])
    except:
        raise Exception("Pattern generation failed: "+pattern+", "+tsv+", "+outfile+".")


def touch(path):
    with open(path, 'a'):
        os.utime(path, None)

def rm(path):
    if os.path.isfile(path):
        os.remove(path)
    else:  ## Show an error ##
        print("Error: %s file not found" % path)