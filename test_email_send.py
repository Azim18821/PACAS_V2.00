"""
Test Email Sending Script - SMTP Version
Sends a verification email to test the SMTP integration
"""

import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)  # Force override any existing env vars

def send_test_email(email):
    """Send a test verification email via SMTP"""
    # Generate random 6-digit code
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    # SMTP configuration
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    sender_email = os.getenv('SENDER_EMAIL', '')
    sender_password = os.getenv('SENDER_PASSWORD', '')
    sender_name = os.getenv('SENDER_NAME', 'PacasHomes')
    
    print(f"\n🔍 Debug - Loaded from .env:")
    print(f"   SENDER_EMAIL env var: {sender_email}")
    print(f"   SMTP_SERVER env var: {smtp_server}")
    
    if not sender_email:
        print("❌ ERROR: SENDER_EMAIL not found in .env file")
        return False
    
    if not sender_password:
        print("❌ ERROR: SMTP password not configured in .env file")
        print("   Set SENDER_PASSWORD in your .env file")
        return False
    
    # Email HTML content
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center;">
                <h1 style="color: white; margin: 0;">Email Verification</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9; border-radius: 10px; margin-top: 20px;">
                <p style="font-size: 16px; color: #333;">Thank you for creating an account with PacasHomes!</p>
                <p style="font-size: 16px; color: #333;">Your verification code is:</p>
                <div style="background: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                    <h2 style="color: #667eea; font-size: 32px; letter-spacing: 5px; margin: 0;">{code}</h2>
                </div>
                <p style="font-size: 14px; color: #666;">This code will expire in 10 minutes.</p>
                <p style="font-size: 14px; color: #666;">If you didn't request this code, please ignore this email.</p>
                <p style="font-size: 14px; color: #999; margin-top: 20px;"><strong>This is a test email.</strong></p>
            </div>
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2026 Aztura LTD trading as PacasHomes. All rights reserved.</p>
                <p style="margin-top: 5px;">Company No: 16805710</p>
            </div>
        </body>
    </html>
    """
    
    # Plain text version
    text_content = f"""
    Email Verification
    
    Thank you for creating an account with PacasHomes!
    
    Your verification code is: {code}
    
    This code will expire in 10 minutes.
    
    If you didn't request this code, please ignore this email.
    
    This is a test email.
    
    © 2026 Aztura LTD trading as PacasHomes. All rights reserved.
    Company No: 16805710
    """
    
    # Create email message
    message = MIMEMultipart('alternative')
    message['Subject'] = "TEST: Verify Your Email - PacasHomes"
    message['From'] = f"{sender_name} <{sender_email}>"
    message['To'] = email
    
    # Attach plain text and HTML versions
    part1 = MIMEText(text_content, 'plain')
    part2 = MIMEText(html_content, 'html')
    message.attach(part1)
    message.attach(part2)
    
    print(f"\n📧 Sending test email to: {email}")
    print(f"   From: {sender_name} <{sender_email}>")
    print(f"   Server: {smtp_server}:{smtp_port}")
    print(f"   Verification Code: {code}")
    print(f"\n⏳ Connecting to SMTP server...")
    
    try:
        # Send email via SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Enable TLS encryption
            print(f"✓ TLS encryption enabled")
            server.login(sender_email, sender_password)
            print(f"✓ Logged in successfully")
            server.send_message(message)
            print(f"✓ Message sent")
        
        print(f"\n✅ SUCCESS! Email sent to {email}")
        print(f"   Check your inbox (and spam folder)")
        print(f"   Verification code: {code}")
        return True
            
    except smtplib.SMTPAuthenticationError:
        print(f"\n❌ AUTHENTICATION FAILED")
        print(f"   Check SENDER_EMAIL and SENDER_PASSWORD in .env")
        print(f"   For Gmail, you need an 'App Password', not your regular password")
        print(f"   Generate one at: https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    # Test email address
    test_email = "azim10109@gmail.com"
    
    print("=" * 60)
    print("  SMTP EMAIL TEST")
    print("=" * 60)
    
    send_test_email(test_email)
    
    print("\n" + "=" * 60)
