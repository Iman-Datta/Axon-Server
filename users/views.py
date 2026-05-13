from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import RegisterSerializer

@api_view(['POST'])
def register_view(request):

    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():

        user = serializer.save()

        return Response(
            {
                "message": "Account created successfully",
                "email": user.email,
                "success": True
            },
            status=201
        )

    return Response(serializer.errors,status=400)