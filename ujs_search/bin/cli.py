"""
CLI Interface for searching the UJS portal.

"""


import click
import json
from ujs_search.services.searchujs import search_by_name, search_by_dockets


@click.group()
def ujs():
    pass


@ujs.command()
@click.option("--first-name", "-fn", help="First name for search", required=True)
@click.option("--last-name", "-ln", help="Last name for search", required=True)
@click.option("--dob", "-d", help="Date of birth for search", required=True)
def name(first_name: str, last_name: str, dob: str):
    """
    Search the UJS Portal for public records relating to a person's name.
    """
    results = search_by_name(first_name, last_name, dob)
    click.echo(json.dumps(results, indent=4))
    click.echo("---Complete.---")


@ujs.command()
@click.option(
    "--docket-number", "-n", help="Docket number to search for", required=True
)
def docket(docket_number: str):
    """
    Search the UJS Portal for a specific docket.
    """
    results = search_by_dockets([docket_number])
    click.echo(json.dumps(results, indent=4))
    click.echo("---Complete.---")