import resend

from django.conf import settings


resend.api_key = settings.RESEND_API_KEY


def send_email(
    to_email,
    subject,
    html
):

    params = {
        "from": settings.RESEND_SENDER_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html
    }

    resend.Emails.send(params)