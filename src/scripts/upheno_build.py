import click
import os
import logging
from lib import uPhenoConfig, download_patterns as dl_patterns, compute_upheno_stats, create_upheno_sssom

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
@click.argument('pattern_dir')
@click.option('--output', '-o', default='patterns_output.txt', help='Output file for patterns')
def prepare_patterns(pattern_dir, output):
    """Prepare pattern files for upheno"""
    logger.debug(f'Preparing patterns from {pattern_dir} and writing to {output}')
    click.echo('Preparing patterns...')


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
