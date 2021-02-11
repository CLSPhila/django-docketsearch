from typing import List, Dict, Tuple, Optional
from dataclasses import asdict
import re
import asyncio
import aiohttp
import ssl
import lxml.html
from .UJSSearch import UJSSearch
from .SearchResult import SearchResult


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


def make_docket_search_request(
    request_verification_token: str, docket_number: str
) -> Dict[str, str]:
    """
    Create the data packet for running the docket number search.
    """
    return {
        "SearchBy": "DocketNumber",
        "DocketNumber": docket_number,
        "__RequestVerificationToken": request_verification_token,
    }


async def search_by_docket_task(docket_number: str) -> Tuple[Dict, List]:
    """
    Task for searching ujs portal for a single docket number.
    """
    all_errs = []
    print("looking for docket " + docket_number)
    # request main page
    # sslcontext = ssl.create_default_context()
    # sslcontext.set_ciphers("HIGH:!DH:!aNULL")

    async with aiohttp.ClientSession(headers=UJSSearch.__headers__) as session:
        searcher = UJSSearch(session=session)
        # Request the landing page to get the form tokens
        main_page, errs = await searcher.fetch(
            "https://ujsportal.pacourts.us/CaseSearch"
        )
        all_errs.extend(errs)

        # Prepare the data for the search
        data = make_docket_search_request(
            request_verification_token=searcher.get_request_verification_token(
                main_page
            ),
            docket_number=docket_number,
        )

        # Request the docket search results.
        result_page, errs = await searcher.post(
            "https://ujsportal.pacourts.us/CaseSearch", data=data
        )
        all_errs.extend(errs)

    # parse results
    search_results, search_errs = searcher.parse_results_from_page(result_page)
    all_errs.extend(search_errs)
    print("  done looking for " + docket_number)
    return search_results, all_errs


async def search_by_dockets_task(
    docket_numbers: List[str],
) -> Tuple[List[SearchResult], List[str]]:
    """
    Async task for searching the ujs portal for a list of docket numbers.
    """
    # search_by_docket_task returns a tuple of [SearchResult], [errors].
    # so this async task doing that many times returns with a list of these pairs.
    # We need to reslice these, to go from [(a,b), (a,b)] to ([a], [b])
    results_with_errs = await asyncio.gather(
        *map(search_by_docket_task, docket_numbers)
    )
    results = []
    errs = []
    for res_list, err in results_with_errs:
        results.extend(res_list)
        errs.extend(err)
    return results, errs


def search_by_dockets(docket_numbers: List[str]) -> Tuple[List[Dict], List[str]]:
    """
    Search the CaseSearch UJS portal for docket numbers.
    """
    results, errs = asyncio.run(search_by_dockets_task(docket_numbers))
    return [asdict(r) for r in results], errs


def search_by_docket(docket_number: str) -> Tuple[List[Dict], List[str]]:
    return search_by_dockets([docket_number])