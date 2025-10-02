import smtplib, os, traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # App password
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", 587))

def send_email_with_pdf(receiver_email, subject, body, pdf_path):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = receiver_email
        msg["Subject"] = subject

        # Body
        msg.attach(MIMEText(body, "plain"))

        # Attach PDF
        with open(pdf_path, "rb") as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
            pdf_attachment.add_header(
                "Content-Disposition", "attachment", filename=os.path.basename(pdf_path)
            )
            msg.attach(pdf_attachment)

        # Send email
        with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, receiver_email, msg.as_string())

        print("✅ Email sent successfully!")
        return True

    except Exception as e:
        print("❌ Email send failed!")
        print(traceback.format_exc())   # 🔥 Print full error details
        return False
    
    
from email_utils import send_email_with_pdf

send_email_with_pdf(
    "your_receiver_email@gmail.com",
    "Helmet Report Test",
    "This is a test email with a PDF attachment.",
    "helmet_report.pdf"
)
