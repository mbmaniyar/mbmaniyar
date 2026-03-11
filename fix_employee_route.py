#!/usr/bin/env python3
import re, os

path = os.path.expanduser("~/Desktop/mbmaniyar/app/admin/routes.py")

with open(path, 'r') as f:
    content = f.read()

# Replace the entire add_employee route cleanly
old = """@admin_bp.route('/employees/add', methods=['GET','POST'])
@admin_required
def add_employee():
    if request.method=='POST':
        full_name=request.form.get('full_name','').strip()
        username=request.form.get('username','').strip()
        email=request.form.get('email','').strip()
        phone=request.form.get('phone','').strip()
        password=request.form.get('password','').strip()
        emp_code=request.form.get('employee_code','').strip()
        designation=request.form.get('designation','').strip()
        department=request.form.get('department','').strip()
        base_salary=request.form.get('base_salary',type=float) or 0
        comm_rate=request.form.get('commission_rate',type=float) or 0
        doj_str=request.form.get('date_of_joining','')
        if User.query.filter_by(username=username).first():
            flash('Username taken.','danger')
            return render_template('admin/employee_form.html',emp=None)
        user=User(full_name=full_name,username=username,email=email,phone=phone,
            password_hash=generate_password_hash(password),role='employee')
        db.session.add(user); db.session.flush()
        doj=datetime.strptime(doj_str,'%Y-%m-%d').date() if doj_str else date.today()
        emp=Employee(user_id=user.id,employee_code=emp_code,designation=designation,
            department=department,date_of_joining=doj,base_salary=base_salary,
            commission_rate=comm_rate/100)
        db.session.add(emp); db.session.commit()
        flash(f'Employee {full_name} added! Login: {username} / {password}','success')
        return redirect(url_for('admin.employees'))
    return render_template('admin/employee_form.html',emp=None)"""

new = """@admin_bp.route('/employees/add', methods=['GET','POST'])
@admin_required
def add_employee():
    if request.method=='POST':
        full_name=request.form.get('full_name','').strip()
        username=request.form.get('username','').strip()
        email=request.form.get('email','').strip()
        phone=request.form.get('phone','').strip()
        password=request.form.get('password','').strip()
        emp_code=request.form.get('employee_code','').strip()
        designation=request.form.get('designation','').strip()
        department=request.form.get('department','').strip()
        base_salary=request.form.get('base_salary',type=float) or 0
        comm_rate=request.form.get('commission_rate',type=float) or 0
        doj_str=request.form.get('date_of_joining','')
        if User.query.filter_by(username=username).first():
            flash('Username already taken. Choose a different username.','danger')
            return render_template('admin/employee_form.html',emp=None)
        if not email:
            email = f"{username}@mbmaniyar.local"
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Use a different email or leave blank.','danger')
            return render_template('admin/employee_form.html',emp=None)
        user=User(full_name=full_name,username=username,email=email,phone=phone,
            password_hash=generate_password_hash(password),role='employee')
        db.session.add(user); db.session.flush()
        doj=datetime.strptime(doj_str,'%Y-%m-%d').date() if doj_str else date.today()
        emp=Employee(user_id=user.id,employee_code=emp_code,designation=designation,
            department=department,date_of_joining=doj,base_salary=base_salary,
            commission_rate=comm_rate/100)
        db.session.add(emp); db.session.commit()
        flash(f'Employee {full_name} added! Login: {username} / {password}','success')
        return redirect(url_for('admin.employees'))
    return render_template('admin/employee_form.html',emp=None)"""

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print("✅ Fixed! add_employee route updated.")
else:
    # Fallback: just fix the known broken if block
    # Find and fix the malformed if block at line ~240
    lines = content.split('\n')
    fixed = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Find the broken pattern: if block with no body
        if "if User.query.filter_by(username=username).first():" in line:
            fixed.append(line)
            # Check if next line is the flash (correct) or something else
            if i+1 < len(lines) and "flash(" in lines[i+1]:
                fixed.append(lines[i+1])
                i += 2
                continue
            else:
                # Insert the missing flash line
                indent = len(line) - len(line.lstrip())
                fixed.append(' ' * (indent+4) + "flash('Username already taken.','danger')")
                fixed.append(' ' * (indent+4) + "return render_template('admin/employee_form.html',emp=None)")
                i += 1
                continue
        fixed.append(line)
        i += 1
    content = '\n'.join(fixed)
    with open(path, 'w') as f:
        f.write(content)
    print("✅ Fixed syntax error in routes.py (fallback method)")

print("   Now run: python3 run.py")
