
import pandas as pd
import os
import yaml
import glob
import argparse
from sssom.context import get_converter
from sssom.parsers import from_sssom_dataframe
from sssom.writers import write_table

def main():
    parser = argparse.ArgumentParser(description='Create SSSOM file from upheno id map and pattern matches')
    parser.add_argument('--upheno_id_map', type=str, help='upheno id map file')
    parser.add_argument('--patterns_dir', type=str, help='directory containing pattern files')
    parser.add_argument('--matches_dir', type=str, help='directory containing pattern matches')
    parser.add_argument('--output', type=str, help='output file')
    args = parser.parse_args()
    create_upheno_sssom(args.upheno_id_map, args.patterns_dir, args.matches_dir, args.output)

def get_id_columns(pattern_file):
    try:
        with open(pattern_file, "r") as stream:
            pattern_json = yaml.safe_load(stream)
            idcolumns = list(pattern_json["vars"].keys())
            return idcolumns
    except Exception as exc:
        print("Could not get id columns: " + pattern_file)
        return None

def create_upheno_sssom(upheno_id_map, patterns_dir, matches_dir, output_file):

    all_pattern_matches_map = dict()

    for pattern_match_tsv in glob.glob(matches_dir + "/**/*.tsv"):
        pattern_name = os.path.basename( pattern_match_tsv ).split(".")[0]
        df = pd.read_csv(pattern_match_tsv, sep='\t')
        if pattern_name in all_pattern_matches_map:
            all_pattern_matches_map[pattern_name] = pd.concat([ all_pattern_matches_map[pattern_name], df ])
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
        if id_columns == None:
            id_columns = get_id_columns(os.path.join(patterns_dir, pattern_file))
            cache_pattern_file_to_idcolumn[pattern_file] = id_columns
        if id_columns == None:
            continue
        # print(tokens)
        # print(pattern_file)
        # print(id_columns)
        # print(fillers)
        tsv_df = all_pattern_matches_map[pattern_name]
        #filtered = tsv[lambda df: filter_row(df, id_columns, fillers) ]

        mask = pd.Series(True, index=tsv_df.index)
        for col, filler in zip(id_columns, fillers):
            mask = mask & (tsv_df[col] == filler)
        subset_df = tsv_df[mask]

        # print(subset_df)

        upheno_id = row['defined_class']

        for index, row in subset_df.iterrows():
            species_specific_id = row['defined_class']
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
    write_table(msdf, open(output_file, "w"))

def filter_row(df, id_columns, fillers):
    n = 0
    while n < len(id_columns):
        column = id_columns[n]
        filler = fillers[n]
        if df[column] != filler:
            return False
    return True

if __name__ == "__main__":
    main()

