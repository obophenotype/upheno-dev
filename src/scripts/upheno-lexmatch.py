import logging
from pathlib import Path
from oaklib.resource import OntologyResource
from oaklib.implementations.sqldb.sql_implementation import SqlImplementation
from oaklib.utilities.lexical.lexical_indexer import (
    create_lexical_index,
    lexical_index_to_sssom,
    load_mapping_rules,
    save_lexical_index,
    load_lexical_index
)
import sys
import click
import yaml

from sssom.constants import SUBJECT_ID, OBJECT_ID
from sssom.util import filter_prefixes
from sssom.parsers import parse_sssom_table
from sssom.writers import write_table
from sssom.io import get_metadata_and_prefix_map, filter_file

SRC = Path(__file__).resolve().parents[1]
ONTOLOGY_DIR = SRC / "ontology"
OUT_INDEX_DB = ONTOLOGY_DIR / "tmp/upheno.db.lexical.yaml"
TEMP_DIR = ONTOLOGY_DIR / "tmp"

input_argument = click.argument("input", required=True, type=click.Path())
output_option = click.option(
    "-o",
    "--output",
    help="Path for output file.",
    default=sys.stdout,
)


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
def main(verbose: int, quiet: bool):
    """Run the SSSOM CLI."""
    logger = logging.getLogger()
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)


@main.command()
@input_argument
@click.option(
    "-c",
    "--config",
    help="YAML file containing metadata.",
)
@click.option(
    "-r",
    "--rules",
    help="Ruleset for mapping.",
)
@click.option(
    "--recreate/--no-recreate",
    default=True,
    show_default=True,
    help="if true and lexical index is specified, always recreate, otherwise load from index",
)
@output_option
def run(input: str, config: str, rules: str, recreate:bool, output: str):
    # Implemented `meta` param in `lexical_index_to_sssom`

    meta = get_metadata_and_prefix_map(config)
    with open(config, "r") as f:
        yml = yaml.safe_load(f)

    prefix_of_interest = yml["subject_prefixes"]

    resource = OntologyResource(slug=f"sqlite:///{Path(input).absolute()}")
    oi = SqlImplementation(resource=resource)
    ruleset = load_mapping_rules(rules)
    syn_rules = [x.synonymizer for x in ruleset.rules if x.synonymizer]
    if not recreate and Path(OUT_INDEX_DB).exists():
        lexical_index = load_lexical_index(OUT_INDEX_DB)
    else:
        lexical_index = create_lexical_index(oi=oi, synonym_rules=syn_rules)
        save_lexical_index(lexical_index, OUT_INDEX_DB)

    if rules:
        msdf = lexical_index_to_sssom(
            oi, lexical_index, ruleset=load_mapping_rules(rules), meta=meta
        )
    else:
        msdf = lexical_index_to_sssom(oi, lexical_index, meta=meta)

    msdf.df = filter_prefixes(
        df=msdf.df, filter_prefixes=prefix_of_interest, features=[SUBJECT_ID, OBJECT_ID]
    )
    with open(str(Path(output)), "w", encoding="utf8") as f:
        write_table(msdf, f)

if __name__ == "__main__":
    main()