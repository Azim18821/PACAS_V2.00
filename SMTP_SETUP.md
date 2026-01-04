# SMTP Email Setup Guide

## ✅ SMTP Switch Complete

The email system has been successfully switched from MailerSend API to SMTP.

## 🔧 Current Status

- **Code Updated**: ✅ main.py now uses SMTP
- **Test Script**: ✅ test_email_send.py ready
- **Configuration Needed**: ⚠️ Valid SMTP credentials required

## 📧 SMTP Options

### Option 1: Gmail SMTP (Recommended for Testing)

**Setup Steps:**
1. Go to your Google Account: https://myaccount.google.com
2. Enable 2-Factor Authentication (Security → 2-Step Verification)
3. Generate App Password:
   - Visit: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "PacasHomes" and click Generate
   - Copy the 16-character password (e.g., "abcd efgh ijkl mnop")

4. Update `.env` file:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-gmail@gmail.com
SENDER_PASSWORD=abcdefghijklmnop  # 16-char app password (no spaces)
SENDER_NAME=PacasHomes
```

**Pros:**
- Free and reliable
- No domain verification needed
- Can send to any email address immediately

**Cons:**
- Sending limit: 500 emails/day
- Sender shows your Gmail address

---

### Option 2: Outlook/Hotmail SMTP

**Setup:**
```env
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SENDER_EMAIL=your-email@outlook.com
SENDER_PASSWORD=your-outlook-password
SENDER_NAME=PacasHomes
```

**Limits:**
- 300 emails/day
- May require app password if 2FA enabled

---

### Option 3: MailerSend SMTP

**Note:** The credentials in your `.env` appear to be from a trial account that may have expired.

**To use MailerSend SMTP:**
1. Login to MailerSend dashboard
2. Go to Settings → SMTP
3. Generate new SMTP credentials
4. Update `.env`:
```env
SMTP_SERVER=smtp.mailersend.net
SMTP_PORT=587
SENDER_EMAIL=your-mailersend-email
SENDER_PASSWORD=your-mailersend-password
SENDER_NAME=PacasHomes
```

---

## 🧪 Testing

After updating `.env` with valid credentials:

```bash
python test_email_send.py
```

This will send a test email to `azim10109@gmail.com` with a verification code.

---

## 🚀 What Changed

### Before (MailerSend API):
- Required domain verification
- Couldn't send to unverified domains
- Used HTTP API calls

### After (SMTP):
- No domain verification needed
- Can send to any email address
- Uses standard SMTP protocol
- Works with any SMTP provider (Gmail, Outlook, MailerSend, etc.)

---

## 📝 Next Steps

1. **Choose SMTP provider** (Gmail recommended for quick testing)
2. **Generate credentials** (app password for Gmail)
3. **Update `.env` file** with your credentials
4. **Run test**: `python test_email_send.py`
5. **Check email** at azim10109@gmail.com

---

## 🔒 Security Notes

- **Never commit `.env` to Git** (already in .gitignore)
- Use **App Passwords**, not your main account password
- For production, consider dedicated email service
- Current daily limits are fine for verification emails

---

## ✉️ Email Template

The email includes:
- **Company**: Aztura LTD trading as PacasHomes
- **Company No**: 16805710
- **6-digit verification code**
- **10-minute expiration notice**
- Professional gradient header
- Mobile-responsive design
