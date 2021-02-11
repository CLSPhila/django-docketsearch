"""
Testing the functions that search for dockets.
"""

import os
from ujs_search.services.searchujs import search_by_dockets, SearchResult


def test_search_by_dockets():
    cp_docket = os.environ["CP_SEARCH_DOCKET_TEST"]
    md_docket = os.environ["MDJ_SEARCH_DOCKET_TEST"]
    dockets = [cp_docket, md_docket]
    results, errs = search_by_dockets(dockets)
    assert len(results) == 2
    for res in results:
        assert "docket_number" in res.keys()
        assert "otn" in res.keys()
        assert "filing_date" in res.keys()


def test_no_docket_found():
    results, errs = search_by_dockets(["CP-12345"])
    assert len(results) == 0