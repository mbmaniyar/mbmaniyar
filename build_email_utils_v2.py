# build_email_utils_v2.py
# Rewrites email_utils.py using the EXACT same mail approach as test_email.py

with open('app/email_utils.py', 'w') as f:
    f.write('''# app/email_utils.py
import os
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_mail import Mail, Message

# Load .env variables (same as test_email.py)
load_dotenv()

STATUS_CONFIG = {
    "Dispatched": {
        "icon":    "📦",
        "color":   "#1565C0",
        "message": "Your order has been packed and handed over to our delivery partner. It is now on its way!"
    },
    "Shipped": {
        "icon":    "🚚",
        "color":   "#6A1B9A",
        "message": "Your order is in transit. Our delivery partner is moving it closer to you. Hang tight!"
    },
    "Out for Delivery": {
        "icon":    "🛵",
        "color":   "#E65100",
        "message": "Your order is OUT FOR DELIVERY today! Please make sure someone is available to receive it."
    },
    "Delivered": {
        "icon":    "🎉",
        "color":   "#2E7D32",
        "message": "Your order has been DELIVERED! Thank you for shopping at M.B Maniyar!"
    },
}


def send_order_status_email(order):
    """
    Sends order status update email to customer.
    Uses a self-contained Flask+Mail setup (same as test_email.py).
    Never crashes the app — always returns True/False.
    """

    # Guard: only send for the 4 tracked statuses
    if order.status not in STATUS_CONFIG:
        print(f"[Email] Skipping status: {order.status}")
        return False

    # Guard: get customer
    from app.models import User
    customer = User.query.get(order.user_id) if order.user_id else None
    if not customer or not customer.email:
        print(f"[Email] No customer email for order #{order.id}")
        return False

    config = STATUS_CONFIG[order.status]

    # Build items list for the email table
    items = []
    try:
        for item in order.items:
            items.append({
                "name":     item.product.name,
                "size":     getattr(item, "size", None),
                "quantity": item.quantity,
                "price":    item.price * item.quantity,
            })
    except Exception as e:
        print(f"[Email] Could not load order items: {e}")
        items = []

    # Pickup note
    pickup_note = None
    if getattr(order, "pickup", False):
        pickup_note = (
            "This is a PICK-UP order. Please collect from: "
            "Main Road, Opp. Bus Stand, Mantha, Jalna."
        )

    try:
        # ── Build a standalone Flask app (same pattern as test_email.py) ──
        mail_app = Flask(__name__, template_folder=\'templates\')
        mail_app.config[\'MAIL_SERVER\']         = os.environ.get(\'MAIL_SERVER\', \'smtp-relay.brevo.com\')
        mail_app.config[\'MAIL_PORT\']            = int(os.environ.get(\'MAIL_PORT\', 587))
        mail_app.config[\'MAIL_USE_TLS\']         = True
        mail_app.config[\'MAIL_USE_SSL\']         = False
        mail_app.config[\'MAIL_USERNAME\']        = os.environ.get(\'MAIL_USERNAME\')
        mail_app.config[\'MAIL_PASSWORD\']        = os.environ.get(\'MAIL_PASSWORD\')
        mail_app.config[\'MAIL_DEFAULT_SENDER\']  = os.environ.get(\'MAIL_DEFAULT_SENDER\')

        mail = Mail(mail_app)

        with mail_app.app_context():
            # Render the HTML template
            html_body = render_template(
                "email/order_status.html",
                customer_name  = customer.username,
                order_id       = order.id,
                status         = order.status,
                status_icon    = config["icon"],
                status_color   = config["color"],
                status_message = config["message"],
                items          = items,
                total_amount   = getattr(order, "total_amount", 0),
                pickup_note    = pickup_note,
            )

            subject_map = {
                "Dispatched":       "📦 Your Order Has Been Dispatched!",
                "Shipped":          "🚚 Your Order is On Its Way!",
                "Out for Delivery": "🛵 Your Order is Out for Delivery Today!",
                "Delivered":        "🎉 Your Order Has Been Delivered!",
            }

            msg = Message(
                subject    = f"{subject_map[order.status]} — Order #{order.id}",
                recipients = [customer.email],
                html       = html_body,
            )
            mail.send(msg)

        print(f"[Email] ✅ Sent to {customer.email} | Order #{order.id} | {order.status}")
        return True

    except Exception as e:
        print(f"[Email] ❌ Failed for Order #{order.id}: {e}")
        return False
''')

print("✅ app/email_utils.py rewritten!")
print("Now restart run.py and test by changing an order status.")
