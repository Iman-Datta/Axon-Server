from functools import wraps
from rest_framework.response import Response


def github_connected(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user

        if not user.github_id or not user.github_access_token:
            return Response({
                    "success": False,
                    "message": "GitHub account is not connected."
                },status=400)
        
        return view_func(request, *args, **kwargs)

    return wrapper