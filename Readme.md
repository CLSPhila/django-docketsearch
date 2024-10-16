# django-docketsearch

[DEPRECATED]

A Django Rest Framework app that adds endpoints useful for searching the PA UJS portal for public records.

## Endpoints

The app provides three endpoints for searching the UJS portal.

**searching by name**

`POST /search/name/` accepts three parameters:

```
{
    first_name: "",
    last_name: "",
    dob: "",
}
```

`dob` is optional.

**searching for a specific docket**

`POST /search/docket/` accepts just one parameter: a `docket_number`.

**searching for multiple dockets at once**

`POST /search/docket/many/` accepts `docket_numbers`, which is a list of docket numbers.

**Return values**
All three endpoints, if they return a `200` response, return an object with the same shape:

```
{
    searchResults: [
        {
            "docket_number": "CP-1234",
            "court": "Common Pleas",
            "docket_sheet_url": "https://ujsportal.pacourts.us/Report/CpDocketSheet?docketNumber=CP-1234",
            "summary_url": "https://ujsportal.pacourts.us/Report/CpCourtSummary?docketNumber=CP-1234",
            "caption": "Comm. v. Rabbit, Bunny.",
            "filing_date": "01/01/2020",
            "case_status": "Active",
            "otn": "U4321",
            "dob": "01/01/1950",
            "participants": "Rabbit, Bunny"
        },
        [...]
    ],
    errors: ['descriptive errors, if there were any.']

}
```

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
