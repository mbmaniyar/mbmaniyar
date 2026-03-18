# 📧 Localhost Mail Setup Guide

## 🎯 **Quick Fix for Testing**

Since you're not receiving emails on localhost, I've added **console OTP display**. The OTP will now show in your terminal when you request a password reset.

---

## 🔐 **How to Test OTP System**

### **Step 1: Request OTP**
1. Go to: `http://localhost:5000/forgot-password-otp`
2. Enter any email (e.g., `test@mbmaniyar.com`)
3. Click "Send OTP"

### **Step 2: Get OTP from Console**
Look at your terminal where the server is running. You'll see:

```
🔐 OTP FOR TESTING: 123456
📧 Email: test@mbmaniyar.com
👤 User: Test Customer
⏰ Expires in 10 minutes
==================================================
```

### **Step 3: Enter OTP**
1. Enter the 6-digit code from console
2. Click "Verify OTP"
3. Reset your password

---

## 🛠️ **Optional: Configure Mail for Localhost**

If you want to receive actual emails on localhost, you can use a test email service:

### **Option 1: Use Brevo (Recommended)**
1. Sign up for free Brevo account: https://www.brevo.com/
2. Get SMTP credentials
3. Add to your `.env` file:

```bash
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USERNAME=your-brevo-username
MAIL_PASSWORD=your-brevo-password
MAIL_DEFAULT_SENDER=M.B Maniyar <your-email@gmail.com>
MAIL_ENABLED=true
```

### **Option 2: Use Mailtrap (Testing)**
1. Sign up for free Mailtrap: https://mailtrap.io/
2. Get SMTP credentials
3. Add to your `.env` file:

```bash
MAIL_SERVER=smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=your-mailtrap-username
MAIL_PASSWORD=your-mailtrap-password
MAIL_DEFAULT_SENDER=M.B Maniyar <test@mbmaniyar.com>
MAIL_ENABLED=true
```

---

## 🎯 **For Now: Use Console OTP**

The easiest way to test is to use the console OTP display:

✅ **No email configuration needed**  
✅ **Instant OTP access**  
✅ **Perfect for testing**  
✅ **Shows all details** (OTP, email, user, expiry)

---

## 🧪 **Test Flow**

1. **Request OTP** → Check console for code
2. **Enter OTP** → Use console code
3. **Reset Password** → Test new password
4. **Login** → Verify it works

---

## 📊 **What You'll See in Console**

```
🔐 OTP FOR TESTING: 123456
📧 Email: test@mbmaniyar.com
👤 User: Test Customer
⏰ Expires in 10 minutes
==================================================
```

Or if email fails:

```
🔐 OTP FOR TESTING (email failed): 123456
📧 Email: test@mbmaniyar.com
👤 User: Test Customer
⏰ Expires in 10 minutes
==================================================
```

---

## 🎉 **Ready to Test!**

1. **Server is running** ✅
2. **Console OTP enabled** ✅  
3. **Beautiful OTP interface** ✅
4. **No email setup required** ✅

**Go test your OTP system now!** 🚀

The OTP will always appear in your console for easy testing! 📱✨
