import logging
import os
logger = logging.getLogger(__name__)

def setup_view(view, request, *args, **kwargs):
    """
    Mimic ``as_view()``, but returns view instance.
    Use this function to get view instances on which you can run unit tests,
    by testing specific methods.
    """

    view.request = request
    view.args = args
    view.kwargs = kwargs
    return view


def test_search_name(monkeypatch, setup_tests, api_rf, name_search_data):
    logger.info(setup_tests)
    req = api_rf.post(
        "/search/name",
    )
    from ujs_search.views import SearchName 
    # this DIY Monkeypatching is necessary b/c the request object that gets created is a 
    # default django Request, not a REST FRAMEWORK request, so has no data attr.
    # see discussion at https://github.com/encode/django-rest-framework/issues/3608#issuecomment-154427523
    setattr(req, 'data', name_search_data)

    v = setup_view(SearchName(), req)
    resp = v.post(req)
    assert resp.status_code == 200

def test_search_cp_docket_number(monkeypatch, setup_tests, api_rf):
    logger.info(setup_tests)
    req = api_rf.post(
        "/search/docket",
    )
    dn = os.environ["CP_SEARCH_DOCKET_TEST"]
    search_data = {"docket_number": dn} 
    from ujs_search.views import SearchDocket
    # this DIY Monkeypatching is necessary b/c the request object that gets created is a 
    # default django Request, not a REST FRAMEWORK request, so has no data attr.
    # see discussion at https://github.com/encode/django-rest-framework/issues/3608#issuecomment-154427523
    setattr(req, 'data', search_data)

    v = setup_view(SearchDocket(), req)
    resp = v.post(req)
    assert resp.status_code == 200

def test_search_mdj_docket_number(monkeypatch, setup_tests, api_rf):
    logger.info(setup_tests)
    req = api_rf.post(
        "/search/docket",
    )
    dn = os.environ["MDJ_SEARCH_DOCKET_TEST"]
    search_data = {"docket_number": dn} 
    from ujs_search.views import SearchDocket
    # this DIY Monkeypatching is necessary b/c the request object that gets created is a 
    # default django Request, not a REST FRAMEWORK request, so has no data attr.
    # see discussion at https://github.com/encode/django-rest-framework/issues/3608#issuecomment-154427523
    setattr(req, 'data', search_data)

    v = setup_view(SearchDocket(), req)
    resp = v.post(req)
    assert resp.status_code == 200

