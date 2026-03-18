# 🔐 OTP Password Reset System - Deployment Guide

## 🎯 **What's New**

Your forgot password system now uses **OTP (One-Time Password)** instead of email links, providing better security and user experience.

---

## 🚀 **New Features**

### **📱 OTP-Based Reset**
- **6-digit OTP** sent to email
- **10-minute expiry** for security
- **Beautiful UI** with step-by-step flow
- **Professional email templates** with your branding

### **🎨 Consistent Design**
- **Same M.B Maniyar branding** across all pages
- **Beautiful gradient backgrounds**
- **Professional email templates**
- **Mobile-responsive design**

---

## 📋 **Deployment Steps**

### **Step 1: Database Update**
Add OTP columns to your users table on Render:

```sql
-- Add OTP columns if they don't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS reset_otp VARCHAR(64),
ADD COLUMN IF NOT EXISTS reset_otp_expiry TIMESTAMP;
```

### **Step 2: Environment Variables**
Set these in your Render dashboard:

```bash
# Mail settings (already configured)
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USERNAME=your-brevo-username
MAIL_PASSWORD=your-brevo-password
MAIL_DEFAULT_SENDER=M.B Maniyar <your-email@gmail.com>
MAIL_ENABLED=true

# Secret key (already configured)
SECRET_KEY=your-secret-key
```

### **Step 3: Code Deployment**
All code is ready! Just push to GitHub and Render will auto-deploy.

---

## 🧪 **Testing Your OTP System**

### **1. Test OTP Flow**
1. Go to: `your-site.onrender.com/login`
2. Click "Forgot password?"
3. Enter email/phone: `test@mbmaniyar.com`
4. Check email for 6-digit OTP
5. Enter OTP and reset password

### **2. Test Email Templates**
- **Beautiful HTML emails** with your branding
- **Security notices** and expiry information
- **Professional layout** with M.B Maniyar styling

### **3. Test Security Features**
- **10-minute OTP expiry**
- **SHA-256 OTP hashing**
- **Secure password reset flow**
- **No plain text storage**

---

## 🎨 **What Your Users Will See**

### **Step 1: Enter Email/Phone**
```
🔐 Forgot Password?
Enter your email or phone to receive OTP

[test@mbmaniyar.com]
[Send OTP →]
```

### **Step 2: Enter OTP**
```
🔐 Enter OTP
We've sent a 6-digit code to your email/phone

[1] [2] [3] [4] [5] [6]
Resend OTP in 2:00
[Verify OTP →]
```

### **Step 3: Reset Password**
```
🔐 Reset Password
Enter your new password below

[New Password] 👁
[Confirm Password] 👁
[Reset Password →]
```

---

## 📧 **Email Template Preview**

Your customers will receive beautiful emails like this:

```
🔐 Password Reset OTP
M.B Maniyar Cloth Store

Hello Test Customer,

You requested to reset your password for your M.B Maniyar account. 
Use the OTP code below to proceed:

┌─────────────────────────────────┐
│      Your OTP code is:          │
│                                 │
│         1 2 3 4 5 6             │
│                                 │
│    This code expires in 10 minutes │
└─────────────────────────────────┘

🔒 Security Notice: Never share this OTP with anyone.

Best regards,
The M.B Maniyar Team
```

---

## 🔒 **Security Features**

### **OTP Security**
- **SHA-256 hashing** of OTP codes
- **10-minute expiry** automatic cleanup
- **Rate limiting** ready (implement if needed)
- **Secure random generation**

### **Email Security**
- **Professional templates** with security notices
- **No OTP in subject line** (email security)
- **Expiry warnings** in emails
- **Brand consistency** throughout

---

## 🌐 **URL Structure**

### **New Endpoints**
- `/forgot-password-otp` - OTP request page
- `/verify-otp` - OTP verification
- `/reset-password-otp/<user_id>` - Password reset

### **Old Endpoint (Still Available)**
- `/forgot-password` - Traditional email link method

---

## 🎯 **Benefits Over Email Links**

### **Better Security**
- **No clickable links** in emails (phishing protection)
- **Short expiry time** (10 minutes vs 1 hour)
- **Verification required** before password change

### **Better UX**
- **Instant access** - no need to check email links
- **Mobile friendly** - easy OTP entry
- **Clear feedback** at each step

### **Professional Appearance**
- **Modern authentication flow**
- **Consistent branding**
- **Beautiful email templates**

---

## 🆘 **Troubleshooting**

### **OTP Not Received**
- Check spam folder
- Verify MAIL settings on Render
- Check email address validity

### **OTP Expired**
- OTP expires in 10 minutes
- User can request new OTP
- Previous OTP becomes invalid

### **Database Issues**
- Run the SQL migration above
- Check if columns exist
- Verify database connection

---

## 🎉 **Ready for Production!**

Your OTP password reset system is:
- ✅ **Fully functional** with beautiful UI
- ✅ **Secure** with proper OTP handling
- ✅ **Professional** with branded emails
- ✅ **Mobile responsive** for all devices
- ✅ **Consistent** with your M.B Maniyar branding

---

## 📞 **Need Help?**

If you encounter issues:
1. **Check environment variables** on Render
2. **Verify database columns** were added
3. **Test email delivery** with a real email
4. **Check logs** in Render dashboard

**Your customers will love the new OTP password reset experience!** 🚀
