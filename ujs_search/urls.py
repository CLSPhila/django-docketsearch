from django.urls import path
from .views import *

urlpatterns = [
    path("search/name/", SearchName.as_view()),
    path("search/docket/", SearchDocket.as_view()),
    path("search/docket/many/", SearchMultipleDockets.as_view()),
]