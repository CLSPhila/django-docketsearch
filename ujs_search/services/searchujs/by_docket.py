import re
from .UJSSearchFactory import UJSSearchFactory
from .CPSearch import CPSearch
from .MDJSearch import MDJSearch
from typing import Optional
import asyncio
from dataclasses import asdict


def which_court(docket_number: str) -> Optional[str]:
    """
    Given a docket number, determine if is is a CP or MDJ docket number.

    If the docket number is in the wrong format, return None.
    """

    cp_patt = re.compile(CPSearch.DOCKET_NUMBER_REGEX, re.IGNORECASE)
    md_patt = re.compile(MDJSearch.DOCKET_NUMBER_REGEX, re.IGNORECASE)

    if cp_patt.match(docket_number):
        return UJSSearchFactory.CP
    if md_patt.match(docket_number):
        return UJSSearchFactory.MDJ
    return None


def search_by_docket(docket_number):
    """
    Search UJS for a single docket using a docket number.


    """
    court = which_court(docket_number)
    if not court:
        raise ValueError(f"{docket_number}")
    searcher = UJSSearchFactory.use_court(court)
    # loop = asyncio.get_event_loop()
    # results = loop.run_until_complete(searcher.search_docket_number(docket_number))
    try:
        results, errs = asyncio.run(
            searcher.search_docket_number(docket_number.upper())
        )
        return [asdict(r) for r in results], errs
    except Exception as err:
        return [], [str(err)]


""" NB - to implement a search_by_multiple_dockets, using async, we should prob. use a semaphor to limit 
concurrency"""