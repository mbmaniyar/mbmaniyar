
# Run this ONCE to add demo products to the database
import sys, os
sys.path.insert(0, os.path.expanduser("~/Desktop/mbmaniyar"))

from app import create_app
from app.models import db, Product, ProductVariant, Category, Brand

app = create_app()

with app.app_context():
    ksatish = Brand.query.filter_by(name="k satish").first()
    raymond = Brand.query.filter_by(name="Raymond").first()
    allen   = Brand.query.filter_by(name="Allen Solly").first()
    generic = Brand.query.filter_by(name="Generic").first()

    shirts   = Category.query.filter_by(slug="shirts").first()
    trousers = Category.query.filter_by(slug="trousers").first()
    kurtas   = Category.query.filter_by(slug="kurtas").first()
    tshirts  = Category.query.filter_by(slug="t-shirts").first()
    kids     = Category.query.filter_by(slug="kids-wear").first()

    if Product.query.first():
        print("Products already exist. Skipping.")
        exit()

    products = [
        # k satish shirts
        dict(name="k satish White Classic Shirt",  sku="KS-SH-001", price=899,  mrp=1199, category=shirts,   brand=ksatish,
             sizes=[("S",8),("M",12),("L",10),("XL",5),("XXL",3)]),
        dict(name="k satish Blue Formal Shirt",    sku="KS-SH-002", price=949,  mrp=1299, category=shirts,   brand=ksatish,
             sizes=[("S",4),("M",8), ("L",9), ("XL",6),("XXL",2)]),
        dict(name="k satish Check Casual Shirt",   sku="KS-SH-003", price=799,  mrp=999,  category=shirts,   brand=ksatish,
             sizes=[("S",6),("M",10),("L",7), ("XL",4),("XXL",1)]),
        dict(name="k satish Cotton Kurta",         sku="KS-KU-001", price=1199, mrp=1599, category=kurtas,   brand=ksatish,
             sizes=[("S",5),("M",9), ("L",11),("XL",4),("XXL",2)]),
        # Raymond
        dict(name="Raymond Grey Wool Trouser",     sku="RM-TR-001", price=1899, mrp=2499, category=trousers, brand=raymond,
             sizes=[("28",4),("30",8),("32",10),("34",6),("36",3)]),
        dict(name="Raymond Navy Formal Trouser",   sku="RM-TR-002", price=2099, mrp=2799, category=trousers, brand=raymond,
             sizes=[("28",3),("30",6),("32",9), ("34",7),("36",2)]),
        # Allen Solly
        dict(name="Allen Solly Polo T-Shirt",      sku="AS-TS-001", price=699,  mrp=899,  category=tshirts,  brand=allen,
             sizes=[("S",10),("M",15),("L",12),("XL",8),("XXL",4)]),
        dict(name="Allen Solly Chino Trouser",     sku="AS-TR-001", price=1499, mrp=1899, category=trousers, brand=allen,
             sizes=[("28",5),("30",10),("32",8),("34",5),("36",2)]),
        # Generic kids
        dict(name="Cotton Kids Shirt Set",         sku="GN-KD-001", price=499,  mrp=699,  category=kids,     brand=generic,
             sizes=[("2Y",6),("4Y",8),("6Y",7),("8Y",5),("10Y",3)]),
        dict(name="Kids Festive Kurta",            sku="GN-KD-002", price=649,  mrp=899,  category=kids,     brand=generic,
             sizes=[("2Y",4),("4Y",6),("6Y",8),("8Y",6),("10Y",4)]),
    ]

    for p in products:
        prod = Product(
            name=p["name"], sku=p["sku"],
            price=p["price"], mrp=p.get("mrp"),
            category_id=p["category"].id,
            brand_id=p["brand"].id,
            description=f"Premium quality {p['category'].name.lower()} from {p['brand'].name}. "
                        "Available in multiple sizes at M B MANIYAR, Mantha.",
            is_active=True, is_online=True,
        )
        db.session.add(prod)
        db.session.flush()
        for size, qty in p["sizes"]:
            db.session.add(ProductVariant(product_id=prod.id, size=size, stock_quantity=qty))

    db.session.commit()
    print(f"✅ Seeded {len(products)} demo products with variants!")
