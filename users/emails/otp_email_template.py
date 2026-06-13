def otp_email_template(otp):

    return f"""
        <div>
            <h2>Axon Email Verification</h2>

            <p>Your verification code is:</p>

            <h1>{otp}</h1>

            <p>This code expires in 10 minutes.</p>

            <p>If you did not request this, ignore this email.</p>
        </div>
    """