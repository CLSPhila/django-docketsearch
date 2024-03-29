import re
from rest_framework import serializers as S


court_pattern = re.compile(r"^(?:CP|MDJ|both)$", re.I)


class NameSearchSerializer(S.Serializer):
    """
    Validate json that is asking for a search of a particular name on ujs.
    """

    first_name = S.CharField(required=True)
    last_name = S.CharField(required=True)
    dob = S.DateField(
        required=False, default=None, input_formats=["iso-8601", r"%m/%d/%Y"]
    )


class DocketSearchSerializer(S.Serializer):
    """
    Validata json asking to search for a particular docket number.
    """

    docket_number = S.CharField(required=True)


class MultipleDocketSearchSerializer(S.Serializer):
    """
    Validata json asking to search for a particular docket number.
    """

    docket_numbers = S.ListField(child=S.CharField(required=True), allow_empty=True)
