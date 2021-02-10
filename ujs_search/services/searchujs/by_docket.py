from typing import List, Dict, Tuple
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


def search_by_docket_pre2021(docket_number):
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


async def search_by_docket_task(docket_number: str) -> Tuple[Dict, List]:
    """
    Task for searching ujs portal for a single docket number.
    """
    print("looking for docket " + docket_number)
    # request main page

    # find keys for the next request

    # select docket number

    # post docket number search

    # parse results

    print("  done looking for " + docket_number)
    return {}, []


async def search_by_dockets_task(docket_numbers: List[str]) -> Tuple[Dict, List]:
    """
    Async task for searching the ujs portal for a list of docket numbers.
    """
    results_with_errs = await asyncio.gather(
        *map(search_by_docket_task, docket_numbers)
    )
    results = []
    errs = []
    for res, err in results_with_errs:
        results.append(res)
        errs.append(err)
    return results, errs


def search_by_dockets(docket_numbers: List[str]) -> Tuple[Dict, List]:
    """
    Search the CaseSearch UJS portal for docket numbers.
    """
    results, errs = asyncio.run(search_by_dockets_task(docket_numbers))
    return results, errs


""" NB - to implement a search_by_multiple_dockets, using async, we should prob. use a semaphor to limit 
concurrency"""