from rest_framework import serializers as S

class NameSearchSerializer(S.Serializer):
    """ 
    Validate json that is asking for a search of a particular name on ujs.
    """
    first_name = S.CharField(required=True)
    last_name = S.CharField(required=True)
    dob = S.DateField(required=False, default=None)

