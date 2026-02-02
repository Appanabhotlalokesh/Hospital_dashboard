import json
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()
def send_email(event, context):
    try:
        body = json.loads(event["body"])

        to_emails = body["to"]
        subject = body["subject"]
        message = body["message"]

        EMAIL_USER = os.environ.get("lokeshappanabhotla@gmail.com")
        EMAIL_PASS = os.environ.get("Anr_1973")

        msg = EmailMessage()
        msg["From"] = EMAIL_USER
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject
        msg.set_content(message)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()

        return {
            "statusCode": 200,
            "body": json.dumps({"success": True})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
