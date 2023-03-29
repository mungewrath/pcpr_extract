import sys
import smtplib, ssl
import email
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_mail(login, send_to, filename):
    frm = login[0]

    body = "Hi! We hope this email finds you well. Your pathology report summary is attached."

    subject = f"Subject: 'Patient Centered Pathology Report"

    context = ssl.create_default_context()

    message = MIMEMultipart()
    message["From"] = frm
    message["To"] = send_to
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))
    with open('tmp/' + filename, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    with smtplib.SMTP_SSL('smtp.uw.edu', 465, context=context) as server:
        server.login(frm, login[1])
        server.sendmail(frm, send_to, text)
        server.close()
    return None