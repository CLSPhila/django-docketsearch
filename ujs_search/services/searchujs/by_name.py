from django.conf import settings
import requests
import logging
from datetime import date
from typing import Optional, Dict
from .UJSSearchFactory import UJSSearchFactory
logger = logging.getLogger(__name__)

def search_by_name(first_name: str, last_name: str, dob: Optional[date] = None, court="both") -> Dict:
    """
    Search the CP or MDJ sites for public records relating to a person's name. 
    """
    assert court in (["both"] + UJSSearchFactory.COURTS)
    if court=="both":
        results=search_by_name(first_name,last_name,dob,court="CP")
        results.update(search_by_name(first_name,last_name,dob,court="MDJ"))
        return results
    searcher = UJSSearchFactory.use_court(court)
    return {court: searcher.search_name(first_name, last_name, dob)}
    
   