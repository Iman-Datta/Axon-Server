import secrets
import hashlib

from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from ..utils.send_email import send_email
from ..emails.verify_email_template import (verify_email_template)
from ..emails.otp_email_template import otp_email_template

def send_magicLink_email(user):
    raw_token = secrets.token_urlsafe(32)

    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

    user.email_verification_token = hashed_token
    user.email_verification_expire = timezone.now() + timedelta(minutes=15)

    user.save()

    verification_url = (f"{settings.BACKEND_URL}" f"/auth/verify-email/?token={raw_token}")

    send_email(user.email,"Verify your email",verify_email_template(verification_url))

    return verification_url

def send_email_otp(user, email):
    otp = str(secrets.randbelow(900000) + 100000)

    hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
    
    user.email_otp_hash = hashed_otp
    user.email_otp_expire = (timezone.now() + timedelta(minutes=10))
    user.pending_email = email

    user.save(
        update_fields=[
            "email_otp_hash",
            "email_otp_expire",
            "pending_email"
        ]
    )

    send_email(
        email, "Your Axon verification code", otp_email_template(otp)
    )
