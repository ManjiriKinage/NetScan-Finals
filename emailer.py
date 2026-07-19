import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_report(sender, password, receiver, file_path):
    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = receiver
        msg["Subject"] = "NetScan Security Report"

        msg.attach(MIMEText("Please find attached report."))

        with open(file_path, "rb") as f:
            attach = MIMEText(f.read(), "base64", "utf-8")
            attach.add_header(
                "Content-Disposition",
                "attachment",
                filename="report.pdf"
            )
            msg.attach(attach)

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
        server.login(sender, password)
        server.send_message(msg)
        server.quit()

        return True

    except Exception as e:
        return str(e)