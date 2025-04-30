from flask import Flask, request
import subprocess
import hmac
import hashlib
import os

app = Flask(__name__)
SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")  # Set this in your .env

@app.route("/webhook", methods=["POST"])
def webhook():
    header_signature = request.headers.get('X-Hub-Signature-256')
    if SECRET:
        sha_name, signature = header_signature.split('=')
        mac = hmac.new(SECRET.encode(), msg=request.data, digestmod=hashlib.sha256)
        if not hmac.compare_digest(mac.hexdigest(), signature):
            return 'Unauthorized', 401

    # Run pull + restart
    subprocess.run([
        'bash', '-c',
        'cd /home/vozter/TakoNautBot && git pull origin main && sudo systemctl restart takonaut.service'
    ])

    return 'OK', 200
