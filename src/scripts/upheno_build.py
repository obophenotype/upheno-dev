import click
import os
import logging
import pandas as pd
from lib import (
    uPhenoConfig,
    download_patterns as dl_patterns,
    compute_upheno_stats,
    create_upheno_sssom,
    add_upheno_ids_to_fillers_and_filter_out_bfo
)

# Setup logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', is_flag=True, help='Enable verbose mode')
@click.pass_context
def upheno(ctx, verbose):
    """Main CLI for upheno"""
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode is on")
    else:
        logger.info("Running in normal mode")


# Subcommand: prepare_patterns
@upheno.command()
@click.option('--patterns-directory', help='Output file for SSSOM')
@click.option('--fillers-directory')
@click.option('--tmp-directory')
@click.option('--upheno-config', help='uPheno config file')
def add_upheno_ids_to_fillers(patterns_directory, fillers_directory, tmp_directory, upheno_config):
    """Prepare pattern files for upheno"""
    logger.debug(f'Adding uPheno IDs to fillers and writing to {fillers_directory}')
    click.echo('Adding uPheno IDs to fillers...')
    config = uPhenoConfig(upheno_config)
    upheno_prefix = "http://purl.obolibrary.org/obo/UPHENO_"
    upheno_map = pd.read_csv(config.get_upheno_id_map(), sep="\t")

    blacklisted_upheno_ids_path = os.path.join(tmp_directory, "blacklisted_upheno_iris.txt")

    # Do not use these Upheno IDs
    with open(blacklisted_upheno_ids_path) as f:
        blacklisted_upheno_ids = f.read().splitlines()

    add_upheno_ids_to_fillers_and_filter_out_bfo(pattern_dir=patterns_directory,
                                                 upheno_map=upheno_map,
                                                 blacklisted_upheno_ids=blacklisted_upheno_ids,
                                                 upheno_config=config,
                                                 upheno_fillers_dir=fillers_directory,
                                                 upheno_prefix=upheno_prefix)


# Subcommand: create_sssom
@upheno.command()
@click.option('--upheno-id-map', default='sssom_output.tsv', help='Output file for SSSOM')
@click.option('--patterns-dir', default='sssom_output.tsv', help='Output file for SSSOM')
@click.option('--matches-dir', default='sssom_output.tsv', help='Output file for SSSOM')
@click.option('--output-file-tsv', default='sssom_output.tsv', help='Output file for SSSOM')
@click.option('--output-file-owl', default='sssom_output.tsv', help='Output file for SSSOM')
def create_species_independent_sssom_mappings(upheno_id_map, patterns_dir, matches_dir, output_file_tsv,
                                              output_file_owl):
    """Create SSSOM file from upheno id map and pattern matches"""
    logger.debug(f'Creating species-neutral SSSOM mappings: {output_file_tsv} and writing to {output_file_owl}')
    click.echo('Creating SSSOM...')
    create_upheno_sssom(upheno_id_map, patterns_dir, matches_dir, output_file_tsv, output_file_owl)


# Subcommand: validate_mappings
@upheno.command()
@click.option('--upheno-config', help='uPheno config file')
@click.option('--pattern-directory', help='Pattern directory to download to.')
def download_patterns(upheno_config, pattern_directory):
    """Validate the mappings"""
    logger.debug(f'Download uPheno Patterns to {pattern_directory}.')
    click.echo('Download uPheno Patterns...')
    config = uPhenoConfig(upheno_config)
    dl_patterns(upheno_pattern_repos=config.get_pattern_repos(),
                pattern_dir=pattern_directory, upheno_config=config)


@upheno.command()
@click.option('--upheno-config', help='uPheno config file')
@click.option('--pattern-directory', help='Pattern directory to download to.')
@click.option('--stats-directory', help='Pattern directory to download to.')
@click.option('--matches-directory', help='Pattern directory to download to.')
def compute_upheno_statistics(upheno_config, pattern_directory, stats_directory, matches_directory):
    """Validate the mappings"""
    logger.debug(f'Download uPheno Patterns to {pattern_directory}.')
    click.echo('Download uPheno Patterns...')
    upheno_config = uPhenoConfig(upheno_config)
    os.environ["ROBOT_JAVA_ARGS"] = upheno_config.get_robot_java_args()
    compute_upheno_stats(upheno_config=upheno_config,
                         pattern_dir=pattern_directory,
                         matches_dir=matches_directory,
                         stats_dir=stats_directory)


# Subcommand: help
@upheno.command()
@click.pass_context
def show_help(ctx):
    """Show this message and exit"""
    click.echo(ctx.parent.get_help())


if __name__ == '__main__':
    upheno()
