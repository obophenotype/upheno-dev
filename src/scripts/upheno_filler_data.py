#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 8 14:24:37 2018

@author: Nicolas Matentzoglu
"""

import os, shutil
import yaml
import re
import urllib.request
import pandas as pd
from subprocess import check_call

### Configuration

java_fill = 'upheno-filler-pipeline.jar'
upheno_prefix = 'http://purl.obolibrary.org/obo/UPHENO_'
outdir_patterns = '../patterns/data/auto'
outdir_mappings = '../ontology/mappings'
upheno_id_map = "../curation/upheno_id_map.txt"
upheno_filler_data_file = '../curation/upheno_fillers.yml'
upheno_filler_ontologies_list = '../curation/ontologies.txt'


#class OLS:
#    def __init__(self):
#      self.base = 'https://www.ebi.ac.uk/ols/api/ontologies/'
#
#    def parents(self, ontology, entity):
#        callols = str(self.base + "%s/ancestors?id=%s" % (ontology, entity))
#        print("Call: " + callols)
#
#
#OLS().parents('go','GO:1990722')


# This restricts what namespaces are considered to be acceptable for fillers..
curie_map = dict([("GO:", "http://purl.obolibrary.org/obo/GO_"),
                  ("CL:", "http://purl.obolibrary.org/obo/CL_"),
                  ("BFO:", "http://purl.obolibrary.org/obo/BFO_"),
                  ("MPATH:", "http://purl.obolibrary.org/obo/MPATH_"),
                  ("PATO:", "http://purl.obolibrary.org/obo/PATO_"),
                  ("BSPO:", "http://purl.obolibrary.org/obo/BSPO_"),
                  ("NBO:", "http://purl.obolibrary.org/obo/NBO_"),
                  ("UBERON:", "http://purl.obolibrary.org/obo/UBERON_"),
                  ("CHEBI:", "http://purl.obolibrary.org/obo/CHEBI_")])

# Github repos
upheno_pattern_repo = 'obophenotype/upheno/contents/src/patterns'

tsvs_repos = ["obophenotype/c-elegans-phenotype-ontology/contents/src/patterns/data/manual",
              "obophenotype/xenopus-phenotype-ontology/contents/src/patterns/data/auto",
              "obophenotype/xenopus-phenotype-ontology/contents/src/patterns/data/manual",
              "obophenotype/zebrafish-phenotype-ontology/contents/src/patterns/data/auto",
              "obophenotype/zebrafish-phenotype-ontology/contents/src/patterns/data/manual",
              "obophenotype/planarian-phenotype-ontology/contents/src/patterns/"]

blacklist = ["https://raw.githubusercontent.com/obophenotype/xenopus-phenotype-ontology/master/src/patterns/data/manual/decreasedSize.tsv"]

### Configuration end

### Methods


def get_files_of_type_from_github_repo_dir(q,type):
    gh = "https://api.github.com/repos/"
    print(q)
    contents = urllib.request.urlopen(gh+q).read()
    raw = yaml.load(contents)
    tsvs = []
    for e in raw:
        tsv = e['name']
        if tsv.endswith(type):
            tsvs.append(e['download_url'])
    return tsvs


def curie_to_url_filtered(string, dictionary):
    if isinstance(string,list):
        out = []
        for item in string:
            if ':' in item and '://' not in item:
                # Its a Curie, not a URL
                for k in dictionary.keys():
                    if item.startswith(k):
                        replace = item.replace(k, dictionary[k])
                        out.append(replace)
                        break
            else:
                for k in dictionary.values():
                    if item.startswith(k):
                        out.append(item)
                        break
        return out
    if isinstance(string,str):
        if ':' in string and '://' not in string:
            for k in dictionary.keys():
                if string.startswith(k):
                    return string.replace(k, dictionary[k])
        else:
            for k in dictionary.values():
                if string.startswith(k):
                    return string
    return None


def get_all_tsv_urls(tsvs_repos):
    tsvs = []

    for repo in tsvs_repos:
        ts = get_files_of_type_from_github_repo_dir(repo,'.tsv')
        tsvs.extend(ts)

    tsvs_set = set(tsvs)
    return tsvs_set


def get_upheno_pattern_urls(upheno_pattern_repo):
    upheno_patterns = get_files_of_type_from_github_repo_dir(upheno_pattern_repo,'.yaml')
    return upheno_patterns


def get_upheno_filler_data(upheno_pattern_repo,tsvs_repos,blacklist):
    # Get all url of the uPheno yaml patterns from the uPheno pattern registry (probably the Github repo)
    upheno_patterns = get_upheno_pattern_urls(upheno_pattern_repo)
    # Get the set of urls of all tsv files indexed
    tsvs_set = get_all_tsv_urls(tsvs_repos)
    data = dict()
    # Loop through all the uPheno patterns and (1) open them
    # (2) extract fillers from patterns
    # (3) for all related tsv files, get the respectives values from the columns
    # OUT: big Yaml file with all filler data
    for pattern in upheno_patterns:
        x = urllib.request.urlopen(pattern).read()
        try:
            y = yaml.load(x)

            filename = os.path.basename(pattern)
            print(filename)
            data[filename] = dict()
            data[filename]['keys'] = dict()
            #ct += 1
            #if ct > 6:
                #break
            # Extract fillers from uPheno pattern file
            columns = dict()
            for v in y['vars']:
                vs = re.sub("[^0-9a-zA-Z _]", "", y['vars'][v])
                filler = y['classes'][vs]
                r = curie_to_url_filtered(filler,curie_map)
                if r == None:
                    print("WARNING: "+filler+" not on curie map!")
                columns[vs]=r

            tsvfn = re.sub("[.]yaml$", ".tsv", filename)

            # For all the tsv files that pertain to the pattern we are currently looking at
            # (1) Load it (only the relevant columns)
            # (2) Loop through columns;
            for tsv in tsvs_set:
                if tsv.endswith(tsvfn) and tsv not in blacklist:
                    print(tsv)
                    df = pd.read_csv(tsv, usecols=list(columns.keys()), sep='\t')
                    print(str((df.shape)))
                    for col,filler in columns.items():
                        if col not in data[filename]:
                            data[filename][col] = dict()
                            data[filename][col]['keys'] = []
                            data[filename][col]['filler'] = filler
                        d = curie_to_url_filtered(df[col].tolist(),curie_map)
                        data[filename][col]['keys'].extend(d)
        except yaml.YAMLError as exc:
            print(exc)

    for pattern in data:
        print(pattern)
    return data


def export_yaml(data,fn):
    with open(fn, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)


def upheno_id(i):
    global last_upheno_index
    if(isinstance(i,str)):
        return i
    else:
        last_upheno_index = last_upheno_index + 1
        id = upheno_prefix+str(last_upheno_index).zfill(7)
        return id


def add_upheno_id(df,pattern):
    global upheno_map
    if 'defined_class' in df.columns:
        df = df.drop(['defined_class'], axis=1)
    df['pattern'] = pattern
    df['id'] = df.apply('-'.join, axis=1)
    df = pd.merge(df, upheno_map, on='id', how='left')
    df['defined_class'] = [upheno_id(i) for i in df['defined_class']]
    upheno_map = upheno_map.append(df[['id', 'defined_class']])
    df = df.drop(['pattern', 'id'], axis=1)
    return df


def add_upheno_ids_to_all_tables(outdir_patterns):
    for file in os.listdir(outdir_patterns):
        if file.endswith(".tsv"):
            f = (os.path.join(outdir_patterns, file))
            df = pd.read_csv(f, sep='\t')
            df = add_upheno_id(df,file.replace(".tsv$", ""))
            df.to_csv(f, sep='\t', index=False)



### Methods end

### Run

# Get the fillers from the available tsvs
data = get_upheno_filler_data(upheno_pattern_repo, tsvs_repos,blacklist)

# Export the fillers to yaml file.
export_yaml(data, upheno_filler_data_file)

# Get everything in between the phenotype classes and the filler classes
check_call(['java', '-jar',java_fill,upheno_filler_data_file,upheno_filler_ontologies_list,outdir_patterns])
for f in os.listdir(outdir_patterns):
    if (f.endswith("-mappings.owl")):
        shutil.move(os.path.join(outdir_patterns,f), os.path.join(outdir_mappings, f))

# Load previous map. This must be up to date!
upheno_map = pd.read_csv(upheno_id_map, sep='\t')

# Get the largest assigned id... This variable is global and incremented by the function that generates new ids.
if len(upheno_map['defined_class'])>0:
    last_upheno_index = max([int(i.replace(upheno_prefix,"").lstrip("0")) for i in upheno_map['defined_class']])

# Add UPHENO ids to all tables around
add_upheno_ids_to_all_tables(outdir_patterns)

# Save the updated UPheno ID map
upheno_map.drop_duplicates().to_csv(upheno_id_map,sep='\t', index=False)

