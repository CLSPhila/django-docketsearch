from django.conf import settings
import requests
import logging
from datetime import date
from typing import Optional, Dict
from .UJSSearchFactory import UJSSearchFactory
logger = logging.getLogger(__name__)
from dataclasses import asdict

async def search_by_name_task(
    first_name: str, last_name: str, dob: Optional[date] = None, court: str = "both") -> Dict:
    assert court in (["both"] + UJSSearchFactory.COURTS)
    if court=="both":
        cp_results = await search_by_name_task(first_name,last_name,dob,court="CP")
        mdj_results = await search_by_name_task(first_name, last_name, dob, court="MDJ")
        results = cp_results
        results.update(mdj_results)
        return results
 
    searcher = UJSSearchFactory.use_court(court)
    results = [asdict(r) for r in await searcher.search_name(first_name, last_name, dob)]
    return {court: results}

def search_by_name(*args, **kwargs) -> Dict:
    """
    Search the CP or MDJ sites for public records relating to a person's name. 

    Return the results as a list of dicts. 
    """
    results = asyncio.run(search_by_name_task(*args, **kwargs))
    return results


    
   