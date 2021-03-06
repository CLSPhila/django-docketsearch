# django-docketsearch

A Django Rest Framework app that adds endpoints useful for searching the PA UJS portal for public records.

## Getting started

1. Add "ujs" to your INSTALLED_APPS setting like this::

```
    
    from rest_framework import permissions
    UJS_SEARCH_PERMISSION_CLASSES = [permissions.IsAuthenticatedOrReadOnly]
    
    INSTALLED_APPS = [
        ...
        'ujs_search',
    ]
```


2. Include the ujs_search URLconf in your project urls.py like this::

    path('ujs/', include('ujs_search.urls')),


## Testing

Test with `pytest --log-cli-level info` (include the switch to see helpful logging info)

You'll need a `.env` file, something like:

```
DJANGO_SETTINGS_MODULE=tests.test_settings

REAL_NETWORK_TESTS=False

UJS_SEARCH_TEST_FNAME=Greasy
UJS_SEARCH_TEST_LNAME=Spoon
UJS_SEARCH_TEST_DOB=1950-05-05

cp_search_docket_test=cp-43-cr-1234567-2020
mdj_search_docket_test=mj-01234-cr-7654321-2020

# vars for testing whether the name search can collect from multiple pages.
# need to use a name that returns multiple pages (obviously?).
UJS_SEARCH_TEST_FNAME_MULTIPAGE=John
UJS_SEARCH_TEST_LNAME_MULTIPAGE=Smith
UJS_SEARCH_TEST_DOB=1950-05-05
# how many results should this return, if we're succesfully scraping multiple pages?
UJS_SEARCH_TEST_MULTIPAGE_RESULTCOUNT=50

```

## Additional Information

This project began as an app in [RecordLib](https://github.com/CLSPhila/RecordLib).