import hashlib

from django.utils import timezone
from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...serializers import (EmailOTPRequestSerializer, EmailOTPVerifySerializer)
from ...utils.email_verification import send_email_otp

@api_view(["POST"])
def 