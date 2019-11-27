import pytest
from ujs_search.services.searchujs.UJSSearchFactory import UJSSearchFactory
from ujs_search.services.searchujs.CPSearch import CPSearch
from ujs_search.services.searchujs.MDJSearch import MDJSearch
from datetime import datetime, date
import logging
import time
import requests
import os

logger = logging.getLogger(__name__)

def get_results(*args, **kwargs):
    """
    the monkeypatched version a response from the service. 

    Used to prevent tests from making network calls.
    """
    return [
        {
            'docket_number': 'CP-11-CR-0001111-2015', 
            'docket_sheet_url': 'CPReport.ashx?docketNumber=xxx', 
            'summary_url': 'CourtSummaryReport.ashx?docketNumber=yyy',
            'caption': 'Comm. v. Normal', 
            'case_status': 'Closed',
            'otn': 'Txxxx', 
            'dob': '1/11/1940'
        }, 
    ]

def test_cp_search(monkeypatch):



    if os.environ.get("REAL_NETWORK_TESTS") != "TRUE":
        logger.info("Monkeypatching network calls.")
        monkeypatch.setattr(CPSearch,"search_name", get_results)
    else:
        logger.warning("Making network calls in tests.")

    first_name = os.environ.get("UJS_SEARCH_TEST_FNAME") or "Joe"
    last_name = os.environ.get("UJS_SEARCH_TEST_LNAME") or "Normal"
    dob = datetime.strptime(os.environ.get("UJS_SEARCH_TEST_DOB"), r"%Y-%m-%d") if \
        os.environ.get("UJS_SEARCH_TEST_DOB") else date(2001, 1, 1)

    cp_searcher = UJSSearchFactory.use_court("CP")
    results = cp_searcher.search_name(
        last_name=last_name, first_name=first_name, 
        dob=dob)
    assert len(results) > 0 
    try:
        for r in results:
            r["docket_number"]
    except KeyError:
        pytest.raises("Search Results missing docket number.")


def test_cp_search_no_results(monkeypatch):

    def get_results(*args, **kwargs):
        return []

    if os.environ.get("REAL_NETWORK_TESTS") != "TRUE":
        logger.info("Monkeypatching network calls")
        monkeypatch.setattr(CPSearch, "search_name", get_results)
    else:
        logger.warning("Making real network calls in tests.")

    cp_searcher = UJSSearchFactory.use_court("CP")
    results = cp_searcher.search_name(
        first_name="Ferocity", last_name="Wimbledybear") 
    assert len(results) == 0 


def test_mdj_search(monkeypatch):
    mdj_searcher = UJSSearchFactory.use_court("MDJ")

    if os.environ.get("REAL_NETWORK_TESTS") != "TRUE":
        logger.info("Monkeypatching network calls.")
        monkeypatch.setattr(MDJSearch,"search_name", get_results)
    else:
        logger.warning("Making network calls in tests.")

    first_name = os.environ.get("UJS_SEARCH_TEST_FNAME") or "Joe"
    last_name = os.environ.get("UJS_SEARCH_TEST_LNAME") or "Normal"
    dob = datetime.strptime(os.environ.get("UJS_SEARCH_TEST_DOB"), r"%Y-%m-%d") if \
        os.environ.get("UJS_SEARCH_TEST_DOB") else date(2001, 1, 1)

 

    results = mdj_searcher.search_name(
        last_name=last_name, 
        first_name=first_name, 
        dob=dob)
    assert len(results) > 0
    try:
        for r in results:
            r["docket_number"]
    except KeyError:
        pytest.raises("Search Results missing docket number.")


def test_mdj_search_no_results(monkeypatch):
    mdj_searcher = UJSSearchFactory.use_court("MDJ")

    if os.environ.get("REAL_NETWORK_TESTS") != "TRUE":
        logger.info("Monkeypatching network calls.")
        monkeypatch.setattr(CPSearch,"search_name", get_results)
    else:
        logger.warning("Making network calls in tests.")

    first_name = "Joe"
    last_name = "NotARealPerson"
    dob = date(2001, 1, 1)

    results = mdj_searcher.search_name(
        last_name=last_name, 
        first_name=first_name, 
        dob=dob)
    assert len(results) == 0



