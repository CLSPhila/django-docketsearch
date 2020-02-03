from django.conf import settings
from rest_framework import permissions

PERMISSION_CLASSES = getattr(settings, "UJS_SEARCH_PERMISSION_CLASSES", [permissions.IsAuthenticated] )
TIMELIMIT = getattr(settings, "UJS_REQUEST_TIMELIMIT", float("Inf"))