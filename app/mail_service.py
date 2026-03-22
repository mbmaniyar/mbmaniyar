# app/mail_service.py
# Handles order confirmation emails sent at checkout
# Uses the existing Flask app's mail instance (no new Flask app created)

def send_order_confirmation(user, order):
    """
    Sends an order confirmation email with itemized receipt.
    Called right after a customer places an order at checkout.
    Returns True if sent, False if skipped or failed.
    """

    # Skip internal/walkin emails
    if not user.email or user.email.endswith('@mbmaniyar.local'):
        print(f"  [Mail] Skipping — internal email: {user.email}")
        return False

    try:
        from app import mail
        from flask import current_app
        from flask_mail import Message

        # Skip if mail not configured
        if not current_app.config.get('MAIL_ENABLED'):
            print(f"  [Mail] MAIL_ENABLED is False — skipping confirmation")
            return False

        # ── Build items table ──────────────────────────────────────
        items_html = ""
        for item in order.items:
            try:
                name     = item.product.name
                size     = item.variant.size if item.variant else ""
                size_str = f" (Size {size})" if size else ""
                qty      = item.quantity
                price    = float(item.unit_price) * qty
                items_html += f"""
                <tr>
                  <td style="padding:9px 12px;border-bottom:1px solid #f0e8e0;color:#2C1810">
                    {name}{size_str}
                  </td>
                  <td style="padding:9px 12px;border-bottom:1px solid #f0e8e0;text-align:center;color:#7A6358">
                    {qty}
                  </td>
                  <td style="padding:9px 12px;border-bottom:1px solid #f0e8e0;text-align:right;font-weight:600;color:#2C1810">
                    &#8377;{price:.2f}
                  </td>
                </tr>"""
            except Exception as e:
                print(f"  [Mail] Item row error: {e}")

        subtotal = float(order.subtotal or 0)
        discount = float(order.discount_amount or 0)
        total    = float(order.total_amount or 0)

        discount_row = ""
        if discount > 0:
            discount_row = f"""
            <tr>
              <td colspan="2" style="padding:8px 12px;text-align:right;color:#166534">Discount</td>
              <td style="padding:8px 12px;text-align:right;color:#166534;font-weight:600">
                -&#8377;{discount:.2f}
              </td>
            </tr>"""

        from datetime import datetime
        order_date = order.created_at.strftime('%d %B %Y') if order.created_at else datetime.now().strftime('%d %B %Y')

        # ── Full HTML email ────────────────────────────────────────
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:20px;background:#F5F0EB;font-family:Arial,sans-serif;">
<table width="600" style="margin:0 auto;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

  <!-- Header -->
  <tr><td style="background:linear-gradient(135deg,#560D1E,#7B1C2E);padding:28px 32px;">
    <table width="100%"><tr>
      <td>
        <div style="font-size:20px;font-weight:900;color:#E8B96A;letter-spacing:1px;">M.B Maniyar</div>
        <div style="font-size:10px;color:rgba(255,255,255,0.45);letter-spacing:3px;text-transform:uppercase;margin-top:2px;">
          Cloth Store · Mantha
        </div>
      </td>
      <td style="text-align:right;">
        <div style="font-size:10px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:1.5px;">
          Order Confirmed
        </div>
        <div style="font-size:16px;font-weight:700;color:#E8B96A;font-family:monospace;margin-top:2px;">
          #{order.order_number}
        </div>
        <div style="font-size:11px;color:rgba(255,255,255,0.4);margin-top:4px;">{order_date}</div>
      </td>
    </tr></table>
  </td></tr>

  <!-- Body -->
  <tr><td style="padding:28px 32px;">

    <!-- Greeting -->
    <p style="font-size:15px;color:#2C1810;margin:0 0 6px;">
      Dear <strong>{user.full_name}</strong>,
    </p>
    <p style="color:#7A6358;margin:0 0 20px;font-size:14px;line-height:1.6;">
      Thank you for your order! 🎉 We have received it and it is being prepared.
      Please visit us at <strong>Main Road, Opposite Bus Stand, Mantha</strong> to pick it up.
    </p>

    <!-- Status badge -->
    <div style="text-align:center;margin-bottom:20px;">
      <span style="background:#D1FAE5;color:#065F46;padding:7px 20px;border-radius:50px;
                   font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;">
        ✅ Order Confirmed
      </span>
    </div>

    <!-- Items table -->
    <table width="100%" style="border:1px solid #E8DDD4;border-radius:8px;border-collapse:collapse;font-size:13px;">
      <thead>
        <tr style="background:#7B1C2E;">
          <th style="padding:10px 12px;text-align:left;color:#E8B96A;font-weight:600;">Item</th>
          <th style="padding:10px 12px;text-align:center;color:#E8B96A;font-weight:600;">Qty</th>
          <th style="padding:10px 12px;text-align:right;color:#E8B96A;font-weight:600;">Price</th>
        </tr>
      </thead>
      <tbody>{items_html}</tbody>
      <tfoot>
        <tr>
          <td colspan="2" style="padding:8px 12px;text-align:right;color:#7A6358;font-size:13px;">Subtotal</td>
          <td style="padding:8px 12px;text-align:right;color:#2C1810;">&#8377;{subtotal:.2f}</td>
        </tr>
        {discount_row}
        <tr style="background:#FDF6EE;border-top:2px solid #C9963E;">
          <td colspan="2" style="padding:11px 12px;text-align:right;font-weight:700;font-size:15px;color:#560D1E;">
            Total
          </td>
          <td style="padding:11px 12px;text-align:right;font-weight:900;font-size:17px;color:#7B1C2E;">
            &#8377;{total:.2f}
          </td>
        </tr>
      </tfoot>
    </table>

    <!-- Payment info -->
    <div style="background:#FDF6EE;border-radius:8px;padding:14px 16px;margin-top:16px;">
      <table width="100%" style="font-size:13px;">
        <tr>
          <td style="color:#9A8578;">Payment Method</td>
          <td style="text-align:right;font-weight:600;color:#2C1810;text-transform:capitalize;">
            {order.payment_method or 'Cash'}
          </td>
        </tr>
        <tr>
          <td style="color:#9A8578;padding-top:6px;">Payment Status</td>
          <td style="text-align:right;padding-top:6px;">
            <span style="background:#FEF3C7;color:#92400E;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700;">
              {(order.payment_status or 'Pending').title()}
            </span>
          </td>
        </tr>
      </table>
    </div>

    <p style="font-size:13px;color:#9A8578;text-align:center;margin-top:20px;">
      Questions? Call us at <strong style="color:#7B1C2E;">+91 94214 74678</strong>
    </p>

  </td></tr>

  <!-- Footer -->
  <tr><td style="background:#F5F0EB;padding:16px 32px;text-align:center;border-top:1px solid #E8DDD4;">
    <p style="margin:0;font-size:11px;color:#9A8578;">
      M.B Maniyar Cloth Store · Main Road, Opposite Bus Stand, Mantha, Jalna, Maharashtra
    </p>
    <p style="margin:4px 0 0;font-size:10px;color:#BEB0A6;">
      This is an automated confirmation. Please do not reply to this email.
    </p>
  </td></tr>

