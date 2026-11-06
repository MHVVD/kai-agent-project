import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(recipient_email: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_summary_email(recipient_email: str, report_image_path: str, summary_data: dict):
    subject = "Your KAI Bi-Weekly Summary"
    body = f"Here is your activity summary:\n- Fitness: {summary_data.get('Fitness', 0)}\n- Health: {summary_data.get('Health', 0)}"
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        with open(report_image_path, 'rb') as fp:
            img = MIMEImage(fp.read())
            img.add_header('Content-Disposition', 'attachment', filename='report.png')
            msg.attach(img)
    except FileNotFoundError:
        print("Could not find report image to attach.")
    send_email(recipient_email, subject, msg.as_string())