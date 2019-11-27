from rest_framework.response import Response 
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework import status
import logging
from django.conf import settings
from .serializers import NameSearchSerializer
from .services import searchujs


logger = logging.getLogger(__name__)

class SearchName(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            to_search = NameSearchSerializer(data=request.data)
            if to_search.is_valid():
                # search ujs portal for a name.
                # and return the results.
                results = searchujs.search_by_name(**to_search.validated_data)
                return Response({
                    "searchResults": results
                })
            else:
                return Response({
                    "errors": to_search.errors
                }, status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({
                "errors": [str(ex)]
            })

