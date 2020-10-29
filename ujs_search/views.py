from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import status
import logging
from . import appsettings
from .serializers import NameSearchSerializer, DocketSearchSerializer
from .services import searchujs

logger = logging.getLogger(__name__)

# class SearchName(APIView):
class SearchName(generics.CreateAPIView):

    queryset = []
    serializer_class = NameSearchSerializer
    permission_classes = appsettings.PERMISSION_CLASSES

    def get(self, request, *args, **kwargs):
        try:
            to_search = NameSearchSerializer(data=request.query_params)
            if to_search.is_valid():
                # search ujs portal for a name.
                # and return the results.
                results, errs = searchujs.search_by_name(**to_search.validated_data)
                return Response({"searchResults": results, "errors": errs})
            else:
                return Response(
                    {"errors": to_search.errors}, status.HTTP_400_BAD_REQUEST
                )
        except Exception as ex:
            return Response({"errors": [str(ex)]})

    def post(self, request, *args, **kwargs):
        try:
            to_search = NameSearchSerializer(data=request.data)
            if to_search.is_valid():
                # search ujs portal for a name.
                # and return the results.
                results, errs = searchujs.search_by_name(**to_search.validated_data)
                return Response({"searchResults": results, "errors": errs})
            else:
                return Response(
                    {"errors": to_search.errors}, status.HTTP_400_BAD_REQUEST
                )
        except Exception as ex:
            return Response({"errors": [str(ex)]})


class SearchDocket(generics.CreateAPIView):

    queryset = []
    serializer_class = DocketSearchSerializer
    permission_classes = appsettings.PERMISSION_CLASSES

    def post(self, request, *args, **kwargs):
        try:
            search_data = DocketSearchSerializer(data=request.data)
            if search_data.is_valid():
                search_data = search_data.validated_data
                docket_number = search_data["docket_number"]
                results, errs = searchujs.search_by_docket(docker_number)
                return Response({"searchResults": results, "errors": errs})
            else:
                return Response({"errors": search_data.errors})

        except Exception as ex:
            return Response({"errors": [str(ex)]})
