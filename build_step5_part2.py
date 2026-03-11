#!/usr/bin/env python3
"""Step 5 Part 2 — All Employee Portal Templates"""
import os

BASE = os.path.expanduser("~/Desktop/mbmaniyar")

def w(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ {path}")

# ══════════════════════════════════════════════════════════════════
# BASE LAYOUT
# ══════════════════════════════════════════════════════════════════
w("app/templates/employee/base_employee.html", r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{% block title %}Staff{% endblock %} | MBM Portal</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=DM+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#F2F5FB;--sidebar:#1B2B4B;--sidebar-accent:#243460;
  --accent:#3B7DFF;--gold:#F5A623;--green:#10B981;
  --red:#EF4444;--purple:#8B5CF6;--orange:#F97316;
  --text:#1A2340;--muted:#64748B;--border:#E2E8F0;
  --card:#FFFFFF;
  --ff:'Outfit',sans-serif;--ff-mono:'DM Mono',monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--ff);background:var(--bg);color:var(--text);min-height:100vh;display:flex}

/* SIDEBAR */
.e-sidebar{width:245px;min-height:100vh;background:var(--sidebar);display:flex;flex-direction:column;flex-shrink:0;position:fixed;left:0;top:0;bottom:0;z-index:200;overflow-y:auto}
.e-sidebar::-webkit-scrollbar{width:3px}
.e-sidebar::-webkit-scrollbar-thumb{background:rgba(255,255,255,.1)}

