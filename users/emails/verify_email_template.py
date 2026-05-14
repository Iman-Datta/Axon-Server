def verify_email_template(verification_url):

    return f"""
        <h2>Verify Your Email</h2>

        <p>
            Click below to verify your account:
        </p>

        <a href="{verification_url}">
            Verify Email
        </a>
    """