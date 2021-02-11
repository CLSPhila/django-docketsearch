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


@ujs.command()
@click.option("--first-name", "-f", help="First name for search")
@click.option("--last-name", "-l", help="Last name for search")
@click.option(
    "--date-of-birth", "-d", help="Birth date for search", required=False, default=None
)
def name(first_name, last_name, date_of_birth):
    results = search_by_name(first_name, last_name, date_of_birth)
    click.echo(json.dumps(results, indent=4))
    click.echo("---Complete.---")
