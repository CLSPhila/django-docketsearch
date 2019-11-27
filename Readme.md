# django-docketsearch

A Django Rest Framework app that adds endpoints useful for searching the PA UJS portal for public records.

## Getting started

1. Add "ujs" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'ujs_search',
    ]

2. Include the ujs_search URLconf in your project urls.py like this::

    path('ujs/', include('ujs_search.urls')),


## Testing

Test with `pytest --log-cli-level info` (include the switch to see helpful logging info)

## Additional Information

This project began as an app in [RecordLib](https://github.com/CLSPhila/RecordLib).