</table>
</body>
</html>"""

        msg = Message(
            subject    = f"🛍️ Order Confirmed #{order.order_number} — M.B Maniyar",
            recipients = [user.email],
            html       = html,
        )
        mail.send(msg)
        print(f"  [Mail] ✅ Order confirmation sent to {user.email} — {order.order_number}")
        return True

    except Exception as e:
        print(f"  [Mail] ❌ Confirmation failed for {order.order_number}: {e}")
        return False


def send_welcome_email(user):
    """Sends a welcome email after email verification."""
    if not user.email or user.email.endswith('@mbmaniyar.local'):
        return False
    try:
        from app import mail
        from flask import current_app
        from flask_mail import Message
        if not current_app.config.get('MAIL_ENABLED'):
            return False
        msg = Message(
            subject    = "🎉 Welcome to M.B Maniyar Cloth Store!",
            recipients = [user.email],
            html       = f"""
<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto">
  <div style="background:#7B1C2E;padding:24px;border-radius:12px 12px 0 0;text-align:center">
    <h2 style="color:#E8B96A;margin:0">M.B Maniyar Cloth Store</h2>
    <p style="color:rgba(255,255,255,0.5);margin:4px 0 0;font-size:11px;letter-spacing:2px">MANTHA · JALNA</p>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #E8DDD4;border-top:none;border-radius:0 0 12px 12px;text-align:center">
    <div style="font-size:40px;margin-bottom:12px">🎉</div>
    <h3 style="color:#2C1810;margin:0 0 10px">Welcome to the family, {user.full_name}!</h3>
    <p style="color:#7A6358;font-size:14px;line-height:1.7">
      Your email has been verified. You can now shop our full collection
      of premium garments and track your orders online.
    </p>
    <a href="https://mbmaniyar.onrender.com/shop"
       style="display:inline-block;margin-top:16px;background:#7B1C2E;color:#E8B96A;
              text-decoration:none;padding:10px 28px;border-radius:50px;font-weight:700;font-size:14px">
      Start Shopping →
    </a>
    <p style="font-size:12px;color:#9A8578;margin-top:20px">
      Questions? Call <strong>+91 94214 74678</strong>
    </p>
  </div>
