# app/email_utils.py — Final working version
import os
from dotenv import load_dotenv
from flask import Flask
from flask_mail import Mail, Message

load_dotenv()

STATUS_CONFIG = {
    "dispatched":       ("📦", "#1565C0", "Your order has been packed and is now on its way!"),
    "shipped":          ("🚚", "#6A1B9A", "Your order is in transit. Hang tight!"),
    "out_for_delivery": ("🛵", "#E65100", "Your order is OUT FOR DELIVERY today!"),
    "delivered":        ("🎉", "#2E7D32", "Your order has been DELIVERED! Thank you for shopping at M.B Maniyar!"),
}

SUBJECT_MAP = {
    "dispatched":       "📦 Your Order Has Been Dispatched!",
    "shipped":          "🚚 Your Order is On Its Way!",
    "out_for_delivery": "🛵 Your Order is Out for Delivery Today!",
    "delivered":        "🎉 Your Order Has Been Delivered!",
}

def send_order_status_email(order):
    # Normalize: "Dispatched" -> "dispatched", "Out for Delivery" -> "out_for_delivery"
    raw = (order.status or "").lower().replace(" ", "_")

    if raw not in STATUS_CONFIG:
        print(f"[Email] Skipping — status not tracked: {order.status}")
        return False

    # Get customer
    from app.models import User
    customer = User.query.filter_by(id=order.user_id).first()
    if not customer or not customer.email:
        print(f"[Email] No customer email for order #{order.id}")
        return False

    icon, color, message = STATUS_CONFIG[raw]
    subject = SUBJECT_MAP[raw]

    # Build items rows
    items_html = ""
    try:
        for item in order.items:
            name = item.product.name
            size = getattr(item, "size", "") or ""
            size_str = f" ({size})" if size else ""
            qty = item.quantity
            price = item.price * item.quantity
            items_html += f"""
            <tr>
                <td style="padding:8px;color:#333;">{name}{size_str}</td>
                <td style="padding:8px;text-align:center;color:#555;">{qty}</td>
                <td style="padding:8px;text-align:right;color:#333;">&#8377;{price:.2f}</td>
            </tr>"""
    except Exception as e:
        print(f"[Email] Items load error: {e}")

    total = getattr(order, "total_amount", 0)

    # Build full HTML inline — no template needed
    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:20px;background:#f4f4f4;font-family:Arial,sans-serif;">
<table width="600" style="margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;">
  <tr><td style="background:#7B1C2E;padding:30px;text-align:center;">
    <h1 style="color:#FFD700;margin:0;font-size:24px;letter-spacing:2px;">M.B MANIYAR</h1>
    <p style="color:#f5c6cb;margin:6px 0 0;font-size:13px;">CLOTH STORE — ORDER UPDATE</p>
  </td></tr>
  <tr><td style="padding:30px;">
    <p style="font-size:16px;color:#333;">Hello <strong>{customer.username}</strong>,</p>
    <p style="color:#555;">Your order status has been updated.</p>
    <div style="background:#fdf3f5;border-left:4px solid #7B1C2E;padding:14px 20px;border-radius:4px;margin:15px 0;">
      <p style="margin:0;font-size:13px;color:#888;">Order Number</p>
      <p style="margin:4px 0 0;font-size:20px;font-weight:bold;color:#7B1C2E;">#{order.id}</p>
    </div>
    <div style="text-align:center;margin:20px 0;">
      <span style="background:{color};color:#fff;padding:10px 28px;border-radius:25px;font-size:17px;font-weight:bold;">
        {icon} {order.status.replace("_"," ").title()}
      </span>
    </div>
    <div style="background:#f9f9f9;border-radius:6px;padding:16px;text-align:center;margin:15px 0;">
      <p style="margin:0;font-size:15px;color:#444;">{message}</p>
    </div>
    <table width="100%" style="border:1px solid #eee;border-radius:6px;font-size:14px;border-collapse:collapse;">
      <tr style="background:#f9f9f9;">
        <th style="padding:8px;text-align:left;color:#555;">Item</th>
        <th style="padding:8px;text-align:center;color:#555;">Qty</th>
        <th style="padding:8px;text-align:right;color:#555;">Price</th>
      </tr>
      {items_html}
      <tr style="border-top:2px solid #eee;">
        <td colspan="2" style="padding:8px;text-align:right;font-weight:bold;">Total Paid:</td>
        <td style="padding:8px;text-align:right;font-weight:bold;color:#7B1C2E;font-size:16px;">&#8377;{total:.2f}</td>
      </tr>
    </table>
  </td></tr>
  <tr><td style="background:#f9f9f9;padding:20px;text-align:center;border-top:1px solid #eee;">
    <p style="margin:0;font-size:13px;color:#888;">Questions? Call <strong>+91 94214 74678</strong></p>
    <p style="margin:6px 0 0;font-size:12px;color:#aaa;">M.B Maniyar · Main Road, Opp. Bus Stand, Mantha, Jalna</p>
  </td></tr>
</table>
</body>
</html>"""

    try:
        mail_app = Flask(__name__)
        mail_app.config["MAIL_SERVER"]         = os.environ.get("MAIL_SERVER", "smtp-relay.brevo.com")
        mail_app.config["MAIL_PORT"]           = int(os.environ.get("MAIL_PORT", 587))
        mail_app.config["MAIL_USE_TLS"]        = True
        mail_app.config["MAIL_USE_SSL"]        = False
        mail_app.config["MAIL_USERNAME"]       = os.environ.get("MAIL_USERNAME")
        mail_app.config["MAIL_PASSWORD"]       = os.environ.get("MAIL_PASSWORD")
        mail_app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")

        mail = Mail(mail_app)

        with mail_app.app_context():
            msg = Message(
                subject    = f"{subject} — Order #{order.id}",
                recipients = [customer.email],
                html       = html,
            )
            mail.send(msg)

        print(f"[Email] ✅ Sent to {customer.email} | Order #{order.id} | {order.status}")
        return True

    except Exception as e:
        print(f"[Email] ❌ FAILED for Order #{order.id}: {e}")
        return False
