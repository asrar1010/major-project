from flask import Flask, request, send_file, jsonify
import requests
import smtplib
from email.mime.text import MIMEText
import yaml
import os


# ---------------- Load Config ---------------- #
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

SERVERS = config["servers"]

app = Flask(__name__)
waiting_emails = set()
GMAIL_ADDRESS = "your_gmail@gmail.com"  
GMAIL_PASSWORD = "your_app_password"    
CAPACITY_HTML_PATH = os.path.join(os.path.dirname(__file__), "capacity.html")


def send_email(to, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = to
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, to, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")


def notify_recovery():
    """Called by load_balancer when servers recover."""
    if waiting_emails:
        for email in list(waiting_emails):
            send_email(email, "Server is back online!", "Our services are up and running now!!. Thanks for your patience")
        waiting_emails.clear()

@app.route("/")
def capacity_page():
    return send_file(CAPACITY_HTML_PATH)

@app.route("/notify", methods=["POST"])
def notify():
    email = request.form.get("email")
    if email:
        waiting_emails.add(email)
    return jsonify({"message": "You will be notified when servers are back online!"}), 200

@app.route("/recover", methods=["POST"])
def recover():
    """Called by load_balancer when servers recover."""
    notify_recovery()
    return jsonify({"message": "Recovery emails sent!"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
