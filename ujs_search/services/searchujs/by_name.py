from django.conf import settings
import requests
import logging
from datetime import date
from typing import Optional, Dict, Tuple, List
from .UJSSearchFactory import UJSSearchFactory

logger = logging.getLogger(__name__)
from dataclasses import asdict
import asyncio


async def search_by_name_task(
    first_name: str, last_name: str, dob: Optional[date] = None, court: str = "both"
) -> Dict[str, List]:
    assert court in (["both"] + UJSSearchFactory.COURTS)
    if court == "both":
        cp_results, cp_errs = await search_by_name_task(
            first_name, last_name, dob, court="CP"
        )
        mdj_results, mdj_errs = await search_by_name_task(
            first_name, last_name, dob, court="MDJ"
        )
        cp_results.update(mdj_results)
        errs = cp_errs + mdj_errs
        return cp_results, errs

    searcher = UJSSearchFactory.use_court(court)

    try:
        results, errs = await searcher.search_name(first_name, last_name, dob)
        results = [asdict(r) for r in results]
    except Exception as err:
        results = []
        errs = [str(err)]
    return {court: results}, errs


def search_by_name(*args, **kwargs) -> Dict:
    """
    Search the CP or MDJ sites for public records relating to a person's name.

    Return the results as a list of dicts.
    """
    results, errs = asyncio.run(search_by_name_task(*args, **kwargs))
    return results, errs
