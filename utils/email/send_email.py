import smtplib

from email.message import Message

from django.conf import settings

from .templates_email import password_templates_email
from .valid_email import verify_email_is_valid


def send_email_first_access_password(user_name, university_name, recipient_email, link_to_reset_password_page):
    title, text_body = password_templates_email.template_email_first_access(
        user_name, university_name, link_to_reset_password_page
    )

    verify_email_is_valid(recipient_email)

    send_email(recipient_email, title, text_body)


def send_email_reset_password(user_name, recipient_email, link_to_reset_password_page):
    title, text_body = password_templates_email.template_email_recovery_password(
        user_name, link_to_reset_password_page
    )

    verify_email_is_valid(recipient_email)
    send_email(recipient_email, title, text_body)


def send_email_reset_password_by_admin(user_name, recipient_email, link_to_reset_password_page):
    title, text_body = password_templates_email.template_email_recovery_password_by_admin(
        user_name, link_to_reset_password_page
    )

    verify_email_is_valid(recipient_email)
    send_email(recipient_email, title, text_body)


def send_email(recipient_email: str, title: str, text_body: str):
    try:
        msg = Message()
        msg["Subject"] = title
        msg["From"] = settings.SMTP_EMAIL_USER
        msg["To"] = recipient_email
        msg.add_header("Content-Type", "text/html")
        msg.set_payload(text_body)

        s = smtplib.SMTP(settings.SMTP_EMAIL_SERVER, settings.SMTP_EMAIL_PORT)
        s.starttls()

        s.login(msg["From"], settings.SMTP_EMAIL_PASSWORD)
        s.sendmail(msg["From"], [msg["To"]], msg.as_string().encode("utf-8"))
    except Exception as error:
        raise Exception(f"Error Send Email: {str(error)}")
