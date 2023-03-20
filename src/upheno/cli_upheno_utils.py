"""uPheno utils Command Line Interface"""

import click


@click.command()
def hello_world():
    """hello world"""
    print("hello world")