</div>"""
        )
        mail.send(msg)
        print(f"  [Mail] ✅ Welcome email sent to {user.email}")
        return True
    except Exception as e:
        print(f"  [Mail] ❌ Welcome email failed: {e}")
        return False


def send_verification_email(user, token):
    """Sends email verification link on registration."""
    if not user.email or user.email.endswith('@mbmaniyar.local'):
        return False
    try:
        from app import mail
        from flask import current_app, url_for
        from flask_mail import Message
        if not current_app.config.get('MAIL_ENABLED'):
            return False
        verify_url = url_for('auth.verify_email', token=token, _external=True)
        msg = Message(
            subject    = "✅ Verify Your Email — M.B Maniyar",
            recipients = [user.email],
            html       = f"""
<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto">
  <div style="background:#7B1C2E;padding:24px;border-radius:12px 12px 0 0;text-align:center">
    <h2 style="color:#E8B96A;margin:0">M.B Maniyar Cloth Store</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #E8DDD4;border-top:none;border-radius:0 0 12px 12px">
    <h3 style="color:#2C1810">Verify your email address</h3>
    <p style="color:#7A6358;font-size:14px;line-height:1.7">
      Hi <strong>{user.full_name}</strong>, click the button below to verify your email and activate your account.
    </p>
    <div style="text-align:center;margin:24px 0">
      <a href="{verify_url}"
         style="background:#7B1C2E;color:#E8B96A;text-decoration:none;
                padding:12px 32px;border-radius:50px;font-weight:700;font-size:14px">
        Verify My Email →
      </a>
    </div>
    <p style="color:#9A8578;font-size:12px;">
      Link expires in 24 hours. If you didn't register, ignore this email.
    </p>
  </div>
</div>"""
        )
        mail.send(msg)
        print(f"  [Mail] ✅ Verification email sent to {user.email}")
        return True
    except Exception as e:
        print(f"  [Mail] ❌ Verification email failed: {e}")
        return False


def send_password_reset_email(user, token):
    """Sends password reset link."""
    if not user.email or user.email.endswith('@mbmaniyar.local'):
        return False
    try:
        from app import mail
        from flask import current_app, url_for
        from flask_mail import Message
        if not current_app.config.get('MAIL_ENABLED'):
            return False
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        msg = Message(
            subject    = "🔐 Reset Your Password — M.B Maniyar",
            recipients = [user.email],
            html       = f"""
<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto">
  <div style="background:#7B1C2E;padding:24px;border-radius:12px 12px 0 0;text-align:center">
    <h2 style="color:#E8B96A;margin:0">M.B Maniyar Cloth Store</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #E8DDD4;border-top:none;border-radius:0 0 12px 12px">
    <h3 style="color:#2C1810">Password Reset Request</h3>
    <p style="color:#7A6358;font-size:14px;line-height:1.7">
      Hi <strong>{user.full_name}</strong>, click below to reset your password. Link expires in 1 hour.
    </p>
    <div style="text-align:center;margin:24px 0">
      <a href="{reset_url}"
         style="background:#7B1C2E;color:#E8B96A;text-decoration:none;
                padding:12px 32px;border-radius:50px;font-weight:700;font-size:14px">
        Reset My Password →
      </a>
    </div>
    <div style="background:#FEF2F2;border-radius:8px;padding:12px 16px;margin-top:16px">
      <p style="color:#991B1B;font-size:12px;margin:0">
        If you did not request this, your account is safe — just ignore this email.
      </p>
    </div>
  </div>
</div>"""
        )
        mail.send(msg)
        print(f"  [Mail] ✅ Password reset email sent to {user.email}")
        return True
    except Exception as e:
        print(f"  [Mail] ❌ Password reset email failed: {e}")
        return False
