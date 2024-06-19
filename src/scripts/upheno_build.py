import click
import logging
from create_sssom import create_upheno_sssom

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
@click.pass_context
def prepare_patterns(ctx, pattern_dir, output):
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
@click.pass_context
def create_species_independent_sssom_mappings(ctx, upheno_id_map, patterns_dir, matches_dir, output_file_tsv, output_file_owl):
    """Create SSSOM file from upheno id map and pattern matches"""
    logger.debug(f'Creating species-neutral SSSOM mappings: {output_file_tsv} and writing to {output_file_owl}')
    click.echo('Creating SSSOM...')
    create_upheno_sssom(upheno_id_map, patterns_dir, matches_dir, output_file_tsv, output_file_owl)

# Subcommand: validate_mappings
@upheno.command()
@click.argument('mappings_file')
@click.option('--report', '-r', default='validation_report.txt', help='Report file for validation')
@click.pass_context
def validate_mappings(ctx, mappings_file, report):
    """Validate the mappings"""
    logger.debug(f'Validating mappings in {mappings_file} and writing report to {report}')
    click.echo('Validating mappings...')

# Subcommand: help
@upheno.command()
@click.pass_context
def help(ctx):
    """Show this message and exit"""
    click.echo(ctx.parent.get_help())

if __name__ == '__main__':
    upheno()