.sb-top{padding:1.4rem 1.2rem;border-bottom:1px solid rgba(255,255,255,.06)}
.sb-logo{display:flex;align-items:center;gap:.8rem;margin-bottom:1rem;text-decoration:none}
.sb-logo-icon{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,var(--accent),#2563EB);display:flex;align-items:center;justify-content:center;font-size:1.1rem;font-weight:800;color:#fff;flex-shrink:0}
.sb-logo-text{font-size:.95rem;font-weight:700;color:#fff;line-height:1.2}
.sb-logo-text small{font-size:.62rem;color:rgba(255,255,255,.4);font-weight:400;letter-spacing:1px;display:block}

.sb-profile{background:rgba(255,255,255,.07);border-radius:14px;padding:.9rem;display:flex;align-items:center;gap:.75rem}
.sb-avatar{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--gold),#E8903A);display:flex;align-items:center;justify-content:center;font-size:1.2rem;font-weight:800;color:#fff;flex-shrink:0}
.sb-name{font-size:.85rem;font-weight:700;color:#fff}
.sb-role{font-size:.7rem;color:rgba(255,255,255,.45);margin-top:.1rem}
.sb-code{display:inline-block;margin-top:.25rem;font-size:.63rem;font-family:var(--ff-mono);background:rgba(59,125,255,.25);color:#93C5FD;border-radius:4px;padding:.1rem .45rem}

.sb-nav{padding:.6rem 0}
.sb-section{font-size:.6rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,.2);padding:.8rem 1.2rem .3rem}
.sb-link{display:flex;align-items:center;gap:.75rem;padding:.58rem 1.2rem;margin:.05rem .7rem;border-radius:9px;color:rgba(255,255,255,.5);font-size:.855rem;font-weight:500;text-decoration:none;transition:all .2s}
.sb-link:hover{background:rgba(255,255,255,.07);color:#fff}
.sb-link.active{background:rgba(59,125,255,.2);color:var(--accent);border:1px solid rgba(59,125,255,.2)}
.sb-link i{font-size:.95rem;width:18px;text-align:center}
.sb-badge{margin-left:auto;background:var(--red);color:#fff;border-radius:50px;font-size:.62rem;padding:.1rem .45rem;font-weight:700}

.sb-bottom{margin-top:auto;padding:1rem;border-top:1px solid rgba(255,255,255,.06)}
.sb-logout{display:flex;align-items:center;gap:.6rem;color:rgba(255,255,255,.3);font-size:.83rem;text-decoration:none;padding:.5rem .7rem;border-radius:8px;transition:all .2s}
.sb-logout:hover{background:rgba(239,68,68,.1);color:var(--red)}

/* MAIN */
.e-main{margin-left:245px;flex:1;min-height:100vh;display:flex;flex-direction:column}
.e-topbar{background:#fff;border-bottom:1px solid var(--border);padding:.85rem 1.8rem;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;box-shadow:0 1px 4px rgba(0,0,0,.04)}
.topbar-left h2{font-size:1.1rem;font-weight:700;margin:0}
.topbar-right{display:flex;align-items:center;gap:.8rem}
.topbar-date{font-size:.8rem;color:var(--muted)}

/* CLOCK WIDGET */
.clock-widget{display:flex;align-items:center;gap:.5rem;background:#F8FAFF;border:1px solid var(--border);border-radius:10px;padding:.4rem .9rem;cursor:pointer;transition:all .2s;font-size:.82rem;font-weight:600}
.clock-widget:hover{border-color:var(--accent);color:var(--accent)}
.clock-dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

.e-body{padding:1.6rem;flex:1}

/* CARDS */
.e-card{background:var(--card);border-radius:16px;border:1px solid var(--border);box-shadow:0 1px 8px rgba(0,0,0,.04)}
.e-card-head{padding:.9rem 1.4rem;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.e-card-head h5{font-size:.93rem;font-weight:700;margin:0}
.e-card-body{padding:1.2rem 1.4rem}

/* STAT */
.e-stat{background:var(--card);border-radius:14px;padding:1.1rem 1.3rem;border:1px solid var(--border);position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s}
.e-stat:hover{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.08)}
.e-stat-lbl{font-size:.68rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);margin-bottom:.4rem}
.e-stat-val{font-size:1.7rem;font-weight:800;line-height:1}
.e-stat-sub{font-size:.73rem;color:var(--muted);margin-top:.3rem}
.e-stat-icon{position:absolute;top:1rem;right:1.1rem;font-size:1.5rem;opacity:.1}

/* BADGES */
.e-badge{display:inline-flex;align-items:center;gap:.25rem;border-radius:50px;padding:.22rem .65rem;font-size:.68rem;font-weight:600}
.eb-green{background:#D1FAE5;color:#065F46}
.eb-blue{background:#DBEAFE;color:#1E40AF}
.eb-yellow{background:#FEF3C7;color:#92400E}
.eb-red{background:#FEE2E2;color:#991B1B}
.eb-gray{background:#F1F5F9;color:#475569}
.eb-purple{background:#EDE9FE;color:#5B21B6}
.eb-orange{background:#FEF3C7;color:#9A3412}

/* FLASH */
.flash-wrap{padding:.4rem 1.8rem 0}
.flash-e{border-radius:10px;padding:.65rem 1rem;margin-bottom:.6rem;font-size:.855rem;display:flex;align-items:center;gap:.5rem;border:1px solid transparent}
.f-success{background:#ECFDF5;border-color:#A7F3D0;color:#065F46}
.f-danger{background:#FEF2F2;border-color:#FECACA;color:#991B1B}
.f-warning{background:#FFFBEB;border-color:#FDE68A;color:#92400E}
.f-info{background:#EFF6FF;border-color:#BFDBFE;color:#1E40AF}

/* PROGRESS BAR */
.prog-wrap{background:#E2E8F0;border-radius:50px;overflow:hidden;height:8px}
.prog-fill{height:100%;border-radius:50px;transition:width .8s ease}

@media(max-width:768px){.e-sidebar{transform:translateX(-100%)}.e-main{margin-left:0}}
</style>
{% block extra_css %}{% endblock %}
</head>
<body>

<nav class="e-sidebar">
  <div class="sb-top">
    <a href="{{ url_for('employee.dashboard') }}" class="sb-logo">
      <div class="sb-logo-icon">M</div>
      <div class="sb-logo-text">MBM Staff<small>Employee Portal</small></div>
    </a>
    {% set emp = current_user.employee_profile %}
    {% if emp %}
    <div class="sb-profile">
      <div class="sb-avatar">{{ current_user.full_name[0] }}</div>
      <div style="min-width:0">
        <div class="sb-name" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ current_user.full_name }}</div>
        <div class="sb-role">{{ emp.designation or 'Staff' }}</div>
        <span class="sb-code">{{ emp.employee_code }}</span>
      </div>
    </div>
    {% endif %}
  </div>

  <div class="sb-nav">
    <div class="sb-section">Main</div>
    <a href="{{ url_for('employee.dashboard') }}" class="sb-link {% if request.endpoint=='employee.dashboard' %}active{% endif %}">
      <i class="bi bi-house-fill"></i> Dashboard
    </a>
    <a href="{{ url_for('employee.profile') }}" class="sb-link {% if request.endpoint=='employee.profile' %}active{% endif %}">
      <i class="bi bi-person-circle"></i> My Profile
    </a>

    <div class="sb-section">Work</div>
    <a href="{{ url_for('employee.schedule') }}" class="sb-link {% if request.endpoint=='employee.schedule' %}active{% endif %}">
      <i class="bi bi-calendar3"></i> My Schedule
    </a>
    <a href="{{ url_for('employee.tasks') }}" class="sb-link {% if request.endpoint=='employee.tasks' %}active{% endif %}">
      <i class="bi bi-check2-square"></i> Daily Tasks
    </a>
    <a href="{{ url_for('employee.leave') }}" class="sb-link {% if request.endpoint=='employee.leave' %}active{% endif %}">
      <i class="bi bi-calendar-x"></i> Leave
    </a>

    <div class="sb-section">Finance</div>
    <a href="{{ url_for('employee.salary') }}" class="sb-link {% if request.endpoint=='employee.salary' %}active{% endif %}">
      <i class="bi bi-wallet2"></i> Salary & Commission
    </a>

    <div class="sb-section">Store</div>
    <a href="{{ url_for('employee.notices') }}" class="sb-link {% if request.endpoint=='employee.notices' %}active{% endif %}">
      <i class="bi bi-megaphone"></i> Notice Board
    </a>
    <a href="{{ url_for('employee.training') }}" class="sb-link {% if request.endpoint in ('employee.training','employee.training_detail') %}active{% endif %}">
      <i class="bi bi-book-half"></i> Training Hub
    </a>
  </div>

  <div class="sb-bottom">
    <a href="{{ url_for('auth.logout') }}" class="sb-logout">
      <i class="bi bi-box-arrow-left"></i> Sign Out
    </a>
  </div>
</nav>

<div class="e-main">
  <div class="e-topbar">
    <div class="topbar-left">
      <h2>{% block page_title %}Dashboard{% endblock %}</h2>
    </div>
    <div class="topbar-right">
      <div class="topbar-date"><i class="bi bi-calendar3 me-1"></i>{{ now().strftime('%a, %d %b %Y') }}</div>
      <div class="clock-widget" id="clockWidget" onclick="doClock()">
        <span class="clock-dot" id="clockDot"></span>
        <span id="clockText">Clock In</span>
      </div>
    </div>
  </div>

  <div class="flash-wrap">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}{% for cat, msg in messages %}
      <div class="flash-e f-{{ cat }}"><i class="bi bi-info-circle"></i>{{ msg }}</div>
      {% endfor %}{% endif %}
    {% endwith %}
  </div>

  <div class="e-body">{% block content %}{% endblock %}</div>
</div>

<div id="clockToast" style="position:fixed;bottom:2rem;right:2rem;background:#1B2B4B;color:#fff;padding:.8rem 1.4rem;border-radius:12px;font-size:.875rem;font-weight:600;z-index:9999;display:none;box-shadow:0 8px 30px rgba(0,0,0,.2)"></div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<script>
async function doClock() {
  const res  = await fetch('/staff/clock', {method:'POST'});
  const data = await res.json();
  const toast = document.getElementById('clockToast');
  const dot   = document.getElementById('clockDot');
  const txt   = document.getElementById('clockText');
  if (data.action === 'clocked_in') {
    toast.textContent = `✅ Clocked in at ${data.time}`;
    dot.style.background = 'var(--green)';
    txt.textContent = 'Clocked In';
  } else if (data.action === 'clocked_out') {
    toast.textContent = `👋 Clocked out at ${data.time} — ${data.hours}h worked`;
    dot.style.background = '#94A3B8';
    txt.textContent = 'Clocked Out';
  } else {
    toast.textContent = data.msg || 'Already recorded today';
  }
  toast.style.display = 'block';
  setTimeout(() => toast.style.display='none', 3000);
}
</script>
{% block extra_js %}{% endblock %}
</body>
</html>
""")

# ══════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════
w("app/templates/employee/dashboard.html", r"""{% extends 'employee/base_employee.html' %}
{% block title %}Dashboard{% endblock %}
{% block page_title %}My Dashboard{% endblock %}
{% block extra_css %}
<style>
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.e-stat{animation:fadeUp .4s ease both}
.e-stat:nth-child(1){animation-delay:.05s}.e-stat:nth-child(2){animation-delay:.1s}
.e-stat:nth-child(3){animation-delay:.15s}.e-stat:nth-child(4){animation-delay:.2s}

.shift-hero{background:linear-gradient(135deg,#1B2B4B,#3B7DFF);border-radius:16px;padding:1.4rem;color:#fff;position:relative;overflow:hidden}
.shift-hero::after{content:'';position:absolute;right:-30px;top:-30px;width:130px;height:130px;border-radius:50%;background:rgba(255,255,255,.05)}
.target-bar{height:10px;border-radius:50px;background:rgba(255,255,255,.15);overflow:hidden;margin:.7rem 0}
.target-fill{height:100%;background:linear-gradient(90deg,#10B981,#06D6A0);border-radius:50px;transition:width 1s ease}

.lb-row{display:flex;align-items:center;gap:.8rem;padding:.6rem 0;border-bottom:1px solid var(--border)}
.lb-row:last-child{border-bottom:none}
.lb-rank{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.78rem;font-weight:800;flex-shrink:0}
.rank-1{background:linear-gradient(135deg,#F5A623,#E8903A);color:#fff}
.rank-2{background:#E2E8F0;color:#64748B}
.rank-3{background:#FCD9BD;color:#9A3412}
.rank-n{background:#F1F5F9;color:#94A3B8}

.notice-strip{border-left:3px solid var(--accent);background:#EFF6FF;border-radius:0 8px 8px 0;padding:.7rem 1rem;margin-bottom:.5rem;font-size:.85rem}
.notice-strip.urgent{border-color:var(--red);background:#FEF2F2}
.notice-strip.important{border-color:var(--orange);background:#FFF7ED}
</style>
{% endblock %}
{% block content %}

<div style="margin-bottom:1.5rem">
  <h2 style="font-size:1.45rem;font-weight:800;margin-bottom:.2rem">
    {% set h=now().hour %}{% if h<12 %}Good Morning{% elif h<17 %}Good Afternoon{% else %}Good Evening{% endif %},
    {{ current_user.full_name.split()[0] }}! 👋
  </h2>
  <p style="color:var(--muted);font-size:.875rem">{{ emp.designation or 'Staff' }} · {{ emp.department or 'M B MANIYAR' }}</p>
</div>

<!-- Stats -->
<div class="row g-3 mb-4">
  <div class="col-6 col-lg-3">
    <div class="e-stat">
      <div class="e-stat-lbl">Base Salary</div>
      <div class="e-stat-val" style="font-size:1.4rem;color:var(--green)">₹{{ "%.0f"|format(emp.base_salary or 0) }}</div>
      <div class="e-stat-sub">per month</div>
      <i class="bi bi-wallet2 e-stat-icon" style="color:var(--green)"></i>
    </div>
  </div>
  <div class="col-6 col-lg-3">
    <div class="e-stat">
      <div class="e-stat-lbl">Commission Earned</div>
      <div class="e-stat-val" style="color:var(--purple)">₹{{ "%.0f"|format(salary.commission_earned if salary else 0) }}</div>
      <div class="e-stat-sub">this month</div>
      <i class="bi bi-graph-up e-stat-icon" style="color:var(--purple)"></i>
    </div>
  </div>
  <div class="col-6 col-lg-3">
    <div class="e-stat">
      <div class="e-stat-lbl">Shifts This Month</div>
      <div class="e-stat-val" style="color:var(--accent)">{{ completed_shifts }}/{{ total_shifts }}</div>
      <div class="e-stat-sub">attended</div>
      <i class="bi bi-calendar-check e-stat-icon" style="color:var(--accent)"></i>
    </div>
  </div>
  <div class="col-6 col-lg-3">
    <div class="e-stat">
      <div class="e-stat-lbl">Pending Tasks</div>
      <div class="e-stat-val" style="color:var(--orange)">{{ pending_tasks|length }}</div>
      <div class="e-stat-sub">to complete today</div>
      <i class="bi bi-list-check e-stat-icon" style="color:var(--orange)"></i>
    </div>
  </div>
</div>

<div class="row g-4">
  <div class="col-lg-8">

    <!-- Today's shift -->
    {% if todays_shift %}
    <div class="shift-hero mb-4">
      <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:2px;opacity:.6;margin-bottom:.4rem">Today's Shift</div>
      <div style="font-size:2rem;font-weight:800;font-family:var(--ff-mono)">
        {{ todays_shift.start_time.strftime('%I:%M %p') }} – {{ todays_shift.end_time.strftime('%I:%M %p') }}
      </div>
      <div style="display:flex;align-items:center;gap:.8rem;margin-top:.5rem">
        <span style="font-size:.8rem;opacity:.7"><i class="bi bi-building me-1"></i>{{ emp.department or 'Main Floor' }}</span>
        <span class="e-badge {% if todays_shift.status=='completed' %}eb-green{% else %}eb-blue{% endif %}" style="font-size:.72rem">{{ todays_shift.status|title }}</span>
      </div>
      {% if clock_today %}
      <div style="margin-top:.8rem;font-size:.8rem;background:rgba(255,255,255,.1);border-radius:8px;padding:.5rem .8rem;display:flex;gap:1.5rem">
        <span>🟢 In: {{ clock_today.clock_in.strftime('%I:%M %p') if clock_today.clock_in else '—' }}</span>
        <span>🔴 Out: {{ clock_today.clock_out.strftime('%I:%M %p') if clock_today.clock_out else 'Active' }}</span>
        {% if clock_today.hours_worked %}<span>⏱ {{ clock_today.hours_worked }}h</span>{% endif %}
      </div>
      {% endif %}
    </div>
    {% else %}
    <div class="e-card mb-4" style="padding:1.5rem;text-align:center;color:var(--muted)">
      <i class="bi bi-calendar-x" style="font-size:2rem;display:block;margin-bottom:.5rem"></i>
      No shift scheduled for today
    </div>
    {% endif %}

    <!-- Sales target progress -->
    {% if target_amount > 0 %}
    <div class="e-card mb-4">
      <div class="e-card-head"><h5><i class="bi bi-bullseye me-2" style="color:var(--orange)"></i>Monthly Sales Target</h5></div>
      <div class="e-card-body">
        {% set pct = [(sales_this_month / target_amount * 100)|int, 100]|min %}
        <div style="display:flex;justify-content:space-between;font-size:.82rem;color:var(--muted);margin-bottom:.4rem">
          <span>₹{{ "%.0f"|format(sales_this_month) }} achieved</span>
          <span>Target: ₹{{ "%.0f"|format(target_amount) }}</span>
        </div>
        <div class="prog-wrap"><div class="prog-fill" style="width:{{ pct }}%;background:{% if pct>=100 %}linear-gradient(90deg,var(--green),#06D6A0){% elif pct>=60 %}linear-gradient(90deg,var(--accent),var(--purple)){% else %}linear-gradient(90deg,var(--orange),var(--red)){% endif %}"></div></div>
        <div style="text-align:center;font-size:.82rem;margin-top:.5rem;color:{% if pct>=100 %}var(--green){% else %}var(--muted){% endif %}">
          {% if pct >= 100 %}🎉 Target achieved!{% else %}{{ pct }}% — ₹{{ "%.0f"|format(target_amount - sales_this_month) }} to go{% endif %}
        </div>
      </div>
    </div>
    {% endif %}

    <!-- Tasks -->
    <div class="e-card">
      <div class="e-card-head">
        <h5><i class="bi bi-check2-square me-2" style="color:var(--accent)"></i>Today's Tasks</h5>
        <a href="{{ url_for('employee.tasks') }}" style="font-size:.8rem;color:var(--accent);text-decoration:none">All Tasks →</a>
      </div>
      <div class="e-card-body" style="padding:.5rem 1.4rem">
        {% if pending_tasks %}
          {% for task in pending_tasks %}
          <div style="display:flex;align-items:center;gap:.8rem;padding:.65rem 0;border-bottom:1px solid var(--border)" id="dt-{{ task.id }}">
            <div onclick="toggleTask({{ task.id }}, this)"
                 style="width:22px;height:22px;border-radius:6px;border:2px solid var(--border);display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;transition:all .2s">
            </div>
            <div style="flex:1">
              <div style="font-size:.86rem;font-weight:600" id="dt-title-{{ task.id }}">{{ task.title }}</div>
              {% if task.due_date %}
              <div style="font-size:.72rem;color:{% if task.due_date < today %}var(--red){% else %}var(--muted){% endif %}">
                Due {{ task.due_date.strftime('%d %b') }}{% if task.due_date < today %} ⚠ Overdue{% endif %}
              </div>
              {% endif %}
            </div>
          </div>
          {% endfor %}
        {% else %}
        <div style="text-align:center;padding:1.5rem;color:var(--muted)">
          <i class="bi bi-check-circle" style="color:var(--green);font-size:1.8rem;display:block;margin-bottom:.4rem"></i>
          All tasks done! Great work 🎉
        </div>
        {% endif %}
      </div>
    </div>
  </div>

  <div class="col-lg-4">

    <!-- Leaderboard -->
    <div class="e-card mb-4">
      <div class="e-card-head"><h5>🏆 This Month's Leaderboard</h5></div>
      <div class="e-card-body" style="padding:.5rem 1.4rem">
        {% if leaderboard %}
          {% for emp_row, sal_row in leaderboard %}
          <div class="lb-row">
            <div class="lb-rank {% if loop.index==1 %}rank-1{% elif loop.index==2 %}rank-2{% elif loop.index==3 %}rank-3{% else %}rank-n{% endif %}">
              {% if loop.index<=3 %}{{ ['🥇','🥈','🥉'][loop.index-1] }}{% else %}{{ loop.index }}{% endif %}
            </div>
            <div style="flex:1;min-width:0">
              <div style="font-size:.855rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis
                {% if emp_row.user_id == current_user.id %};color:var(--accent){% endif %}">
                {{ emp_row.user.full_name }}{% if emp_row.user_id == current_user.id %} (You){% endif %}
              </div>
              <div style="font-size:.72rem;color:var(--muted)">{{ emp_row.designation or 'Staff' }}</div>
            </div>
            <div style="font-family:var(--ff-mono);font-size:.85rem;font-weight:700;color:var(--green)">
              ₹{{ "%.0f"|format(sal_row.commission_earned or 0) }}
            </div>
          </div>
          {% endfor %}
        {% else %}
        <div style="text-align:center;padding:2rem;color:var(--muted);font-size:.85rem">No data yet this month</div>
        {% endif %}
      </div>
    </div>

    <!-- Notices -->
    <div class="e-card">
      <div class="e-card-head">
        <h5><i class="bi bi-megaphone me-2" style="color:var(--orange)"></i>Notice Board</h5>
        <a href="{{ url_for('employee.notices') }}" style="font-size:.8rem;color:var(--accent);text-decoration:none">All →</a>
      </div>
      <div class="e-card-body" style="padding:.8rem 1rem">
        {% for n in notices %}
        <div class="notice-strip {{ n.priority }}">
          {% if n.priority=='urgent' %}🚨{% elif n.priority=='important' %}⚠️{% else %}📌{% endif %}
          <strong style="font-size:.83rem">{{ n.title }}</strong>
          <div style="font-size:.75rem;color:var(--muted);margin-top:.2rem">{{ n.created_at.strftime('%d %b') }}</div>
        </div>
        {% else %}
        <div style="text-align:center;padding:1.5rem;color:var(--muted);font-size:.85rem">No notices posted yet</div>
        {% endfor %}
      </div>
    </div>
  </div>
</div>
{% endblock %}
{% block extra_js %}
<script>
async function toggleTask(id, el) {
  const res  = await fetch(`/staff/tasks/toggle/${id}`,{method:'POST'});
  const data = await res.json();
  if(data.ok && data.done){
    el.style.background='var(--green)';el.style.borderColor='var(--green)';el.innerHTML='<i class="bi bi-check-lg" style="color:#fff;font-size:.7rem"></i>';
    document.getElementById(`dt-title-${id}`).style.textDecoration='line-through';
    document.getElementById(`dt-title-${id}`).style.color='var(--muted)';
  }
}
</script>
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════
# PROFILE
# ══════════════════════════════════════════════════════════════════
w("app/templates/employee/profile.html", r"""{% extends 'employee/base_employee.html' %}
{% block title %}My Profile{% endblock %}
{% block page_title %}My Profile{% endblock %}
{% block content %}
<div class="row g-4">
  <div class="col-lg-4">
    <div class="e-card" style="text-align:center;padding:2rem">
      <div style="width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,var(--gold),#E8903A);display:flex;align-items:center;justify-content:center;font-size:2.2rem;font-weight:800;color:#fff;margin:0 auto 1rem">{{ current_user.full_name[0] }}</div>
      <h4 style="font-size:1.2rem;font-weight:800;margin-bottom:.2rem">{{ current_user.full_name }}</h4>
      <p style="color:var(--muted);font-size:.875rem">{{ emp.designation or 'Staff' }}</p>
      <div style="display:flex;justify-content:center;gap:.5rem;flex-wrap:wrap;margin-top:.5rem">
        <span class="e-badge eb-blue">{{ emp.department or 'General' }}</span>
        <span class="e-badge eb-gray" style="font-family:var(--ff-mono)">{{ emp.employee_code }}</span>
      </div>
      <hr style="margin:1.2rem 0;border-color:var(--border)">
      <div style="text-align:left;font-size:.85rem">
        <div style="display:flex;gap:.6rem;margin-bottom:.5rem;color:var(--muted)"><i class="bi bi-envelope" style="width:18px"></i>{{ current_user.email }}</div>
        <div style="display:flex;gap:.6rem;margin-bottom:.5rem;color:var(--muted)"><i class="bi bi-phone" style="width:18px"></i>{{ current_user.phone or 'Not set' }}</div>
        <div style="display:flex;gap:.6rem;color:var(--muted)"><i class="bi bi-calendar3" style="width:18px"></i>Joined {{ emp.date_of_joining.strftime('%d %b %Y') if emp.date_of_joining else '—' }}</div>
      </div>
    </div>
  </div>

  <div class="col-lg-8">
    <div class="e-card mb-4">
      <div class="e-card-head"><h5>Job Details</h5></div>
      <div class="e-card-body">
        <div class="row g-3">
          {% for label, val in [('Employee Code', emp.employee_code), ('Designation', emp.designation or '—'), ('Department', emp.department or '—'), ('Base Salary', '₹'~"%.0f"|format(emp.base_salary or 0)~'/mo'), ('Commission Rate', "%.1f"|format((emp.commission_rate or 0)*100)~'%'), ('Date of Joining', emp.date_of_joining.strftime('%d %b %Y') if emp.date_of_joining else '—')] %}
          <div class="col-6">
            <div style="background:#F8FAFF;border-radius:10px;padding:.7rem .9rem">
              <div style="font-size:.65rem;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin-bottom:.25rem">{{ label }}</div>
              <div style="font-weight:600;font-size:.9rem">{{ val }}</div>
            </div>
          </div>
          {% endfor %}
        </div>
      </div>
    </div>

    <div class="e-card">
      <div class="e-card-head"><h5>Update Contact & Emergency Info</h5></div>
      <div class="e-card-body">
        <form method="POST" action="{{ url_for('employee.update_profile') }}">
          <div class="row g-3">
            <div class="col-md-6">
              <label style="font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);margin-bottom:.3rem;display:block">Phone</label>
              <input type="tel" name="phone" value="{{ current_user.phone or '' }}"
                     style="width:100%;background:#F8FAFF;border:1px solid var(--border);border-radius:9px;padding:.6rem .9rem;font-size:.9rem;outline:none;transition:border-color .2s"
                     placeholder="Your mobile number">
            </div>
            <div class="col-md-6">
              <label style="font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);margin-bottom:.3rem;display:block">Emergency Contact Name</label>
              <input type="text" name="emergency_contact" value="{{ emp.emergency_contact or '' }}"
                     style="width:100%;background:#F8FAFF;border:1px solid var(--border);border-radius:9px;padding:.6rem .9rem;font-size:.9rem;outline:none"
                     placeholder="Father / Spouse name">
            </div>
            <div class="col-md-6">
              <label style="font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);margin-bottom:.3rem;display:block">Emergency Phone</label>
              <input type="tel" name="emergency_phone" value="{{ emp.emergency_phone or '' }}"
                     style="width:100%;background:#F8FAFF;border:1px solid var(--border);border-radius:9px;padding:.6rem .9rem;font-size:.9rem;outline:none"
                     placeholder="Emergency contact number">
            </div>
          </div>
          <button type="submit" style="margin-top:1rem;background:var(--accent);color:#fff;border:none;border-radius:9px;padding:.65rem 1.5rem;font-weight:600;cursor:pointer;font-size:.9rem">Save Changes</button>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════
# SALARY
# ══════════════════════════════════════════════════════════════════
w("app/templates/employee/salary.html", r"""{% extends 'employee/base_employee.html' %}
{% block title %}Salary & Commission{% endblock %}
{% block page_title %}Salary & Commission{% endblock %}
{% block content %}

<div style="background:linear-gradient(135deg,#1B2B4B,#3B7DFF,#8B5CF6);border-radius:20px;padding:2rem;color:#fff;margin-bottom:1.5rem;position:relative;overflow:hidden">
  <div style="position:absolute;top:-40px;right:-40px;width:180px;height:180px;border-radius:50%;background:rgba(255,255,255,.04)"></div>
  <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:2px;opacity:.6;margin-bottom:.6rem">{{ today.strftime('%B %Y') }} — Your Earnings</div>
  {% if current_sal %}
  <div class="row g-3">
    {% for lbl, val, col in [('Base Salary','₹'~"%.0f"|format(current_sal.base_salary or 0),'#fff'),('Commission','₹'~"%.0f"|format(current_sal.commission_earned or 0),'#FFD166'),('Bonus','₹'~"%.0f"|format(current_sal.bonus or 0),'#06D6A0'),('Deductions','-₹'~"%.0f"|format(current_sal.deductions or 0),'#FF6B9D')] %}
    <div class="col-6 col-md-3">
      <div style="opacity:.7;font-size:.7rem;margin-bottom:.25rem">{{ lbl }}</div>
      <div style="font-size:1.3rem;font-weight:800;font-family:var(--ff-mono);color:{{ col }}">{{ val }}</div>
    </div>
    {% endfor %}
  </div>
  <div style="margin-top:1rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,.15);display:flex;align-items:center;justify-content:space-between">
    <div>
      <div style="font-size:.72rem;opacity:.6">Net Payable</div>
      <div style="font-size:2rem;font-weight:800;font-family:var(--ff-mono)">
        ₹{{ "%.0f"|format(current_sal.net_salary or ((current_sal.base_salary or 0)+(current_sal.commission_earned or 0)+(current_sal.bonus or 0)-(current_sal.deductions or 0))) }}
      </div>
    </div>
    <span style="background:{% if current_sal.payment_status=='paid' %}rgba(16,185,129,.3){% else %}rgba(255,255,255,.12){% endif %};border-radius:50px;padding:.3rem 1rem;font-size:.82rem;font-weight:700">
      {% if current_sal.payment_status=='paid' %}✓ Paid{% else %}⏳ Pending{% endif %}
    </span>
  </div>
  {% else %}
  <p style="opacity:.6;margin-top:.5rem">Salary record will be generated by month end.</p>
  {% endif %}
</div>

<div class="row g-4">
  <div class="col-lg-7">
    <div class="e-card">
      <div class="e-card-head"><h5><i class="bi bi-clock-history me-2" style="color:var(--accent)"></i>Payslip History</h5></div>
      <div style="overflow-x:auto">
        <table style="width:100%;border-collapse:collapse">
          <thead>
            <tr>{% for h in ['Month','Base','Commission','Bonus','Net','Status'] %}<th style="font-size:.68rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);padding:.65rem 1rem;border-bottom:1px solid var(--border);text-align:left;white-space:nowrap">{{ h }}</th>{% endfor %}</tr>
          </thead>
          <tbody>
            {% for r in records %}
            <tr style="border-bottom:1px solid var(--border)">
              <td style="padding:.75rem 1rem;font-weight:700">{{ ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][r.month] }} {{ r.year }}</td>
              <td style="padding:.75rem 1rem;font-size:.85rem">₹{{ "%.0f"|format(r.base_salary or 0) }}</td>
              <td style="padding:.75rem 1rem;font-size:.85rem;color:var(--purple);font-weight:600">₹{{ "%.0f"|format(r.commission_earned or 0) }}</td>
              <td style="padding:.75rem 1rem;font-size:.85rem;color:var(--green)">₹{{ "%.0f"|format(r.bonus or 0) }}</td>
              <td style="padding:.75rem 1rem;font-weight:800;font-family:var(--ff-mono);color:var(--accent)">₹{{ "%.0f"|format(r.net_salary or ((r.base_salary or 0)+(r.commission_earned or 0)+(r.bonus or 0)-(r.deductions or 0))) }}</td>
              <td style="padding:.75rem 1rem"><span class="e-badge {% if r.payment_status=='paid' %}eb-green{% else %}eb-yellow{% endif %}">{{ r.payment_status|title }}</span></td>
            </tr>
            {% else %}
            <tr><td colspan="6" style="text-align:center;padding:3rem;color:var(--muted)">No records yet</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="col-lg-5">
    <div class="e-card">
      <div class="e-card-head"><h5><i class="bi bi-list-ul me-2" style="color:var(--purple)"></i>Commission Breakdown</h5></div>
      <div class="e-card-body" style="padding:.5rem 1rem">
        <div style="font-size:.78rem;color:var(--muted);margin-bottom:.7rem">
          Rate: <strong style="color:var(--purple)">{{ "%.1f"|format((emp.commission_rate or 0)*100) }}%</strong> of sales you process via POS
        </div>
        {% if commission_log %}
          {% for log in commission_log %}
          <div style="display:flex;justify-content:space-between;align-items:center;padding:.6rem 0;border-bottom:1px solid var(--border)">
            <div>
              <div style="font-size:.82rem;font-weight:600;font-family:var(--ff-mono);color:var(--accent)">{{ log.order }}</div>
              <div style="font-size:.72rem;color:var(--muted)">{{ log.date }} · Sale ₹{{ "%.0f"|format(log.amount) }}</div>
            </div>
            <div style="font-weight:700;color:var(--green)">+₹{{ "%.2f"|format(log.commission) }}</div>
          </div>
          {% endfor %}
          <div style="text-align:right;padding:.6rem 0;font-weight:800;color:var(--purple)">
            Total: ₹{{ "%.2f"|format(commission_log|sum(attribute='commission')) }}
          </div>
        {% else %}
        <div style="text-align:center;padding:2rem;color:var(--muted);font-size:.85rem">
          No commissions logged this month yet.<br>
          <small>Make sure you enter your employee code when billing on POS.</small>
        </div>
        {% endif %}
      </div>
    </div>
  </div>
</div>
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════
# LEAVE PAGE
# ══════════════════════════════════════════════════════════════════
w("app/templates/employee/leave.html", r"""{% extends 'employee/base_employee.html' %}
{% block title %}Leave{% endblock %}
{% block page_title %}Leave Management{% endblock %}
{% block content %}
<div class="row g-4">
  <div class="col-lg-4">
    <!-- Leave balance -->
    <div class="e-card mb-4">
      <div class="e-card-head"><h5>Leave Balance ({{ today.year }})</h5></div>
      <div class="e-card-body">
        {% for lbl, bal, used, color in [('Casual Leave', balance_casual, used_casual, 'var(--accent)'), ('Sick Leave', balance_sick, used_sick, 'var(--orange)')] %}
        <div style="margin-bottom:1.2rem">
          <div style="display:flex;justify-content:space-between;font-size:.82rem;margin-bottom:.3rem">
            <span style="font-weight:600">{{ lbl }}</span>
            <span style="color:{{ color }};font-weight:700">{{ bal }} days left</span>
          </div>
          <div class="prog-wrap"><div class="prog-fill" style="width:{{ [(bal / (12 if 'Casual' in lbl else 7) * 100)|int, 100]|min }}%;background:{{ color }}"></div></div>
          <div style="font-size:.72rem;color:var(--muted);margin-top:.25rem">{{ used }} used of {{ 12 if 'Casual' in lbl else 7 }}</div>
        </div>
        {% endfor %}
      </div>
    </div>

    <!-- Apply leave -->
    <div class="e-card">
      <div class="e-card-head"><h5>Apply for Leave</h5></div>
      <div class="e-card-body">
        <form method="POST" action="{{ url_for('employee.apply_leave') }}">
          <div style="margin-bottom:.8rem">
            <label style="font-size:.73rem;font-weight:600;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:.3rem">Leave Type</label>
            <select name="leave_type" style="width:100%;background:#F8FAFF;border:1px solid var(--border);border-radius:9px;padding:.6rem .9rem;font-size:.875rem;outline:none">
              <option value="casual">Casual Leave</option>
              <option value="sick">Sick Leave</option>
              <option value="earned">Earned Leave</option>
            </select>
          </div>
          <div class="row g-2 mb-3">
            <div class="col-6">
              <label style="font-size:.73rem;font-weight:600;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:.3rem">From</label>
              <input type="date" name="start_date" min="{{ today }}" required
                     style="width:100%;background:#F8FAFF;border:1px solid var(--border);border-radius:9px;padding:.6rem .9rem;font-size:.875rem;outline:none">
            </div>
            <div class="col-6">
              <label style="font-size:.73rem;font-weight:600;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:.3rem">To</label>
              <input type="date" name="end_date" min="{{ today }}" required
                     style="width:100%;background:#F8FAFF;border:1px solid var(--border);border-radius:9px;padding:.6rem .9rem;font-size:.875rem;outline:none">
            </div>
          </div>
          <div style="margin-bottom:1rem">
            <label style="font-size:.73rem;font-weight:600;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:.3rem">Reason</label>
            <textarea name="reason" rows="3" placeholder="Brief reason for leave…"
                      style="width:100%;background:#F8FAFF;border:1px solid var(--border);border-radius:9px;padding:.6rem .9rem;font-size:.875rem;outline:none;resize:vertical"></textarea>
          </div>
          <button type="submit" style="width:100%;background:var(--accent);color:#fff;border:none;border-radius:9px;padding:.7rem;font-weight:700;cursor:pointer;font-size:.9rem">Submit Request</button>
        </form>
      </div>
    </div>
  </div>

  <div class="col-lg-8">
    <div class="e-card">
      <div class="e-card-head"><h5><i class="bi bi-calendar-x me-2" style="color:var(--accent)"></i>My Leave Requests</h5></div>
      <div style="overflow-x:auto">
        <table style="width:100%;border-collapse:collapse">
          <thead>
            <tr>{% for h in ['Type','From','To','Days','Reason','Status','Note'] %}<th style="font-size:.68rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);padding:.65rem 1rem;border-bottom:1px solid var(--border);text-align:left;white-space:nowrap">{{ h }}</th>{% endfor %}</tr>
          </thead>
          <tbody>
            {% for r in requests %}
            <tr style="border-bottom:1px solid var(--border)">
              <td style="padding:.75rem 1rem"><span class="e-badge eb-blue">{{ r.leave_type|title }}</span></td>
              <td style="padding:.75rem 1rem;font-size:.84rem">{{ r.start_date.strftime('%d %b') }}</td>
              <td style="padding:.75rem 1rem;font-size:.84rem">{{ r.end_date.strftime('%d %b %Y') }}</td>
              <td style="padding:.75rem 1rem;font-weight:700;text-align:center">{{ r.days }}</td>
              <td style="padding:.75rem 1rem;font-size:.82rem;color:var(--muted);max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ r.reason or '—' }}</td>
              <td style="padding:.75rem 1rem"><span class="e-badge {% if r.status=='approved' %}eb-green{% elif r.status=='rejected' %}eb-red{% else %}eb-yellow{% endif %}">{{ r.status|title }}</span></td>
              <td style="padding:.75rem 1rem;font-size:.78rem;color:var(--muted)">{{ r.admin_note or '—' }}</td>
            </tr>
            {% else %}
            <tr><td colspan="7" style="text-align:center;padding:3rem;color:var(--muted)">No leave requests yet</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════
# NOTICES
# ══════════════════════════════════════════════════════════════════
w("app/templates/employee/notices.html", r"""{% extends 'employee/base_employee.html' %}
{% block title %}Notice Board{% endblock %}
{% block page_title %}Notice Board{% endblock %}
{% block content %}
<div style="max-width:780px">
  {% if notices %}
    {% for n in notices %}
    <div style="background:#fff;border-radius:16px;border:1px solid var(--border);margin-bottom:1rem;overflow:hidden;border-left:4px solid {% if n.priority=='urgent' %}var(--red){% elif n.priority=='important' %}var(--orange){% else %}var(--accent){% endif %}">
      <div style="padding:1.1rem 1.4rem">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:.8rem;margin-bottom:.5rem">
          <div style="display:flex;align-items:center;gap:.6rem">
            <span style="font-size:1.2rem">{% if n.priority=='urgent' %}🚨{% elif n.priority=='important' %}⚠️{% else %}📌{% endif %}</span>
            <h5 style="font-size:1rem;font-weight:700;margin:0">{{ n.title }}</h5>
          </div>
          <span class="e-badge {% if n.priority=='urgent' %}eb-red{% elif n.priority=='important' %}eb-orange{% else %}eb-blue{% endif %}">{{ n.priority|title }}</span>
        </div>
        <p style="font-size:.88rem;color:var(--muted);line-height:1.6;margin:0">{{ n.body }}</p>
        <div style="font-size:.73rem;color:var(--muted);margin-top:.7rem">
          Posted {{ n.created_at.strftime('%d %b %Y, %I:%M %p') }}
          {% if n.author %} by {{ n.author.full_name }}{% endif %}
        </div>
      </div>
    </div>
    {% endfor %}
  {% else %}
  <div style="text-align:center;padding:5rem;color:var(--muted)">
    <i class="bi bi-megaphone" style="font-size:3rem;display:block;margin-bottom:1rem;opacity:.3"></i>
    <h4 style="font-weight:700">No notices yet</h4>
    <p>Your manager will post announcements here.</p>
  </div>
  {% endif %}
</div>
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════
# TRAINING HUB
# ══════════════════════════════════════════════════════════════════
w("app/templates/employee/training.html", r"""{% extends 'employee/base_employee.html' %}
{% block title %}Training Hub{% endblock %}
{% block page_title %}Training Hub{% endblock %}
{% block content %}

<div style="display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:1.5rem">
  {% for cat in categories %}
  <a href="{{ url_for('employee.training', cat=cat) }}"
     style="padding:.4rem 1rem;border-radius:8px;font-size:.82rem;font-weight:600;text-decoration:none;transition:all .2s;
            {% if active_cat==cat %}background:var(--accent);color:#fff{% else %}background:#fff;color:var(--muted);border:1px solid var(--border){% endif %}">
    {{ cat }}
  </a>
  {% endfor %}
</div>

<div class="row g-3">
  {% for r in resources %}
  <div class="col-md-6 col-xl-4">
    <a href="{{ url_for('employee.training_detail', rid=r.id) }}" style="text-decoration:none">
      <div style="background:#fff;border-radius:14px;border:1px solid var(--border);padding:1.2rem;transition:all .2s;height:100%" onmouseover="this.style.transform='translateY(-3px)';this.style.boxShadow='0 8px 24px rgba(0,0,0,.08)'" onmouseout="this.style.transform='';this.style.boxShadow=''">
        <div style="font-size:1.8rem;margin-bottom:.6rem">
          {% if r.resource_type=='video' %}🎬{% elif r.resource_type=='policy' %}📋{% else %}📖{% endif %}
        </div>
        <span class="e-badge eb-blue" style="margin-bottom:.5rem;display:inline-block">{{ r.category }}</span>
        <h5 style="font-size:.95rem;font-weight:700;color:var(--text);margin:.3rem 0 .4rem">{{ r.title }}</h5>
        <p style="font-size:.8rem;color:var(--muted);line-height:1.5;margin:0">{{ r.description or '' }}</p>
        <div style="font-size:.72rem;color:var(--muted);margin-top:.7rem">{{ r.created_at.strftime('%d %b %Y') }}</div>
      </div>
    </a>
  </div>
  {% else %}
  <div class="col-12" style="text-align:center;padding:5rem;color:var(--muted)">
    <i class="bi bi-book" style="font-size:3rem;display:block;margin-bottom:1rem;opacity:.3"></i>
    No training resources in this category yet.
  </div>
  {% endfor %}
</div>
{% endblock %}
""")

w("app/templates/employee/training_detail.html", r"""{% extends 'employee/base_employee.html' %}
{% block title %}{{ resource.title }}{% endblock %}
{% block page_title %}Training Hub{% endblock %}
{% block content %}
<div style="max-width:760px">
  <a href="{{ url_for('employee.training') }}" style="color:var(--accent);text-decoration:none;font-size:.875rem;display:inline-flex;align-items:center;gap:.4rem;margin-bottom:1.2rem">
    <i class="bi bi-arrow-left"></i> Back to Training Hub
  </a>
  <div class="e-card">
    <div style="padding:1.5rem 1.8rem;border-bottom:1px solid var(--border)">
      <div style="font-size:2rem;margin-bottom:.6rem">
        {% if resource.resource_type=='video' %}🎬{% elif resource.resource_type=='policy' %}📋{% else %}📖{% endif %}
      </div>
      <span class="e-badge eb-blue" style="margin-bottom:.6rem;display:inline-block">{{ resource.category }}</span>
      <h2 style="font-size:1.4rem;font-weight:800;margin-bottom:.4rem">{{ resource.title }}</h2>
      {% if resource.description %}<p style="color:var(--muted);font-size:.9rem">{{ resource.description }}</p>{% endif %}
      <div style="font-size:.75rem;color:var(--muted);margin-top:.5rem">Added {{ resource.created_at.strftime('%d %b %Y') }}</div>
    </div>
    <div style="padding:1.5rem 1.8rem;font-size:.9rem;line-height:1.8;color:var(--text)">
      {% if resource.content %}
        {% set content = resource.content %}
        {% for line in content.split('\n') %}
          {% if line.startswith('## ') %}
            <h3 style="font-size:1.1rem;font-weight:700;margin:1.2rem 0 .4rem;color:var(--text)">{{ line[3:] }}</h3>
          {% elif line.startswith('### ') %}
            <h4 style="font-size:.95rem;font-weight:700;margin:1rem 0 .3rem;color:var(--accent)">{{ line[4:] }}</h4>
          {% elif line.startswith('- ') %}
            <div style="display:flex;gap:.5rem;margin-bottom:.3rem">
              <span style="color:var(--accent);flex-shrink:0">•</span>
              <span>{{ line[2:] }}</span>
            </div>
          {% elif line.startswith('**') and line.endswith('**') %}
            <strong>{{ line[2:-2] }}</strong>
          {% elif line.strip() == '' %}
            <div style="height:.5rem"></div>
          {% else %}
            <p style="margin-bottom:.3rem">{{ line }}</p>
          {% endif %}
        {% endfor %}
      {% else %}
        <p style="color:var(--muted)">No content added yet.</p>
      {% endif %}
    </div>
  </div>
</div>
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════
# SCHEDULE (reuse from before but update URL)
# ══════════════════════════════════════════════════════════════════
w("app/templates/employee/schedule.html", r"""{% extends 'employee/base_employee.html' %}
{% block title %}My Schedule{% endblock %}
{% block page_title %}My Schedule{% endblock %}
{% block extra_css %}
<style>
.cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:.4rem}
.cal-head{text-align:center;font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--muted);padding:.4rem 0}
.cal-cell{aspect-ratio:1;border-radius:10px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:.82rem;font-weight:600;background:#F8FAFF;border:1px solid transparent;transition:all .2s}
.cal-cell.has-shift{background:#EFF6FF;border-color:#BFDBFE}
.cal-cell.today{border-color:var(--accent);box-shadow:0 0 0 2px rgba(59,125,255,.2)}
.cal-cell.completed{background:#ECFDF5;border-color:#A7F3D0}
.cal-cell.absent{background:#FEF2F2;border-color:#FECACA}
.cal-cell.empty{background:transparent;border:none}
.shift-dot{width:5px;height:5px;border-radius:50%;margin-top:.1rem}
.shift-mini{font-size:.5rem;color:var(--muted);margin-top:.05rem;text-align:center;line-height:1.2}
</style>
{% endblock %}
{% block content %}
<div class="row g-4">
  <div class="col-lg-8">
    <div class="e-card">
      <div class="e-card-head">
        <div style="display:flex;align-items:center;gap:.8rem">
          <a href="{{ url_for('employee.schedule', month=prev_month, year=prev_year) }}" style="width:32px;height:32px;border-radius:8px;border:1px solid var(--border);background:#fff;display:flex;align-items:center;justify-content:center;color:var(--text);text-decoration:none;transition:all .2s" onmouseover="this.style.background='var(--accent)';this.style.color='#fff'" onmouseout="this.style.background='#fff';this.style.color='var(--text)'"><i class="bi bi-chevron-left"></i></a>
          <div style="font-size:1rem;font-weight:700;min-width:150px;text-align:center">{{ month_name }} {{ year }}</div>
          <a href="{{ url_for('employee.schedule', month=next_month, year=next_year) }}" style="width:32px;height:32px;border-radius:8px;border:1px solid var(--border);background:#fff;display:flex;align-items:center;justify-content:center;color:var(--text);text-decoration:none;transition:all .2s" onmouseover="this.style.background='var(--accent)';this.style.color='#fff'" onmouseout="this.style.background='#fff';this.style.color='var(--text)'"><i class="bi bi-chevron-right"></i></a>
        </div>
        <span style="font-size:.8rem;color:var(--muted)">{{ shifts|length }} shifts</span>
      </div>
      <div class="e-card-body">
        <div class="cal-grid mb-2">{% for d in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'] %}<div class="cal-head">{{ d }}</div>{% endfor %}</div>
        <div class="cal-grid">
          {% for week in cal %}{% for day in week %}
            {% if day == 0 %}<div class="cal-cell empty"></div>
            {% else %}
              {% set shift = shift_map.get(day) %}
              <div class="cal-cell {% if shift %}has-shift {{ shift.status }}{% endif %} {% if day==today.day and month==today.month and year==today.year %}today{% endif %}">
                <span>{{ day }}</span>
                {% if shift %}<span class="shift-dot" style="background:{% if shift.status=='completed' %}var(--green){% elif shift.status=='absent' %}var(--red){% else %}var(--accent){% endif %}"></span>
                <span class="shift-mini">{{ shift.start_time.strftime('%I%p')|lower }}</span>{% endif %}
              </div>
            {% endif %}
          {% endfor %}{% endfor %}
        </div>
        <div style="display:flex;gap:1.2rem;margin-top:1rem;flex-wrap:wrap">
          {% for lbl, col in [('Scheduled','var(--accent)'),('Completed','var(--green)'),('Absent','var(--red)')] %}
          <div style="display:flex;align-items:center;gap:.4rem;font-size:.75rem;color:var(--muted)">
            <span style="width:9px;height:9px;border-radius:50%;background:{{ col }};display:inline-block"></span>{{ lbl }}
          </div>
          {% endfor %}
        </div>
      </div>
    </div>
  </div>
  <div class="col-lg-4">
    <div class="e-card">
      <div class="e-card-head"><h5>Shift Details</h5></div>
      <div class="e-card-body" style="padding:.6rem">
        {% for s in shifts %}
        <div style="display:flex;align-items:center;gap:.8rem;padding:.7rem .6rem;border-bottom:1px solid var(--border);border-left:3px solid {% if s.status=='completed' %}var(--green){% elif s.status=='absent' %}var(--red){% else %}var(--accent){% endif %};margin-bottom:.3rem;border-radius:0 8px 8px 0;background:#F8FAFF">
          <div style="text-align:center;min-width:38px">
            <div style="font-size:.6rem;font-weight:700;text-transform:uppercase;color:var(--muted)">{{ s.date.strftime('%a') }}</div>
            <div style="font-size:1.1rem;font-weight:800">{{ s.date.day }}</div>
          </div>
          <div style="flex:1">
            <div style="font-size:.84rem;font-weight:600">{{ s.start_time.strftime('%I:%M %p') }} – {{ s.end_time.strftime('%I:%M %p') }}</div>
            {% if s.notes %}<div style="font-size:.72rem;color:var(--muted)">{{ s.notes }}</div>{% endif %}
          </div>
          <span class="e-badge {% if s.status=='completed' %}eb-green{% elif s.status=='absent' %}eb-red{% else %}eb-blue{% endif %}">{{ s.status|replace('_',' ')|title }}</span>
        </div>
        {% else %}
        <div style="text-align:center;padding:2rem;color:var(--muted)">No shifts this month</div>
        {% endfor %}
      </div>
    </div>
  </div>
</div>
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════
# TASKS
# ══════════════════════════════════════════════════════════════════
w("app/templates/employee/tasks.html", r"""{% extends 'employee/base_employee.html' %}
{% block title %}My Tasks{% endblock %}
{% block page_title %}Daily Tasks{% endblock %}
{% block content %}
{% set done_ct = tasks|selectattr('is_completed')|list|length %}
{% set total_ct = tasks|length %}
<div style="display:flex;gap:1rem;margin-bottom:1.5rem;flex-wrap:wrap">
  {% for lbl, val, col in [('Total', total_ct, 'var(--accent)'), ('Completed', done_ct, 'var(--green)'), ('Pending', total_ct-done_ct, 'var(--orange)')] %}
  <div style="background:#fff;border:1px solid var(--border);border-radius:10px;padding:.6rem 1.1rem;display:flex;align-items:center;gap:.5rem;font-size:.83rem;font-weight:600">
    <span style="width:9px;height:9px;border-radius:50%;background:{{ col }};display:inline-block"></span>{{ lbl }}: {{ val }}
  </div>
  {% endfor %}
</div>
<div style="max-width:700px">
  {% set pending = tasks|rejectattr('is_completed')|list %}
  {% if pending %}
  <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin-bottom:.7rem">Pending ({{ pending|length }})</div>
  {% for task in pending %}
  <div style="background:#fff;border-radius:13px;border:1px solid var(--border);padding:.9rem 1.1rem;margin-bottom:.6rem;display:flex;align-items:flex-start;gap:.9rem;transition:all .2s" id="tc-{{ task.id }}" onmouseover="this.style.boxShadow='0 4px 14px rgba(0,0,0,.06)'" onmouseout="this.style.boxShadow=''">
    <div onclick="toggleTask({{ task.id }})" id="chk-{{ task.id }}" style="width:24px;height:24px;border-radius:7px;border:2px solid var(--border);display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;margin-top:.1rem;transition:all .2s"></div>
    <div style="flex:1">
      <div style="font-size:.9rem;font-weight:600" id="tt-{{ task.id }}">{{ task.title }}</div>
      {% if task.description %}<div style="font-size:.8rem;color:var(--muted);margin-top:.2rem">{{ task.description }}</div>{% endif %}
      {% if task.due_date %}
      <div style="font-size:.73rem;margin-top:.3rem">
        <span style="padding:.15rem .55rem;border-radius:50px;font-weight:600;background:{% if task.due_date < today %}#FEF2F2;color:var(--red){% elif task.due_date == today %}#FFFBEB;color:#92400E{% else %}#EFF6FF;color:#1E40AF{% endif %}">
          {% if task.due_date < today %}⚠ Overdue: {% elif task.due_date == today %}📅 Due Today{% else %}📅 {% endif %}{{ task.due_date.strftime('%d %b') if task.due_date != today else '' }}
        </span>
      </div>
      {% endif %}
    </div>
  </div>
  {% endfor %}
  {% endif %}

  {% set done = tasks|selectattr('is_completed')|list %}
  {% if done %}
  <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin:1.5rem 0 .7rem">Done ({{ done|length }})</div>
  {% for task in done %}
  <div style="background:#F8FAFF;border-radius:13px;border:1px solid var(--border);padding:.9rem 1.1rem;margin-bottom:.6rem;display:flex;align-items:flex-start;gap:.9rem;opacity:.65" id="tc-{{ task.id }}">
    <div onclick="toggleTask({{ task.id }})" id="chk-{{ task.id }}" style="width:24px;height:24px;border-radius:7px;background:var(--green);border:2px solid var(--green);display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;margin-top:.1rem">
      <i class="bi bi-check-lg" style="color:#fff;font-size:.7rem"></i>
    </div>
    <div style="flex:1">
      <div style="font-size:.9rem;font-weight:600;text-decoration:line-through;color:var(--muted)" id="tt-{{ task.id }}">{{ task.title }}</div>
      {% if task.completed_at %}<div style="font-size:.73rem;color:var(--muted)">Done {{ task.completed_at.strftime('%d %b, %I:%M %p') }}</div>{% endif %}
    </div>
  </div>
  {% endfor %}
  {% endif %}

  {% if not tasks %}
  <div style="text-align:center;padding:5rem;color:var(--muted)">
    <i class="bi bi-check-circle" style="font-size:3.5rem;color:var(--green);display:block;margin-bottom:1rem"></i>
    <h4 style="font-weight:700">No tasks assigned yet</h4>
    <p>Your manager will assign tasks here.</p>
  </div>
  {% endif %}
</div>
{% endblock %}
{% block extra_js %}
<script>
async function toggleTask(id) {
  const res  = await fetch(`/staff/tasks/toggle/${id}`,{method:'POST'});
  const data = await res.json();
  if(!data.ok) return;
  const chk  = document.getElementById(`chk-${id}`);
  const title = document.getElementById(`tt-${id}`);
  const card  = document.getElementById(`tc-${id}`);
  if(data.done){
    chk.style.background='var(--green)';chk.style.borderColor='var(--green)';
    chk.innerHTML='<i class="bi bi-check-lg" style="color:#fff;font-size:.7rem"></i>';
    title.style.textDecoration='line-through';title.style.color='var(--muted)';
    card.style.opacity='.65';
  } else {
    chk.style.background='';chk.style.borderColor='var(--border)';chk.innerHTML='';
    title.style.textDecoration='';title.style.color='';card.style.opacity='';
  }
}
</script>
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════
# ADMIN TEMPLATES for notices, leave, targets, training
# ══════════════════════════════════════════════════════════════════
w("app/templates/admin/notices.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}Notice Board{% endblock %}
{% block page_title %}Notice Board{% endblock %}
{% block content %}
<div class="row g-4">
  <div class="col-lg-4">
    <div class="panel">
      <div class="panel-head"><h5>Post New Notice</h5></div>
      <div class="panel-body">
        <form method="POST" action="{{ url_for('admin.add_notice') }}">
          <label class="ctrl-label">Title *</label>
          <input type="text" name="title" class="ctrl mb-3" required placeholder="Notice title…">
          <label class="ctrl-label">Priority</label>
          <select name="priority" class="ctrl mb-3">
            <option value="normal">📌 Normal</option>
            <option value="important">⚠️ Important</option>
            <option value="urgent">🚨 Urgent</option>
          </select>
          <label class="ctrl-label">Message *</label>
          <textarea name="body" class="ctrl mb-3" rows="5" required placeholder="Write your notice…"></textarea>
          <button type="submit" class="btn-accent w-100"><i class="bi bi-megaphone me-2"></i>Post Notice</button>
        </form>
      </div>
    </div>
  </div>
  <div class="col-lg-8">
    <div class="panel">
      <div class="panel-head"><h5>All Notices ({{ notices|length }})</h5></div>
      <div class="panel-body" style="padding:.5rem">
        {% for n in notices %}
        <div style="background:var(--surface2);border-radius:12px;padding:1rem;margin-bottom:.6rem;border-left:3px solid {% if n.priority=='urgent' %}var(--accent2){% elif n.priority=='important' %}var(--gold){% else %}var(--blue){% endif %}">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:.8rem">
            <div style="flex:1">
              <div style="font-size:.9rem;font-weight:700;margin-bottom:.3rem">{{ n.title }}</div>
              <div style="font-size:.82rem;color:var(--muted)">{{ n.body[:150] }}{% if n.body|length > 150 %}…{% endif %}</div>
              <div style="font-size:.72rem;color:var(--muted);margin-top:.4rem">{{ n.created_at.strftime('%d %b %Y, %I:%M %p') }}</div>
            </div>
            <form method="POST" action="{{ url_for('admin.delete_notice', nid=n.id) }}" onsubmit="return confirm('Delete this notice?')">
              <button type="submit" class="btn-danger"><i class="bi bi-trash3"></i></button>
            </form>
          </div>
        </div>
        {% else %}
        <div style="text-align:center;padding:3rem;color:var(--muted)">No notices posted yet</div>
        {% endfor %}
      </div>
    </div>
  </div>
</div>
{% endblock %}
""")

w("app/templates/admin/leave_requests.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}Leave Requests{% endblock %}
{% block page_title %}Leave Requests{% endblock %}
{% block content %}
<div style="display:flex;gap:.5rem;margin-bottom:1.5rem">
  {% for s,lbl in [('pending','⏳ Pending'),('approved','✅ Approved'),('rejected','❌ Rejected'),('all','All')] %}
  <a href="{{ url_for('admin.leave_requests', status=s) }}"
     style="padding:.4rem 1rem;border-radius:8px;font-size:.82rem;font-weight:600;text-decoration:none;
            {% if status==s %}background:var(--accent);color:#1A1A00{% else %}background:var(--surface2);color:var(--muted){% endif %}">{{ lbl }}</a>
  {% endfor %}
</div>
<div class="panel">
  <div class="panel-head"><h5>{{ requests|length }} Request{% if requests|length!=1 %}s{% endif %}</h5></div>
  <div style="overflow-x:auto">
    <table class="data-table">
      <thead><tr><th>Employee</th><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Reason</th><th>Status</th><th>Action</th></tr></thead>
      <tbody>
        {% for r in requests %}
        <tr>
          <td style="font-weight:600">{{ r.employee.user.full_name }}<br><span style="font-size:.72rem;color:var(--muted)">{{ r.employee.employee_code }}</span></td>
          <td><span class="badge-status badge-confirmed">{{ r.leave_type|title }}</span></td>
          <td>{{ r.start_date.strftime('%d %b %Y') }}</td>
          <td>{{ r.end_date.strftime('%d %b %Y') }}</td>
          <td style="text-align:center;font-weight:700">{{ r.days }}</td>
          <td style="font-size:.82rem;color:var(--muted);max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ r.reason or '—' }}</td>
          <td><span class="badge-status {% if r.status=='approved' %}badge-completed{% elif r.status=='rejected' %}badge-pending{% else %}badge-confirmed{% endif %}">{{ r.status|title }}</span></td>
          <td>
            <form method="POST" action="{{ url_for('admin.update_leave', lid=r.id) }}" style="display:flex;gap:.3rem;align-items:center">
              <select name="status" class="ctrl" style="padding:.3rem .5rem;font-size:.78rem;width:110px">
                {% for s in ['pending','approved','rejected'] %}<option value="{{ s }}" {% if r.status==s %}selected{% endif %}>{{ s|title }}</option>{% endfor %}
              </select>
              <input type="text" name="admin_note" class="ctrl" style="padding:.3rem .5rem;font-size:.78rem;width:120px" placeholder="Note…">
              <button type="submit" class="btn-success" style="padding:.3rem .6rem">✓</button>
            </form>
          </td>
        </tr>
        {% else %}
        <tr><td colspan="8" style="text-align:center;padding:3rem;color:var(--muted)">No requests</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

w("app/templates/admin/sales_targets.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}Sales Targets{% endblock %}
{% block page_title %}Sales Targets — {{ month }}{% endblock %}
{% block content %}
<div class="panel">
  <div class="panel-head"><h5>Set Monthly Sales Targets</h5></div>
  <div style="overflow-x:auto">
    <table class="data-table">
      <thead><tr><th>Employee</th><th>Target (₹)</th><th>Achieved (₹)</th><th>Commission</th><th>Progress</th><th>Set Target</th></tr></thead>
      <tbody>
        {% for emp in employees %}
        {% set t = targets.get(emp.id) %}
        {% set s = salaries.get(emp.id) %}
        {% set achieved = (s.commission_earned or 0) / (emp.commission_rate or 0.01) if (s and emp.commission_rate) else 0 %}
        {% set target_val = t.target_amount if t else 0 %}
        {% set pct = [(achieved/target_val*100)|int, 100]|min if target_val > 0 else 0 %}
        <tr>
          <td>
            <div style="font-weight:600">{{ emp.user.full_name }}</div>
            <div style="font-size:.72rem;color:var(--muted)">{{ emp.designation or 'Staff' }}</div>
          </td>
          <td style="font-weight:700;font-family:var(--ff-mono)">₹{{ "%.0f"|format(target_val) }}</td>
          <td style="font-weight:700;font-family:var(--ff-mono);color:var(--green)">₹{{ "%.0f"|format(achieved) }}</td>
          <td style="font-family:var(--ff-mono);color:var(--purple)">₹{{ "%.0f"|format(s.commission_earned or 0) if s else '0' }}</td>
          <td style="min-width:120px">
            <div class="prog-wrap" style="height:6px"><div class="prog-fill" style="width:{{ pct }}%;background:{% if pct>=100 %}var(--green){% elif pct>=60 %}var(--blue){% else %}var(--accent2){% endif %}"></div></div>
            <div style="font-size:.7rem;color:var(--muted);margin-top:.2rem">{{ pct }}%</div>
          </td>
          <td>
            <form method="POST" action="{{ url_for('admin.set_target') }}" style="display:flex;gap:.4rem">
              <input type="hidden" name="employee_id" value="{{ emp.id }}">
              <input type="number" name="target_amount" class="ctrl" style="padding:.3rem .6rem;font-size:.82rem;width:110px" value="{{ target_val }}" placeholder="₹ target">
              <button type="submit" class="btn-success" style="padding:.3rem .7rem">Set</button>
            </form>
          </td>
        </tr>
        {% else %}
        <tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--muted)">No employees yet</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

w("app/templates/admin/training.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}Training Hub{% endblock %}
{% block page_title %}Training Hub{% endblock %}
{% block content %}
<div class="row g-4">
  <div class="col-lg-4">
    <div class="panel">
      <div class="panel-head"><h5>Add Resource</h5></div>
      <div class="panel-body">
        <form method="POST" action="{{ url_for('admin.add_training') }}">
          <label class="ctrl-label">Title *</label>
          <input type="text" name="title" class="ctrl mb-3" required placeholder="e.g. How to fold shirts">
          <label class="ctrl-label">Category</label>
          <input type="text" name="category" class="ctrl mb-3" placeholder="e.g. Store Operations">
          <label class="ctrl-label">Type</label>
          <select name="resource_type" class="ctrl mb-3">
            <option value="guide">📖 Guide</option>
            <option value="video">🎬 Video</option>
            <option value="policy">📋 Policy</option>
          </select>
          <label class="ctrl-label">Short Description</label>
          <input type="text" name="description" class="ctrl mb-3" placeholder="One line summary">
          <label class="ctrl-label">Content (Markdown)</label>
          <textarea name="content" class="ctrl mb-3" rows="8" placeholder="## Heading&#10;- Point 1&#10;- Point 2&#10;&#10;### Sub heading&#10;Text here..."></textarea>
          <button type="submit" class="btn-accent w-100"><i class="bi bi-plus-circle me-2"></i>Add Resource</button>
        </form>
      </div>
    </div>
  </div>
  <div class="col-lg-8">
    <div class="panel">
      <div class="panel-head"><h5>{{ resources|length }} Training Resources</h5></div>
      <div style="overflow-x:auto">
        <table class="data-table">
          <thead><tr><th>Title</th><th>Category</th><th>Type</th><th>Added</th><th>Action</th></tr></thead>
          <tbody>
            {% for r in resources %}
            <tr>
              <td style="font-weight:600">{{ r.title }}</td>
              <td><span class="badge-status badge-confirmed">{{ r.category }}</span></td>
              <td>{{ {'guide':'📖 Guide','video':'🎬 Video','policy':'📋 Policy'}.get(r.resource_type,'Guide') }}</td>
              <td style="font-size:.8rem;color:var(--muted)">{{ r.created_at.strftime('%d %b %Y') }}</td>
              <td>
                <form method="POST" action="{{ url_for('admin.delete_training', rid=r.id) }}" onsubmit="return confirm('Delete this resource?')">
                  <button type="submit" class="btn-danger"><i class="bi bi-trash3"></i></button>
                </form>
              </td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="text-align:center;padding:2rem;color:var(--muted)">No resources yet</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}
""")

print()
print("="*55)
print("  🎉 Step 5 Part 2 complete!")
print("  Now run:")
print("  1. python3 seed_step5.py   (seed sample data)")
print("  2. python3 run.py")
print("="*55)
