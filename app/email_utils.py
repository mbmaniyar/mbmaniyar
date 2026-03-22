# app/email_utils.py — Fixed version
# Uses the existing Flask app's mail instance instead of creating a new one
# Fixes: item.price -> item.unit_price, order.id -> order.order_number

STATUS_CONFIG = {
    "dispatched":       ("📦", "#1565C0", "Your order has been packed and handed to our delivery partner!"),
    "shipped":          ("🚚", "#6A1B9A", "Your order is in transit. It will reach you soon!"),
    "out_for_delivery": ("🛵", "#E65100", "Your order is OUT FOR DELIVERY today. Stay home!"),
    "delivered":        ("🎉", "#2E7D32", "Your order has been DELIVERED! Thank you for shopping at M.B Maniyar!"),
}

SUBJECT_MAP = {
    "dispatched":       "📦 Your Order Has Been Dispatched!",
    "shipped":          "🚚 Your Order is On Its Way!",
    "out_for_delivery": "🛵 Your Order is Out for Delivery Today!",
    "delivered":        "🎉 Your Order Has Been Delivered!",
}

def send_order_status_email(order):
    """
    Sends an order status update email to the customer.
    Uses the existing Flask app's mail instance — no new app created.
    Returns True if sent, False if skipped or failed.
    """

    # Normalize status: "Out for Delivery" -> "out_for_delivery"
    raw = (order.status or "").lower().replace(" ", "_")

    if raw not in STATUS_CONFIG:
        print(f"[Email] Skipping — status not tracked: {order.status}")
        return False

    # Get customer details
    from app.models import User
    customer = User.query.filter_by(id=order.user_id).first()

    # Skip walkin customers and those without real emails
    if not customer or not customer.email:
        print(f"[Email] No customer email for order {order.order_number}")
        return False

    if customer.email.endswith('@mbmaniyar.local'):
        print(f"[Email] Skipping internal email for {customer.email}")
        return False

    icon, color, message = STATUS_CONFIG[raw]
    subject = SUBJECT_MAP[raw]

    # ── Build items table rows ─────────────────────────────────────
    items_html = ""
    try:
        for item in order.items:
            name     = item.product.name
            size     = item.variant.size if item.variant else ""
            size_str = f" (Size {size})" if size else ""
            qty      = item.quantity
            # ✅ Fixed: use unit_price not price
            price    = float(item.unit_price) * item.quantity
            items_html += f"""
            <tr>
                <td style="padding:8px 12px;color:#333;border-bottom:1px solid #f0f0f0">
                    {name}{size_str}
                </td>
                <td style="padding:8px 12px;text-align:center;color:#555;border-bottom:1px solid #f0f0f0">
                    {qty}
                </td>
                <td style="padding:8px 12px;text-align:right;color:#333;border-bottom:1px solid #f0f0f0">
                    &#8377;{price:.2f}
                </td>
            </tr>"""
    except Exception as e:
        print(f"[Email] Items load error: {e}")
        items_html = "<tr><td colspan='3' style='padding:8px;color:#999'>Item details unavailable</td></tr>"

    total = float(order.total_amount or 0)

    # ── Build HTML email ───────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:20px;background:#f4f4f4;font-family:Arial,sans-serif;">
<table width="600" style="margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">

  <!-- Header -->
  <tr><td style="background:linear-gradient(135deg,#560D1E,#7B1C2E);padding:30px;text-align:center;">
    <h1 style="color:#E8B96A;margin:0;font-size:22px;letter-spacing:2px;font-weight:900;">
      M.B MANIYAR
    </h1>
    <p style="color:rgba(255,255,255,0.5);margin:4px 0 0;font-size:11px;letter-spacing:3px;text-transform:uppercase;">
      Cloth Store · Order Update
    </p>
  </td></tr>

  <!-- Body -->
  <tr><td style="padding:30px;">

    <p style="font-size:15px;color:#333;margin-bottom:6px;">
      Hello <strong>{customer.full_name}</strong>,
    </p>
    <p style="color:#666;margin-top:0;">Your order status has been updated.</p>

    <!-- Order number card -->
    <div style="background:#fdf6ee;border-left:4px solid #7B1C2E;padding:14px 20px;border-radius:0 8px 8px 0;margin:16px 0;">
      <p style="margin:0;font-size:11px;color:#9A8578;text-transform:uppercase;letter-spacing:1.5px;">
        Order Number
      </p>
      <!-- ✅ Fixed: order.order_number not order.id -->
      <p style="margin:4px 0 0;font-size:20px;font-weight:bold;color:#7B1C2E;font-family:monospace;">
        #{order.order_number}
      </p>
    </div>

    <!-- Status badge -->
    <div style="text-align:center;margin:24px 0 16px;">
      <span style="background:{color};color:#fff;padding:12px 32px;border-radius:50px;
                   font-size:16px;font-weight:bold;display:inline-block;">
        {icon} &nbsp;{order.status.replace('_',' ').title()}
      </span>
    </div>

    <!-- Message -->
    <div style="background:#f9f9f9;border-radius:8px;padding:16px;text-align:center;margin:16px 0;">
      <p style="margin:0;font-size:14px;color:#444;line-height:1.6;">{message}</p>
    </div>

    <!-- Items table -->
    <table width="100%" style="border:1px solid #eee;border-radius:8px;font-size:13px;border-collapse:collapse;margin-top:20px;">
      <tr style="background:#f9f9f9;">
        <th style="padding:10px 12px;text-align:left;color:#666;font-weight:600;">Item</th>
        <th style="padding:10px 12px;text-align:center;color:#666;font-weight:600;">Qty</th>
        <th style="padding:10px 12px;text-align:right;color:#666;font-weight:600;">Price</th>
      </tr>
      {items_html}
      <tr style="background:#fdf6ee;">
        <td colspan="2" style="padding:10px 12px;text-align:right;font-weight:700;color:#333;">
          Total Paid:
        </td>
        <td style="padding:10px 12px;text-align:right;font-weight:900;color:#7B1C2E;font-size:16px;">
          &#8377;{total:.2f}
        </td>
      </tr>
    </table>

  </td></tr>

  <!-- Footer -->
  <tr><td style="background:#f5f0eb;padding:20px;text-align:center;border-top:1px solid #e8ddd4;">
    <p style="margin:0;font-size:12px;color:#9A8578;">
      Questions? Call <strong style="color:#7B1C2E;">+91 94214 74678</strong>
    </p>
    <p style="margin:6px 0 0;font-size:11px;color:#beb0a6;">
      M.B Maniyar · Main Road, Opp. Bus Stand, Mantha, Jalna, Maharashtra
    </p>
  </td></tr>

</table>
</body>
</html>"""

    # ── Send using the EXISTING app's mail instance ────────────────
    # No new Flask() app created — reuses the one already running
    try:
        from app import mail
        from flask_mail import Message

        msg = Message(
            subject    = f"{subject} — Order #{order.order_number}",
            recipients = [customer.email],
            html       = html,
        )
        mail.send(msg)
        print(f"[Email] Sent to {customer.email} | {order.order_number} | {order.status}")
        return True

    except Exception as e:
        print(f"[Email] FAILED for {order.order_number}: {e}")
        return False
