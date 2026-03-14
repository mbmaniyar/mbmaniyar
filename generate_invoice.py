#!/usr/bin/env python3
# generate_invoice.py
# PURPOSE : Generate a professional PDF invoice and email it
# RUN WITH: python3 generate_invoice.py  (to test with dummy data)

import os
import io
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_mail import Mail, Message
from weasyprint import HTML

app = Flask(__name__)

# ── Mail config from .env ─────────────────────────────────────────
app.config['MAIL_SERVER']         = os.environ.get('MAIL_SERVER', 'smtp-relay.brevo.com')
app.config['MAIL_PORT']           = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS']        = True
app.config['MAIL_USE_SSL']        = False
app.config['MAIL_USERNAME']       = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD']       = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)


# ─────────────────────────────────────────────────────────────────
# STEP A: Build the invoice HTML
# This is the design of your PDF — edit colors/logo/layout freely
# ─────────────────────────────────────────────────────────────────
def build_invoice_html(order):
    """
    Takes an order dictionary and returns a complete HTML string.
    WeasyPrint will convert this HTML into a PDF.

    order = {
        'order_number': 'MBM-20250314-0001',
        'date':         '14 March 2025',
        'customer_name':'Krish Maniyar',
        'customer_email':'krish@gmail.com',
        'customer_phone':'+91 94214 74678',
        'items': [
            {'name':'Raymond Formal Shirt','size':'L','qty':2,'price':1299,'total':2598},
            {'name':'k satish Kurta',      'size':'M','qty':1,'price':899, 'total':899},
        ],
        'subtotal':  3497,
        'discount':  0,
        'tax':       0,
        'total':     3497,
        'payment_method': 'UPI',
        'payment_status': 'Paid',
    }
    """

    # ── Build the items rows HTML ──────────────────────────────────
    items_html = ""
    for i, item in enumerate(order['items']):
        # Alternate row background for readability
        bg = "#FFFFFF" if i % 2 == 0 else "#FDF6EE"
        items_html += f"""
        <tr style="background:{bg}">
          <td style="padding:10px 14px;font-size:13px;color:#2C1810">{item['name']}</td>
          <td style="padding:10px 14px;font-size:13px;text-align:center;color:#7A6358">{item['size']}</td>
          <td style="padding:10px 14px;font-size:13px;text-align:center;color:#7A6358">{item['qty']}</td>
          <td style="padding:10px 14px;font-size:13px;text-align:right;color:#2C1810">₹{item['price']:,.0f}</td>
          <td style="padding:10px 14px;font-size:13px;text-align:right;font-weight:bold;color:#7B1C2E">₹{item['total']:,.0f}</td>
        </tr>"""

    # ── Discount row (only show if discount > 0) ──────────────────
    discount_row = ""
    if order.get('discount', 0) > 0:
        discount_row = f"""
        <tr>
          <td colspan="4" style="padding:8px 14px;text-align:right;font-size:13px;color:#166534">
            Discount
          </td>
          <td style="padding:8px 14px;text-align:right;font-size:13px;color:#166534;font-weight:bold">
            -₹{order['discount']:,.0f}
          </td>
        </tr>"""

    # ── Full invoice HTML (designed to look great as a PDF) ───────
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        /* WeasyPrint uses these for page setup */
        @page {{
          size: A4;
          margin: 0;
        }}
        body {{
          font-family: 'Helvetica Neue', Arial, sans-serif;
          margin: 0;
          padding: 0;
          background: #FFFFFF;
          color: #2C1810;
        }}
        .page {{
          padding: 0;
          min-height: 297mm;
          position: relative;
        }}
      </style>
    </head>
    <body>
    <div class="page">

      <!-- ── HEADER (maroon band) ─────────────────────────────── -->
      <div style="background:linear-gradient(135deg,#560D1E,#7B1C2E);
                  padding:32px 40px;color:white">
        <table style="width:100%;border-collapse:collapse">
          <tr>
            <td style="vertical-align:top">
              <!-- Store name & address -->
              <div style="font-size:24px;font-weight:900;
                          color:#E8B96A;letter-spacing:1px">
                M.B Maniyar
              </div>
              <div style="font-size:11px;color:rgba(255,255,255,0.6);
                          letter-spacing:2px;text-transform:uppercase;
                          margin-top:2px">
                Cloth Store · Mantha
              </div>
              <div style="font-size:12px;color:rgba(255,255,255,0.7);
                          margin-top:10px;line-height:1.6">
                Main Road, Opposite Bus Stand<br>
                Mantha, Jalna District, Maharashtra<br>
                +91 94214 74678
              </div>
            </td>
            <td style="text-align:right;vertical-align:top">
              <!-- Invoice label -->
              <div style="font-size:32px;font-weight:900;
                          color:rgba(255,255,255,0.15);
                          letter-spacing:4px;text-transform:uppercase">
                INVOICE
              </div>
              <div style="font-size:16px;font-weight:700;
                          color:#E8B96A;margin-top:4px;
                          font-family:monospace">
                #{order['order_number']}
              </div>
              <div style="font-size:12px;color:rgba(255,255,255,0.6);
                          margin-top:6px">
                Date: {order['date']}
              </div>
              <!-- Payment status badge -->
              <div style="display:inline-block;
                          margin-top:10px;
                          background:{'#D1FAE5' if order['payment_status']=='Paid' else '#FEF3C7'};
                          color:{'#065F46' if order['payment_status']=='Paid' else '#92400E'};
                          padding:4px 14px;border-radius:20px;
                          font-size:11px;font-weight:700;
                          letter-spacing:1px;text-transform:uppercase">
                {order['payment_status']}
              </div>
            </td>
          </tr>
        </table>
      </div>

      <!-- ── BILL TO SECTION ──────────────────────────────────── -->
      <div style="padding:24px 40px;
                  background:#FDF6EE;
                  border-bottom:1px solid #E8DDD4">
        <table style="width:100%;border-collapse:collapse">
          <tr>
            <td style="vertical-align:top;width:50%">
              <div style="font-size:10px;font-weight:700;
                          text-transform:uppercase;letter-spacing:2px;
                          color:#9A8578;margin-bottom:6px">
                Bill To
              </div>
              <div style="font-size:15px;font-weight:700;
                          color:#2C1810">
                {order['customer_name']}
              </div>
              <div style="font-size:12px;color:#7A6358;
                          margin-top:3px;line-height:1.6">
                {order['customer_email']}<br>
                {order['customer_phone']}
              </div>
            </td>
            <td style="text-align:right;vertical-align:top">
              <div style="font-size:10px;font-weight:700;
                          text-transform:uppercase;letter-spacing:2px;
                          color:#9A8578;margin-bottom:6px">
                Payment Method
              </div>
              <div style="font-size:14px;font-weight:700;
                          color:#7B1C2E">
                {order['payment_method']}
              </div>
            </td>
          </tr>
        </table>
      </div>

      <!-- ── ITEMS TABLE ──────────────────────────────────────── -->
      <div style="padding:24px 40px">
        <table style="width:100%;border-collapse:collapse;
                      border-radius:10px;overflow:hidden;
                      border:1px solid #E8DDD4">
          <!-- Table header -->
          <thead>
            <tr style="background:#7B1C2E">
              <th style="padding:11px 14px;text-align:left;
                         font-size:11px;font-weight:700;
                         text-transform:uppercase;letter-spacing:1px;
                         color:#E8B96A">Item</th>
              <th style="padding:11px 14px;text-align:center;
                         font-size:11px;font-weight:700;
                         text-transform:uppercase;letter-spacing:1px;
                         color:#E8B96A">Size</th>
              <th style="padding:11px 14px;text-align:center;
                         font-size:11px;font-weight:700;
                         text-transform:uppercase;letter-spacing:1px;
                         color:#E8B96A">Qty</th>
              <th style="padding:11px 14px;text-align:right;
                         font-size:11px;font-weight:700;
                         text-transform:uppercase;letter-spacing:1px;
                         color:#E8B96A">Unit Price</th>
              <th style="padding:11px 14px;text-align:right;
                         font-size:11px;font-weight:700;
                         text-transform:uppercase;letter-spacing:1px;
                         color:#E8B96A">Total</th>
            </tr>
          </thead>
          <tbody>
            {items_html}
          </tbody>

          <!-- Totals -->
          <tfoot>
            <tr style="border-top:1px solid #E8DDD4">
              <td colspan="4"
                  style="padding:8px 14px;text-align:right;
                         font-size:13px;color:#7A6358">
                Subtotal
              </td>
              <td style="padding:8px 14px;text-align:right;
                         font-size:13px;color:#2C1810">
                ₹{order['subtotal']:,.0f}
              </td>
            </tr>
            {discount_row}
            <tr style="background:#FDF6EE;border-top:2px solid #C9963E">
              <td colspan="4"
                  style="padding:12px 14px;text-align:right;
                         font-size:15px;font-weight:900;color:#560D1E">
                TOTAL AMOUNT
              </td>
              <td style="padding:12px 14px;text-align:right;
                         font-size:18px;font-weight:900;color:#7B1C2E">
                ₹{order['total']:,.0f}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      <!-- ── THANK YOU FOOTER ──────────────────────────────────── -->
      <div style="margin:0 40px;padding:20px;
                  background:#FDF6EE;border-radius:10px;
                  border:1px solid #E8DDD4;text-align:center">
        <div style="font-size:16px;font-weight:700;color:#7B1C2E;
                    margin-bottom:4px">
          Thank you for shopping with us! 🙏
        </div>
        <div style="font-size:12px;color:#9A8578;line-height:1.6">
          For any queries, please contact us at
          <strong>+91 94214 74678</strong> or visit us at
          Main Road, Opposite Bus Stand, Mantha.
        </div>
      </div>

      <!-- ── PAGE FOOTER ───────────────────────────────────────── -->
      <div style="position:absolute;bottom:20px;left:0;right:0;
                  text-align:center;font-size:10px;color:#BEB0A6;
                  letter-spacing:1px">
        M.B Maniyar Cloth Store · Mantha, Jalna, Maharashtra
        · This is a computer-generated invoice
      </div>

    </div>
    </body>
    </html>
    """
    return html


# ─────────────────────────────────────────────────────────────────
# STEP B: Convert HTML → PDF bytes using WeasyPrint
# ─────────────────────────────────────────────────────────────────
def generate_pdf(order):
    """
    Converts the invoice HTML into PDF bytes in memory.
    Returns bytes that can be attached to an email or saved to disk.
    """
    html_string = build_invoice_html(order)

    # Write to memory (not a file on disk) for efficiency
    pdf_bytes = io.BytesIO()
    HTML(string=html_string).write_pdf(pdf_bytes)
    pdf_bytes.seek(0)  # rewind to beginning so it can be read

    return pdf_bytes.read()


# ─────────────────────────────────────────────────────────────────
# STEP C: Send the invoice email WITH the PDF attached
# ─────────────────────────────────────────────────────────────────
def send_invoice_email(order):
    """
    Generates PDF and sends it as an email attachment to the customer.
    """
    print(f"  📄 Generating PDF for order {order['order_number']}...")
    pdf_data = generate_pdf(order)
    print(f"  ✅ PDF generated ({len(pdf_data):,} bytes)")

    recipient = order['customer_email']
    print(f"  📧 Sending to {recipient}...")

    with app.app_context():
        msg = Message(
            subject    = f"🛍️ Order Confirmed #{order['order_number']} — M.B Maniyar",
            recipients = [recipient],
            # Plain text version (for email clients that don't support HTML)
            body = f"""
Dear {order['customer_name']},

Thank you for your order! Your invoice is attached as a PDF.

Order Number : {order['order_number']}
Date         : {order['date']}
Total Amount : ₹{order['total']:,.0f}
Payment      : {order['payment_method']} — {order['payment_status']}

Items ordered:
""" + "\n".join([
    f"  • {i['name']} (Size {i['size']}) x{i['qty']} = ₹{i['total']:,.0f}"
    for i in order['items']
]) + f"""

For any questions, call us at +91 94214 74678.
Thank you for shopping with M.B Maniyar Cloth Store!

Main Road, Opposite Bus Stand, Mantha, Jalna, Maharashtra
            """.strip(),

            # Rich HTML version
            html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
  <div style="background:#7B1C2E;padding:24px;border-radius:12px 12px 0 0;text-align:center">
    <h2 style="color:#E8B96A;margin:0;font-size:22px">M.B Maniyar Cloth Store</h2>
    <p style="color:rgba(255,255,255,0.6);margin:4px 0 0;font-size:12px;letter-spacing:2px">MANTHA · JALNA</p>
  </div>
  <div style="background:#FDF6EE;padding:24px;border:1px solid #E8DDD4;border-top:none">
    <p style="font-size:16px;color:#2C1810">Dear <strong>{order['customer_name']}</strong>,</p>
    <p style="color:#5A4A42">Your order has been confirmed! 🎉 Please find your invoice attached as a PDF.</p>
    <div style="background:#fff;border-radius:10px;border:1px solid #E8DDD4;padding:16px;margin:16px 0">
      <table style="width:100%">
        <tr><td style="color:#9A8578;font-size:13px">Order Number</td>
            <td style="font-weight:bold;font-family:monospace;color:#7B1C2E;text-align:right">#{order['order_number']}</td></tr>
        <tr><td style="color:#9A8578;font-size:13px;padding-top:6px">Total Amount</td>
            <td style="font-weight:900;font-size:18px;color:#7B1C2E;text-align:right;padding-top:6px">₹{order['total']:,.0f}</td></tr>
        <tr><td style="color:#9A8578;font-size:13px;padding-top:6px">Payment</td>
            <td style="text-align:right;padding-top:6px"><span style="background:#D1FAE5;color:#065F46;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700">{order['payment_status']}</span></td></tr>
      </table>
    </div>
    <p style="font-size:13px;color:#9A8578;text-align:center;margin-top:20px">
      Questions? Call us at <strong style="color:#7B1C2E">+91 94214 74678</strong>
    </p>
  </div>
</div>
            """
        )

        # ── Attach the PDF ─────────────────────────────────────────
        # 'application/pdf' tells the email client it's a PDF file
        msg.attach(
            filename    = f"Invoice_{order['order_number']}.pdf",
            content_type= "application/pdf",
            data        = pdf_data
        )

        mail.send(msg)

    print(f"  ✅ Invoice email sent to {recipient}!")
    return True


