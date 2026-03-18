# 🗄️ Step 2: Database Update Guide for Render

## 🎯 What You Need to Do
Add the new OTP columns to your existing users table on Render PostgreSQL.

---

## 🚀 Method 1: Render Dashboard (Easiest)

### 1. Go to Your Render Dashboard
1. Login to [render.com](https://render.com)
2. Go to your **M B Maniyar** service
3. Click on **"PostgreSQL"** tab

### 2. Open Query Editor
1. Click **"Query"** button
2. You'll see a SQL editor interface
3. Copy and paste the commands below

### 3. Run These SQL Commands
```sql
-- Add OTP columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS reset_otp VARCHAR(6);

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS reset_otp_expiry TIMESTAMP;
```

### 4. Verify Changes
Run this to verify:
```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' 
  AND column_name IN ('reset_otp', 'reset_otp_expiry');
```

You should see both columns listed.

---

## 🛠️ Method 2: Command Line (Advanced)

### 1. Get Connection Details
1. Go to Render Dashboard → PostgreSQL service
2. Click **"Connect"** → **"External Connection"**
3. Copy the **Connection URI**

### 2. Connect Using psql
```bash
# Install psql if needed
brew install postgresql  # Mac
sudo apt-get install postgresql-client  # Ubuntu

# Connect to database
psql "your-connection-uri-here"
```

### 3. Run SQL Commands
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_otp VARCHAR(6);
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_otp_expiry TIMESTAMP;
```

---

## 🔍 Method 3: GUI Tools (pgAdmin, DBeaver)

### 1. Download Database Client
- **pgAdmin**: [https://www.pgadmin.org/](https://www.pgadmin.org/)
- **DBeaver**: [https://dbeaver.io/](https://dbeaver.io/)

### 2. Connect
1. Install and open the tool
2. Create new connection with Render credentials
3. Connect to your database

### 3. Execute SQL
1. Open SQL query editor
2. Paste and run:
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_otp VARCHAR(6);
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_otp_expiry TIMESTAMP;
```

---

## ✅ Verification Steps

### Check if Columns Were Added
```sql
-- Describe the users table
\d users

-- Or check specific columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
  AND column_name IN ('reset_otp', 'reset_otp_expiry');
```

### Expected Output
You should see:
| column_name       | data_type |
|------------------|------------|
| reset_otp        | varchar    |
| reset_otp_expiry | timestamp  |

---

## 🚨 Important Notes

### ⚠️ Backup First
Always backup your database before making changes:
```sql
-- Create backup
CREATE TABLE users_backup AS SELECT * FROM users;
```

### ⚠️ Use IF NOT EXISTS
The `IF NOT EXISTS` clause makes the command safe to run multiple times.

### ⚠️ No Data Loss
These commands only ADD columns - they won't delete any existing data.

---

## 🎯 After Database Update

Once you've added the columns:

### 1. ✅ Test OTP System
- Go to: `your-app.onrender.com/forgot-password-otp`
- Try password reset with any user email
- Check if OTP is generated and stored

### 2. ✅ Test Admin Panel
- Login as admin
- Go to: `your-app.onrender.com/admin/users`
- Verify you can see password hashes and logs

### 3. ✅ Test Email Notifications
- Login as any user → Should get security email
- Reset password → Should get OTP email

---

## 🆘️ Troubleshooting

### Error: Column Already Exists
If you get "column already exists":
- That's OK! It means the columns are already there
- Continue to testing

### Error: Permission Denied
- Check your database user has ALTER TABLE permissions
- Use the Render dashboard owner account

### Error: Connection Failed
- Verify your connection string
- Check if your IP is allowed (if using external access)

---

## 📞 Need Help?

If you're stuck:
1. **Screenshot the error** and share it
2. **Tell me which method** you're using (Dashboard, CLI, GUI)
3. **Show me the exact error message**

---

## ✅ Success!

Once you see both columns in the users table, your database is ready!

**Your M B Maniyar store will have OTP password reset functionality!** 🎉
