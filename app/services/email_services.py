from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig, NameEmail

from app.core import get_settings

settings = get_settings()


conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS
)


async def send_otp_email(email: NameEmail, otp: str, retries: int = 3, delay: int = 5):

    message = MessageSchema(
        subject="Your OTP Code",
        recipients=[email],
        body=f"""
            Hello {email.name},

            Your OTP is: {otp}

            This code is valid for 5 minutes.

            If you did not request this, ignore this email.
            """,
        subtype=MessageType.plain,
    )

    fm = FastMail(config=conf)
    await fm.send_message(message=message)

    # for attempt in range(1, retries+1):
    #     try:
    #         await fm.send_message(message=message)
    #         return
    #     except (ConnectionErrors) as e:

    #         if attempt <= retries:
    #             await asyncio.sleep(delay)  # retry after sleep for some time
    #         else:
    #             raise HTTPException(
    #                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                 detail="Error sending email"
    #             )
