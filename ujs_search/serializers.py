from rest_framework import serializers as S

class NameSearchSerializer(S.Serializer):
    """ 
    Validate json that is asking for a search of a particular name on ujs.
    """
    first_name = S.CharField(required=True)
    last_name = S.CharField(required=True)
    dob = S.DateField(required=False, default=None)

class DocketSearchSerializer(S.Serializer):
    """
    Validata json asking to search for a particular docket number.
    """
    docket_number = S.CharField(required=True)
