from django.conf import settings
import requests
import logging
from datetime import date
from typing import Optional, Dict
from .UJSSearchFactory import UJSSearchFactory
logger = logging.getLogger(__name__)
from dataclasses import asdict
import asyncio

async def search_by_name_task(
    first_name: str, last_name: str, dob: Optional[date] = None, court: str = "both", timelimit = float("Inf")) -> Dict:
    assert court in (["both"] + UJSSearchFactory.COURTS)
    if court=="both":
        cp_results, cp_errors = await search_by_name_task(first_name,last_name,dob,court="CP", timelimit=timelimit)
        mdj_results, mdj_errors = await search_by_name_task(first_name, last_name, dob, court="MDJ", timelimit=timelimit)
        results = cp_results
        errors = cp_errors
        results.update(mdj_results)
        errors.update(mdj_errors)
        return results, errors
 
    searcher = UJSSearchFactory.use_court(court, timelimit=timelimit)
    results, errors = await searcher.search_name(first_name, last_name, dob)
    results = [asdict(r) for in results]
    #results = [asdict(r), errs for r, errs in await searcher.search_name(first_name, last_name, dob)]
    return {court: results}, {court: errors}

def search_by_name(*args, **kwargs) -> Dict:
    """
    Search the CP or MDJ sites for public records relating to a person's name. 

    Return the results as a list of dicts. 
    """
    results, errors = asyncio.run(search_by_name_task(*args, **kwargs))
    return results, errors


    
   
