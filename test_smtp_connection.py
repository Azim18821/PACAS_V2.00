"""
SMTP Diagnostic Tool
Tests SMTP connection and authentication separately
"""

import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
smtp_port = int(os.getenv('SMTP_PORT', '587'))
sender_email = os.getenv('SENDER_EMAIL', '')
sender_password = os.getenv('SENDER_PASSWORD', '')

print("=" * 60)
print("  SMTP DIAGNOSTIC TEST")
print("=" * 60)
print(f"\n📋 Configuration:")
print(f"   Server: {smtp_server}")
print(f"   Port: {smtp_port}")
print(f"   Email: {sender_email}")
print(f"   Password: {'*' * min(len(sender_password), 20)} ({len(sender_password)} chars)")

print(f"\n⏳ Step 1: Connecting to SMTP server...")
try:
    server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
    print(f"   ✅ Connected successfully")
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    exit(1)

print(f"\n⏳ Step 2: Starting TLS encryption...")
try:
    server.starttls()
    print(f"   ✅ TLS enabled")
except Exception as e:
    print(f"   ❌ TLS failed: {e}")
    server.quit()
    exit(1)

print(f"\n⏳ Step 3: Authenticating...")
try:
    server.login(sender_email, sender_password)
    print(f"   ✅ Authentication successful!")
    print(f"\n✅ ALL TESTS PASSED - SMTP is ready to send emails")
    server.quit()
except smtplib.SMTPAuthenticationError as e:
    print(f"   ❌ Authentication failed: {e}")
    print(f"\n💡 Possible solutions:")
    print(f"   1. Check if password is correct in MailerSend dashboard")
    print(f"   2. Regenerate SMTP password in MailerSend Settings → SMTP")
    print(f"   3. Verify domain is added in MailerSend")
    print(f"   4. Try using trial email: MS_xxxxx@trial-xxxxx.mlsender.net")
    server.quit()
except Exception as e:
    print(f"   ❌ Error: {e}")
    server.quit()

print("=" * 60)
