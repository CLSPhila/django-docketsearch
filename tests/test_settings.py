SECRET_KEY = "fake-key"
DEBUG = True
REST_FRAMEWORK = {
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

INSTALLED_APPS = [
    "rest_framework",
    "ujs_search",
]

EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
