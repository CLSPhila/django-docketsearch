import pytest
from ujs_search.services.searchujs.UJSSearchFactory import UJSSearchFactory
from ujs_search.services.searchujs.CPSearch import CPSearch
from ujs_search.services.searchujs.MDJSearch import MDJSearch
from ujs_search.services.searchujs.by_name import search_by_name
from datetime import datetime, date
import logging
import time
import requests
from dataclasses import asdict
import os
import asyncio


logger = logging.getLogger(__name__)


def test_by_name(monkeypatch, mock_search_results):
    first_name = os.environ.get("UJS_SEARCH_TEST_FNAME") or "Joe"
    last_name = os.environ.get("UJS_SEARCH_TEST_LNAME") or "Normal"
    dob = (
        datetime.strptime(os.environ.get("UJS_SEARCH_TEST_DOB"), r"%Y-%m-%d")
        if os.environ.get("UJS_SEARCH_TEST_DOB")
        else date(2001, 1, 1)
    )
    results, errs = search_by_name(first_name, last_name, dob)
    assert len(results["CP"]) >= 0
    assert len(results["MDJ"]) >= 0


def test_cp_search_name(monkeypatch, mock_search_results):
    first_name = os.environ.get("UJS_SEARCH_TEST_FNAME") or "Joe"
    last_name = os.environ.get("UJS_SEARCH_TEST_LNAME") or "Normal"
    dob = (
        datetime.strptime(os.environ.get("UJS_SEARCH_TEST_DOB"), r"%Y-%m-%d")
        if os.environ.get("UJS_SEARCH_TEST_DOB")
        else date(2001, 1, 1)
    )

    cp_searcher = UJSSearchFactory.use_court("CP")
    results, errs = asyncio.run(
        cp_searcher.search_name(last_name=last_name, first_name=first_name, dob=dob)
    )
    assert len(results) > 0

    try:
        for r in results:
            r.docket_number
    except AttributeError:
        pytest.raises("Search Results missing docket number.")


def test_cp_search_name_multiple_pages():
    first_name = os.environ.get("UJS_SEARCH_TEST_FNAME_MULTIPAGE")
    last_name = os.environ.get("UJS_SEARCH_TEST_LNAME_MULTIPAGE")

    cp_searcher = UJSSearchFactory.use_court("CP")

    if os.environ.get("REAL_NETWORK_TESTS") != "TRUE":
        # don't run these tests.
        return
    results, errs = asyncio.run(
        cp_searcher.search_name(last_name=last_name, first_name=first_name)
    )
    assert len(results) == int(os.environ["UJS_SEARCH_TEST_MULTIPAGE_RESULTCOUNT"])

    try:
        for r in results:
            r.docket_number
    except AttributeError:
        pytest.raises("Search Results missing docket number.")


def test_cp_search_name_no_results(monkeypatch):
    def get_results(*args, **kwargs):
        return []

    if os.environ.get("REAL_NETWORK_TESTS") != "TRUE":
        logger.info("Monkeypatching network calls")
        monkeypatch.setattr(CPSearch, "search_name", get_results)
    else:
        logger.warning("Making real network calls in tests.")

    cp_searcher = UJSSearchFactory.use_court("CP")
    results, errs = asyncio.run(
        cp_searcher.search_name(first_name="Ferocity", last_name="Wimbledybear")
    )

    assert len(results) == 0


def test_mdj_search_name(monkeypatch, mock_search_results):
    mdj_searcher = UJSSearchFactory.use_court("MDJ")
    first_name = os.environ.get("UJS_SEARCH_TEST_FNAME") or "Joe"
    last_name = os.environ.get("UJS_SEARCH_TEST_LNAME") or "Normal"
    dob = (
        datetime.strptime(os.environ.get("UJS_SEARCH_TEST_DOB"), r"%Y-%m-%d")
        if os.environ.get("UJS_SEARCH_TEST_DOB")
        else date(2001, 1, 1)
    )

    results, errs = asyncio.run(
        mdj_searcher.search_name(last_name=last_name, first_name=first_name, dob=dob)
    )

    assert len(results) > 0
    try:
        for r in results:
            r.docket_number
    except KeyError:
        pytest.raises("Search Results missing docket number.")

    for r in results:
        for k, v in asdict(r).items():
            assert v.strip() != ""


