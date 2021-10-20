from django.conf import settings
import requests
import logging
from datetime import date, datetime
from typing import Optional, Dict, Tuple, List
import aiohttp
from .UJSSearch import UJSSearch
from .SearchResult import SearchResult

logger = logging.getLogger(__name__)
from dataclasses import asdict
import asyncio


def make_name_search_request(
    request_verification_token: str,
    first_name: str,
    last_name: str,
    dob: Optional[date],
):
    """
    Create the data packet for running a search by a person's name.
    """
    data = {
        "SearchBy": "ParticipantName",
        "ParticipantFirstName": first_name,
        "ParticipantLastName": last_name,
        "__RequestVerificationToken": request_verification_token,
        "FiledStartDate": "1920-01-01",
        "FiledEndDate": date.today().strftime(r"%Y-%m-%d"),
    }
    if dob:
        data["ParticipantDateOfBirth"] = dob.strftime(r"%Y-%m-%d")

    return data


async def search_by_name_task(
    first_name: str, last_name: str, dob: Optional[date]
) -> Tuple[List[SearchResult], List[str]]:
    """
    Async task to earch the UJS CaseSearch site for a record relating to a person's name.

    Args:
        first_name (str): First name of person to search
        last_name (str): Last name
        dob (date): Birth date, optional

    Returns:
        A list of search results
        A list of error messages.
    """
    all_errs = []
    logger.debug("searching for dockets related to %s", first_name)

    async with aiohttp.ClientSession(headers=UJSSearch.__headers__) as session:
        searcher = UJSSearch(session=session)
        # Request the landing page to get the form tokens
        main_page, errs = await searcher.fetch(
            "https://ujsportal.pacourts.us/CaseSearch"
        )
        all_errs.extend(errs)

        # Prepare the data for the search
        data = make_name_search_request(
            request_verification_token=searcher.get_request_verification_token(
                main_page
            ),
            first_name=first_name,
            last_name=last_name,
            dob=dob,
        )

        result_page, errs = await searcher.post(
            "https://ujsportal.pacourts.us/CaseSearch", data=data
        )
        all_errs.extend(errs)

    # parse results
    search_results, search_errs = searcher.parse_results_from_page(result_page)
    all_errs.extend(search_errs)
    logger.debug("  done looking for dockets related to %s", first_name)
    return search_results, all_errs


def search_by_name(
    first_name: str, last_name: str, dob: Optional[date] = None
) -> Tuple[Dict[str, str], List[str]]:
    """
    Search the UJS CaseSearch site for public records relating to a person's name.

    Args:
        first_name (str): First name of person to search
        last_name (str): Last name
        dob (date): Birth date, optional

    Returns:
        the results as a list of dicts.
    """
    results, errs = asyncio.run(search_by_name_task(first_name, last_name, dob))
    return [asdict(res) for res in results], errs
