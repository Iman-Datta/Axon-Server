def otp_email_template(otp):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0; padding:0; background-color:#f4f4f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f5; padding:40px 0;">
        <tr>
          <td align="center">
            <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.08);">

              <!-- Header -->
              <tr>
                <td style="background-color:#0d1117; padding:36px 40px;">
                  <span style="color:#ffffff; font-size:24px; font-weight:700; letter-spacing:0.3px;">Axon</span>
                </td>
              </tr>

              <!-- Body -->
              <tr>
                <td style="padding:40px;">
                  <h2 style="margin:0 0 20px 0; font-size:26px; font-weight:600; color:#0d1117;">
                    Verify your email
                  </h2>

                  <p style="margin:0 0 28px 0; font-size:15px; line-height:1.6; color:#3f3f46;">
                    Use the verification code below to confirm your Axon account. This code is valid for
                    <strong>10 minutes</strong> and can only be used once.
                  </p>

                  <!-- OTP box -->
                  <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                      <td align="center" style="background-color:#161b22; border-radius:8px; padding:24px;">
                        <span style="font-size:36px; font-weight:700; letter-spacing:10px; color:#ffffff; font-family: 'Courier New', monospace;">
                          {otp}
                        </span>
                      </td>
                    </tr>
                  </table>

                  <p style="margin:28px 0 0 0; font-size:15px; line-height:1.6; color:#3f3f46;">
                    If you did not request this code, you can safely ignore this email. No action is required.
                  </p>

                  <hr style="border:none; border-top:1px solid #e4e4e7; margin:32px 0;">

                  <p style="margin:0 0 24px 0; font-size:13px; line-height:1.6; color:#a1a1aa;">
                    This email was sent because a sign-in was requested for your Axon account.
                    If this wasn't you, no action is required.
                  </p>

                  <p style="margin:0 0 12px 0; font-size:13px; color:#a1a1aa;">
                    Axon — Built by Iman Datta
                  </p>

                  <p style="margin:0; font-size:13px;">
                    <a href="https://github.com/Iman-Datta" style="color:#3f3f46; text-decoration:none; margin-right:16px;">GitHub Profile</a>
                    <a href="https://www.linkedin.com/in/iman-datta-161615307/" style="color:#3f3f46; text-decoration:none;">LinkedIn</a>
                  </p>
                </td>
              </tr>

            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """