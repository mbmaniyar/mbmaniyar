# build_order_status_email.py
# This script creates the HTML email template for order status updates.
# Run it once to generate the file, then you can delete this script.

import os

# Make sure the email templates folder exists
os.makedirs('app/templates/email', exist_ok=True)

template = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Order Update — M.B Maniyar</title>
</head>
<body style="margin:0; padding:0; background:#f4f4f4; font-family: Arial, sans-serif;">

  <!-- Outer wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4; padding:30px 0;">
    <tr>
      <td align="center">

        <!-- Email card -->
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#ffffff; border-radius:8px; overflow:hidden;
                      box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

          <!-- ── HEADER ── -->
          <tr>
            <td style="background:#7B1C2E; padding:30px 40px; text-align:center;">
              <h1 style="color:#FFD700; margin:0; font-size:26px; letter-spacing:2px;">
                M.B MANIYAR
              </h1>
              <p style="color:#f5c6cb; margin:6px 0 0; font-size:13px; letter-spacing:1px;">
                CLOTH STORE — ORDER UPDATE
              </p>
            </td>
          </tr>

          <!-- ── GREETING ── -->
          <tr>
            <td style="padding:30px 40px 10px;">
              <p style="font-size:16px; color:#333; margin:0;">
                Hello <strong>{{ customer_name }}</strong>,
              </p>
              <p style="font-size:15px; color:#555; margin:10px 0 0;">
                Great news! Your order status has been updated.
              </p>
            </td>
          </tr>

          <!-- ── ORDER NUMBER BOX ── -->
          <tr>
            <td style="padding:10px 40px;">
              <div style="background:#fdf3f5; border-left:4px solid #7B1C2E;
                          padding:14px 20px; border-radius:4px;">
                <p style="margin:0; font-size:13px; color:#888;">Order Number</p>
                <p style="margin:4px 0 0; font-size:20px; font-weight:bold;
                           color:#7B1C2E; letter-spacing:1px;">
                  #{{ order_id }}
                </p>
              </div>
            </td>
          </tr>

          <!-- ── STATUS BADGE ── -->
          <tr>
            <td style="padding:20px 40px 10px; text-align:center;">
              <p style="margin:0 0 8px; font-size:13px; color:#888; text-transform:uppercase;
                         letter-spacing:1px;">Current Status</p>
              <span style="display:inline-block; background:{{ status_color }};
                            color:#fff; padding:10px 28px; border-radius:25px;
                            font-size:17px; font-weight:bold; letter-spacing:1px;">
                {{ status_icon }} {{ status }}
              </span>
            </td>
          </tr>

          <!-- ── PROGRESS TRACKER ── -->
          <tr>
            <td style="padding:20px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <!-- Each step: circle + label -->
                  {% set steps = [
                    ("Confirmed",       "✅"),
                    ("Dispatched",      "📦"),
                    ("Shipped",         "🚚"),
                    ("Out for Delivery","🛵"),
                    ("Delivered",       "🎉")
                  ] %}
                  {% for step_name, step_icon in steps %}
                  <td style="text-align:center; width:20%;">
                    <!-- Circle -->
                    <div style="width:36px; height:36px; border-radius:50%; margin:0 auto;
                                 display:flex; align-items:center; justify-content:center;
                                 font-size:16px;
                                 background: {{ '#7B1C2E' if step_name == status else
                                               ('#d4a5ac' if loop.index < steps|length and
                                                steps|map(attribute=0)|list|index(status)|int >= loop.index0
                                                else '#e0e0e0') }};
                                 color: white; line-height:36px;">
                      {{ step_icon }}
                    </div>
                    <!-- Label -->
                    <p style="margin:6px 0 0; font-size:10px; color:
                               {{ '#7B1C2E' if step_name == status else '#999' }};
                               font-weight: {{ 'bold' if step_name == status else 'normal' }};">
                      {{ step_name }}
                    </p>
                  </td>
                  {% endfor %}
                </tr>
              </table>
            </td>
          </tr>

          <!-- ── STATUS MESSAGE ── -->
          <tr>
            <td style="padding:10px 40px 20px;">
              <div style="background:#f9f9f9; border-radius:6px; padding:16px 20px;
                           text-align:center;">
                <p style="margin:0; font-size:15px; color:#444; line-height:1.6;">
                  {{ status_message }}
                </p>
              </div>
            </td>
          </tr>

          <!-- ── ORDER SUMMARY ── -->
          <tr>
            <td style="padding:0 40px 20px;">
              <p style="font-size:13px; color:#888; text-transform:uppercase;
                         letter-spacing:1px; margin:0 0 10px;">Order Summary</p>
              <table width="100%" cellpadding="8" cellspacing="0"
                     style="border:1px solid #eee; border-radius:6px; font-size:14px;">
                <tr style="background:#f9f9f9;">
                  <th style="text-align:left; color:#555; font-weight:600;">Item</th>
                  <th style="text-align:center; color:#555; font-weight:600;">Qty</th>
                  <th style="text-align:right; color:#555; font-weight:600;">Price</th>
                </tr>
                {% for item in items %}
                <tr>
                  <td style="color:#333;">{{ item.name }}
                    {% if item.size %}<span style="color:#888; font-size:12px;">
                      ({{ item.size }})</span>{% endif %}
                  </td>
                  <td style="text-align:center; color:#555;">{{ item.quantity }}</td>
                  <td style="text-align:right; color:#333;">₹{{ "%.2f"|format(item.price) }}</td>
                </tr>
                {% endfor %}
                <tr style="border-top:2px solid #eee;">
                  <td colspan="2" style="text-align:right; font-weight:bold; color:#333;">
                    Total Paid:</td>
                  <td style="text-align:right; font-weight:bold; color:#7B1C2E; font-size:16px;">
                    ₹{{ "%.2f"|format(total_amount) }}
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- ── PICKUP / DELIVERY NOTE ── -->
          {% if pickup_note %}
          <tr>
            <td style="padding:0 40px 20px;">
              <div style="background:#fff8e1; border:1px solid #ffe082; border-radius:6px;
                           padding:14px 20px;">
                <p style="margin:0; font-size:14px; color:#6d4c00;">
                  📍 <strong>Pickup Reminder:</strong> {{ pickup_note }}
                </p>
              </div>
            </td>
          </tr>
          {% endif %}

          <!-- ── FOOTER ── -->
          <tr>
            <td style="background:#f9f9f9; padding:20px 40px; text-align:center;
                        border-top:1px solid #eee;">
              <p style="margin:0; font-size:13px; color:#888;">
                Questions? Call us at <strong>+91 94214 74678</strong>
              </p>
              <p style="margin:6px 0 0; font-size:12px; color:#aaa;">
                M.B Maniyar Cloth Store · Main Road, Opp. Bus Stand, Mantha, Jalna
              </p>
              <p style="margin:10px 0 0; font-size:11px; color:#ccc;">
                This is an automated message. Please do not reply to this email.
              </p>
            </td>
          </tr>

        </table>
        <!-- end card -->

      </td>
    </tr>
  </table>

</body>
</html>'''

# Write the template file
with open('app/templates/email/order_status.html', 'w') as f:
    f.write(template)

print("✅ Created: app/templates/email/order_status.html")
print("   This is the HTML email your customers will receive.")
print()
print("Next: run Part 2 to build the send function.")