# ─────────────────────────────────────────────────────────────────
# TEST — Run this file directly to test with dummy order data
# ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':

    print("=" * 50)
    print("  MBM — PDF Invoice Generator Test")
    print("=" * 50)

    # Dummy order data to test with
    test_order = {
        'order_number'   : 'MBM-20250314-0001',
        'date'           : '14 March 2025',
        'customer_name'  : 'Krish Maniyar',
        'customer_email' : os.environ.get('TEST_EMAIL', 'test@example.com'),
        'customer_phone' : '+91 98765 43210',
        'items': [
            {
                'name' : 'Raymond Premium Formal Shirt',
                'size' : 'L',
                'qty'  : 2,
                'price': 1299,
                'total': 2598
            },
            {
                'name' : 'k satish Cotton Kurta',
                'size' : 'M',
                'qty'  : 1,
                'price': 899,
                'total': 899
            },
            {
                'name' : 'Peter England Formal Trousers',
                'size' : '32',
                'qty'  : 1,
                'price': 1599,
                'total': 1599
            },
        ],
        'subtotal'       : 5096,
        'discount'       : 200,
        'tax'            : 0,
        'total'          : 4896,
        'payment_method' : 'UPI',
        'payment_status' : 'Paid',
    }

    # First save PDF locally so you can preview it
    print("\n📄 Saving PDF locally to preview...")
    pdf_bytes = generate_pdf(test_order)
    with open('test_invoice.pdf', 'wb') as f:
        f.write(pdf_bytes)
    print(f"  ✅ Saved as: test_invoice.pdf  ({len(pdf_bytes):,} bytes)")
    print(f"  👀 Open it: xdg-open test_invoice.pdf")

    # Then send via email
    print("\n📧 Sending invoice email...")
    send_invoice_email(test_order)

    print()
    print("=" * 50)
    print("  Done! Check your inbox for the invoice email.")
    print("  Also open test_invoice.pdf to preview the design.")
    print("=" * 50)
