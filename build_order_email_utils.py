# build_order_email_utils.py
# Creates/updates app/email_utils.py with the order status email function.
# Run once to generate the file.

with open('app/email_utils.py', 'w') as f:
    f.write('''# app/email_utils.py — Email Utility Functions
#
# This file is the central place for ALL email-sending logic.
# Currently contains:
#   - send_order_status_email() : fires when admin updates an order status
#
# We keep email logic HERE (not in routes.py) so routes stay clean and readable.
# Any route can just call: send_order_status_email(order)

from flask import render_template, current_app
from flask_mail import Message
from app import mail  # our Flask-Mail instance from app/__init__.py

# ─────────────────────────────────────────────────────────────────────────────
# STATUS CONFIGURATION
# Each status gets: a display icon, a badge colour, and a human message
# ─────────────────────────────────────────────────────────────────────────────
STATUS_CONFIG = {
    "Dispatched": {
        "icon":    "📦",
        "color":   "#1565C0",   # blue
        "message": "Your order has been packed and handed over to our delivery partner. "
                   "It is now on its way to you!"
    },
    "Shipped": {
        "icon":    "🚚",
        "color":   "#6A1B9A",   # purple
        "message": "Your order is in transit. Our delivery partner is moving it "
                   "closer to you. Hang tight!"
    },
    "Out for Delivery": {
        "icon":    "🛵",
        "color":   "#E65100",   # orange
        "message": "Your order is OUT FOR DELIVERY today! "
                   "Please make sure someone is available to receive it."
    },
    "Delivered": {
        "icon":    "🎉",
        "color":   "#2E7D32",   # green
        "message": "Your order has been DELIVERED! We hope you love your purchase. "
                   "Thank you for shopping at M.B Maniyar!"
    },
}


def send_order_status_email(order):
    """
    Sends a branded HTML status-update email to the customer.

    Call this function from any route like:
        send_order_status_email(order_object)

    Parameters:
        order  — an Order model instance (must have .user, .items relationships)

    Returns:
        True  if email sent successfully
        False if something went wrong (we NEVER crash the app over email)
    """

    # ── Guard: only send for the 4 tracked statuses ───────────────────────────
    if order.status not in STATUS_CONFIG:
        return False  # e.g. "Pending" or "Cancelled" — don't email

    # ── Guard: make sure the order has a customer with an email ───────────────
    if not order.user or not order.user.email:
        current_app.logger.warning(
            f"Order #{order.id} has no customer email — skipping status email."
        )
        return False

    # ── Pull config for this status ───────────────────────────────────────────
    config = STATUS_CONFIG[order.status]

    # ── Build the list of items for the email table ───────────────────────────
    # Each item needs: name, size (optional), quantity, price
    items = []
    for cart_item in order.items:          # order.items = relationship to OrderItem
        items.append({
            "name":     cart_item.product.name,
            "size":     getattr(cart_item, "size", None),   # size may not exist
            "quantity": cart_item.quantity,
            "price":    cart_item.price * cart_item.quantity,
        })

    # ── Pickup note — only shown for "Buy Online, Pick Up In Store" orders ────
    pickup_note = None
    if getattr(order, "pickup", False):
        pickup_note = (
            "This is a PICK-UP order. Please collect your order from our store: "
            "Main Road, Opp. Bus Stand, Mantha, Jalna. "
            "Bring this email or your order number as reference."
        )

    # ── Render the HTML template with all the variables ───────────────────────
    # render_template fills in all the {{ }} placeholders in our email HTML
    html_body = render_template(
        "email/order_status.html",
        customer_name  = order.user.username,
        order_id       = order.id,
        status         = order.status,
        status_icon    = config["icon"],
        status_color   = config["color"],
        status_message = config["message"],
        items          = items,
        total_amount   = order.total_amount,
        pickup_note    = pickup_note,
    )

    # ── Build and send the email ───────────────────────────────────────────────
    try:
        subject_map = {
            "Dispatched":       "📦 Your Order Has Been Dispatched!",
            "Shipped":          "🚚 Your Order is On Its Way!",
            "Out for Delivery": "🛵 Your Order is Out for Delivery Today!",
            "Delivered":        "🎉 Your Order Has Been Delivered!",
        }

        msg = Message(
            subject    = f"{subject_map[order.status]} — Order #{order.id}",
            recipients = [order.user.email],
            html       = html_body,
        )
        mail.send(msg)

        current_app.logger.info(
            f"✅ Status email sent → {order.user.email} | "
            f"Order #{order.id} | Status: {order.status}"
        )
        return True

    except Exception as e:
        # IMPORTANT: we catch ALL errors here.
        # A failed email must NEVER prevent the order status from saving.
        current_app.logger.error(
            f"❌ Status email FAILED → Order #{order.id} | Error: {e}"
        )
        return False
''')

print("✅ Created: app/email_utils.py")
print()
print("Now let's test it with a dry-run script before touching any routes.")
print("Run: python3 build_order_email_utils.py")
