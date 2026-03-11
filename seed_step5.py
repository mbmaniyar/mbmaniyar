
import sys
sys.path.insert(0, ".")
from app import create_app
from app.models import db, Notice, TrainingResource, User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(role="admin").first()
    
    if Notice.query.count() == 0:
        notices = [
            Notice(title="Welcome to the New Staff Portal!",
                   body="We have launched our new digital staff portal. You can view your shifts, salary, and tasks all in one place. Please explore and let the manager know if you have any questions.",
                   priority="important", posted_by=admin.id if admin else None),
            Notice(title="Summer Sale — 20% off all Kurtas",
                   body="Starting this weekend, all Kurta items will have a 20% discount. Please ensure displays are updated and price tags are correct before Saturday morning.",
                   priority="urgent", posted_by=admin.id if admin else None),
            Notice(title="New Stock Arriving Thursday",
                   body="Raymond and k satish new collection arriving Thursday. All floor staff please clear the designated display area by Wednesday evening.",
                   priority="normal", posted_by=admin.id if admin else None),
        ]
        for n in notices:
            db.session.add(n)

    if TrainingResource.query.count() == 0:
        resources = [
            TrainingResource(
                title="How to Process a POS Sale",
                description="Step-by-step guide for billing customers at the counter.",
                resource_type="guide", category="POS & Billing",
                content="""## Processing a POS Sale

### Step 1: Open the POS
Go to Admin → POS Billing from the sidebar.

### Step 2: Find the Product
- Type the product name or SKU in the search bar
- OR tap the product tile on the left panel
- Select the correct SIZE from the popup

### Step 3: Review the Cart
- Check item name, size, quantity, and price
- Use +/- buttons to adjust quantity
- Apply discount if applicable (flat ₹ or percentage %)

### Step 4: Enter Your Employee Code
Type your employee code (e.g. MBM-001) in the field — this ensures you get credit for the sale commission!

### Step 5: Select Payment Method
Choose Cash, UPI, or Card.

### Step 6: Click CHARGE
Confirm the total and click the orange CHARGE button. The receipt will appear automatically.

### Step 7: Print Receipt
Click "Print Receipt" and hand it to the customer."""
            ),
            TrainingResource(
                title="How to Fold & Stack Shirts",
                description="Proper folding technique to keep the floor display neat.",
                resource_type="guide", category="Store Operations",
                content="""## Shirt Folding Guide

### Formal Shirts
1. Lay flat, buttons facing down
2. Fold one sleeve diagonally across the back
3. Fold the other sleeve the same way
4. Fold the bottom third up
5. Fold again so the collar is on top

### T-Shirts
1. Lay flat, design facing down
2. Fold left side (with sleeve) to the center
3. Fold right side the same way
4. Fold bottom half up to the collar

### Display Tips
- All sizes in a stack: XS at top, XXL at bottom
- Face the collar outward on shelves
- Keep folds tight and even
- Check and refold every 2 hours during busy periods"""
            ),
            TrainingResource(
                title="How to Handle Customer Returns",
                description="Policy and procedure for processing returns and exchanges.",
                resource_type="policy", category="Customer Service",
                content="""## Return & Exchange Policy

### What We Accept
- Items returned within **7 days** of purchase
- Original receipt must be present
- Item must be **unworn, unwashed, with all tags attached**

### What We DO NOT Accept
- Items without receipt
- Items that have been worn/washed
- Sale items (20%+ discount) — exchange only

### Return Process
1. Verify receipt and check item condition
2. Call the manager if unsure — **do not process without approval**
3. For cash returns: manager must authorize and give cash from the till
4. For exchange: find the replacement item and process as new sale at ₹0

### Important
Always be polite and empathetic. If a customer is upset, stay calm and say: *"Let me check with my manager to make sure we give you the best solution."*"""
            ),
            TrainingResource(
                title="New Brand: Raymond Collection Guide",
                description="Overview of the new Raymond premium collection we now stock.",
                resource_type="guide", category="Product Knowledge",
                content="""## Raymond Collection — Staff Guide

### About the Brand
Raymond is India's largest integrated manufacturer of worsted suiting fabric. Premium positioning — target customers are professionals aged 30-55.

### Key Selling Points
- "The Complete Man" brand identity
- Superior wool-blend fabric
- Machine washable options available
- 2-year fabric quality guarantee

### Products We Stock
| Item | Price Range | Key Feature |
|------|------------|-------------|
| Wool Trousers | ₹1,899–₹2,499 | Wrinkle-resistant |
| Formal Shirts | ₹1,299–₹1,799 | Stain-guard treated |
| Suit Fabric | ₹2,500/metre | Custom tailoring |

### How to Pitch
"Raymond fabric is crafted for the modern professional. It looks sharp all day without ironing, and the quality will last you years — it's an investment piece."
"""
            ),
        ]
        for r in resources:
            db.session.add(r)
    
    db.session.commit()
    print("✅ Sample notices and training resources seeded!")
