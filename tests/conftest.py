import pytest
import os 
import django
import logging
from ujs_search.services.searchujs.SearchResult import SearchResult    
from ujs_search.services.searchujs.CPSearch import CPSearch
from ujs_search.services.searchujs.MDJSearch import MDJSearch

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_search_results(monkeypatch):
    """
    Monkeypatch network calling, so we avoid network calls unless 
    really necessary.
    """
    def get_results(*args, **kwargs):
        return [
                SearchResult(**{
                    'docket_number': 'CP-11-CR-0001111-2015', 
                    'docket_sheet_url': 'CPReport.ashx?docketNumber=xxx', 
                    'summary_url': 'CourtSummaryReport.ashx?docketNumber=yyy',
                    'caption': 'Comm. v. Normal', 
                    'case_status': 'Closed',
                    'otn': 'Txxxx', 
                    'dob': '1/11/1940',
                    'filing_date':'1/1/2000',
                }), 
            ], []

    if os.environ.get("REAL_NETWORK_TESTS") != "TRUE":
        logger.info("Monkeypatching network calls.")
        monkeypatch.setattr(MDJSearch,"search_name", get_results)
        
        monkeypatch.setattr(CPSearch,"search_name", get_results)
    else:
        logger.warning("Making network calls in tests.")



    return get_results



@pytest.fixture
def setup_tests(monkeypatch, mock_search_results):
    """
    Setup the django app

    Turns out there's nothing to do here, b/c pytest auto-sets up django, using the env var 'DJANGO_SETTINGS_MODULE'
    
    """
    return "Django was set up by pytest-django."
    #os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.test_settings'
    #django.setup()
    #return "Django is setup"


@pytest.fixture
def api_rf(setup_tests):    
    from rest_framework.test import APIRequestFactory
    return APIRequestFactory()


@pytest.fixture
def name_search_data():
    if os.environ.get("REAL_NETWORK_TESTS") == "TRUE":
        data = {
            "first_name": os.environ["UJS_SEARCH_TEST_FNAME"],
            "last_name": os.environ["UJS_SEARCH_TEST_LNAME"],
            "dob": os.environ["UJS_SEARCH_TEST_DOB"],
        }
    else:
        data = {
            "first_name": "Pizza",
            "last_name": "Pie",
            "dob": "2000-01-01",
        }
    return data