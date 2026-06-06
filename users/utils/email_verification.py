import secrets
import hashlib

from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from ..utils.send_email import send_email
from ..emails.verify_email_template import (verify_email_template)

def send_verification_email(user):
    raw_token = secrets.token_urlsafe(32)

    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

    user.email_verification_token = hashed_token
    user.email_verification_expire = timezone.now() + timedelta(minutes=15)

    user.save()

    verification_url = (f"{settings.BACKEND_URL}" f"/auth/verify-email/?token={raw_token}")

    send_email(user.email,"Verify your email",verify_email_template(verification_url))

    return verification_url