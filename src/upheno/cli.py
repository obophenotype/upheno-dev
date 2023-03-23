"""Command line interface for uPheno-dev."""
import logging

import click

from upheno import __version__
from upheno.cli_upheno import run
from upheno.cli_upheno_utils import hello_world

__all__ = [
    "main",
]

logger = logging.getLogger(__name__)
info_log = logging.getLogger("info")


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
def main(verbose=1, quiet=False) -> None:
    """main CLI method for uPheno
    Args:
        verbose (int, optional): Verbose flag.
        quiet (bool, optional): Queit Flag.
    """
    if verbose >= 2:
        info_log.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        info_log.setLevel(level=logging.INFO)
    else:
        info_log.setLevel(level=logging.WARNING)
    if quiet:
        info_log.setLevel(level=logging.ERROR)


@click.group()
def upheno():
    """upheno"""


upheno.add_command(run)


@click.group()
def upheno_utils():
    """upheno_utils"""


upheno_utils.add_command(hello_world)


if __name__ == "__main__":
    main()