def test_mdj_search_name_multiple_pages(monkeypatch, mock_search_results):
    mdj_searcher = UJSSearchFactory.use_court("MDJ")
    first_name = os.environ.get("UJS_SEARCH_TEST_FNAME_MULTIPAGE")
    last_name = os.environ.get("UJS_SEARCH_TEST_LNAME_MULTIPAGE")

    if os.environ.get("REAL_NETWORK_TESTS") != "TRUE":
        # don't run these tests.
        return

    results, errs = asyncio.run(
        mdj_searcher.search_name(last_name=last_name, first_name=first_name)
    )

    assert len(results) == int(os.environ.get("UJS_SEARCH_TEST_MULTIPAGE_RESULTCOUNT"))
    try:
        for r in results:
            r.docket_number
    except KeyError:
        pytest.raises("Search Results missing docket number.")

    all_docket_urls = [res.docket_sheet_url for res in results]
    compare = all_docket_urls[0]
    if all([compare == val for val in all_docket_urls]):
        pytest.fail("All docket urls are the same!")


def test_mdj_search_no_results_name(monkeypatch, mock_search_results):
    mdj_searcher = UJSSearchFactory.use_court("MDJ")

    if os.environ.get("REAL_NETWORK_TESTS") != "TRUE":
        logger.info("Monkeypatching network calls.")
        monkeypatch.setattr(MDJSearch, "search_name", lambda *a, **kw: [])
    else:
        logger.warning("Making network calls in tests.")

    first_name = "Joe"
    last_name = "NotARealPerson"
    dob = date(2001, 1, 1)

    results, errs = asyncio.run(
        mdj_searcher.search_name(last_name=last_name, first_name=first_name, dob=dob)
    )
    assert len(results) == 0
    assert len(errs) == 0


def test_parse_cp_docket_number():
    cp_searcher = UJSSearchFactory.use_court("CP")
    dn = "CP-12-CR-1234567-2000"
    parsed = cp_searcher.parse_docket_number(dn)
    assert parsed.court == "CP"
    assert parsed.sequence == "1234567"

    bad_dn = "CP-1234"
    with pytest.raises(ValueError):
        cp_searcher.parse_docket_number(bad_dn)


def test_cp_search_docket(monkeypatch, mock_search_results):
    dn = os.environ["CP_SEARCH_DOCKET_TEST"]
    if os.environ.get("REAL_NETWORK_TESTS") != "TRUE":
        logger.info("Monkeypatching network calls.")
        monkeypatch.setattr(CPSearch, "search_docket_number", mock_search_results)

    cp_searcher = UJSSearchFactory.use_court("CP")
    # loop = asyncio.get_event_loop()
    # results = loop.run_until_complete(cp_searcher.search_docket_number(dn))
    results, errs = asyncio.run(cp_searcher.search_docket_number(dn))
    assert len(results) == 1
    assert len(errs) == 0


def test_mdj_search_docket(monkeypatch, mock_search_results):
    dn = os.environ["MDJ_SEARCH_DOCKET_TEST"]
    if os.environ.get("REAL_NETWORK_TESTS") != "TRUE":
        logger.info("Monkeypatching network calls.")
        monkeypatch.setattr(MDJSearch, "search_docket_number", mock_search_results)

    mdj_searcher = UJSSearchFactory.use_court("MDJ")
    # loop = asyncio.get_event_loop()
    # results = loop.run_until_complete(mdj_searcher.search_docket_number(dn))
    results, errs = asyncio.run(mdj_searcher.search_docket_number(dn))
    assert len(results) == 1
    assert len(errs) == 0