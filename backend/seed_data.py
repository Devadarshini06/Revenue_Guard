import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Base
from backend.models import (
    Category, Region, Product, Customer, Order, OrderItem, Discount, Refund, Transaction, DataUpload
)

# Realistic product catalog
CATEGORIES_DATA = [
    {
        "name": "Cloud & Infrastructure",
        "code": "CAT-CLOUD",
        "description": "Enterprise cloud computing, storage clusters, and managed kubernetes services.",
        "products": [
            {"sku": "PRD-CLD-01", "name": "Dedicated Kubernetes Cluster", "unit_price": 1499.0, "unit_cost": 720.0, "target_margin": 52.0},
            {"sku": "PRD-CLD-02", "name": "High-Throughput Object Storage (10TB)", "unit_price": 450.0, "unit_cost": 180.0, "target_margin": 60.0},
            {"sku": "PRD-CLD-03", "name": "Global Anycast CDN Appliance", "unit_price": 850.0, "unit_cost": 340.0, "target_margin": 60.0},
            {"sku": "PRD-CLD-04", "name": "Enterprise Virtual Private Cloud", "unit_price": 2200.0, "unit_cost": 990.0, "target_margin": 55.0},
        ]
    },
    {
        "name": "Cybersecurity & Compliance",
        "code": "CAT-SEC",
        "description": "Zero-trust network access, WAF firewalls, SIEM logging, and SOC2 compliance automation.",
        "products": [
            {"sku": "PRD-SEC-01", "name": "Zero-Trust Perimeter Shield", "unit_price": 1850.0, "unit_cost": 650.0, "target_margin": 65.0},
            {"sku": "PRD-SEC-02", "name": "Automated Penetration Testing Suite", "unit_price": 950.0, "unit_cost": 310.0, "target_margin": 67.0},
            {"sku": "PRD-SEC-03", "name": "Next-Gen AI Web Application Firewall", "unit_price": 1200.0, "unit_cost": 420.0, "target_margin": 65.0},
            {"sku": "PRD-SEC-04", "name": "Endpoint Threat Detection (500 seats)", "unit_price": 3500.0, "unit_cost": 1400.0, "target_margin": 60.0},
        ]
    },
    {
        "name": "Data Analytics & AI",
        "code": "CAT-DATA",
        "description": "Real-time streaming ingestion, vector databases, and fine-tuned predictive modeling.",
        "products": [
            {"sku": "PRD-DAT-01", "name": "Real-Time Event Ingestion Pipeline", "unit_price": 1250.0, "unit_cost": 500.0, "target_margin": 60.0},
            {"sku": "PRD-DAT-02", "name": "Serverless Vector Indexing Node", "unit_price": 680.0, "unit_cost": 290.0, "target_margin": 57.0},
            {"sku": "PRD-DAT-03", "name": "Predictive Churn Engine Subscription", "unit_price": 2100.0, "unit_cost": 840.0, "target_margin": 60.0},
            {"sku": "PRD-DAT-04", "name": "Business Intelligence Workspace Tier", "unit_price": 490.0, "unit_cost": 150.0, "target_margin": 69.0},
        ]
    },
    {
        "name": "Hardware Appliances",
        "code": "CAT-HW",
        "description": "Rackmount edge gateways, hardware security modules, and biometric access controllers.",
        "products": [
            {"sku": "PRD-HW-01", "name": "Edge Telemetry Gateway 10Gbps", "unit_price": 3200.0, "unit_cost": 2400.0, "target_margin": 25.0},
            {"sku": "PRD-HW-02", "name": "FIPS 140-3 Hardware Security Module", "unit_price": 5400.0, "unit_cost": 4100.0, "target_margin": 24.0},
            {"sku": "PRD-HW-03", "name": "Biometric Turnstile Controller Rack", "unit_price": 2800.0, "unit_cost": 2150.0, "target_margin": 23.0},
            {"sku": "PRD-HW-04", "name": "Industrial IoT Sensor Hub", "unit_price": 1100.0, "unit_cost": 850.0, "target_margin": 22.0},
        ]
    },
    {
        "name": "Professional Services & Support",
        "code": "CAT-SRV",
        "description": "24/7 dedicated enterprise technical account management, architectural reviews, and migration.",
        "products": [
            {"sku": "PRD-SRV-01", "name": "Enterprise TAM & 24/7 SLA Pack", "unit_price": 2500.0, "unit_cost": 1200.0, "target_margin": 52.0},
            {"sku": "PRD-SRV-02", "name": "Cloud Migration Sprint (40 Hours)", "unit_price": 6000.0, "unit_cost": 3600.0, "target_margin": 40.0},
            {"sku": "PRD-SRV-03", "name": "Architecture Health Assessment", "unit_price": 3800.0, "unit_cost": 1900.0, "target_margin": 50.0},
        ]
    }
]

REGIONS_DATA = [
    {"name": "North America - East", "code": "NA-EAST", "country": "United States", "state": "New York", "city": "New York"},
    {"name": "North America - West", "code": "NA-WEST", "country": "United States", "state": "California", "city": "San Francisco"},
    {"name": "North America - Central", "code": "NA-CENTRAL", "country": "United States", "state": "Illinois", "city": "Chicago"},
    {"name": "Europe - UK & Ireland", "code": "EU-WEST", "country": "United Kingdom", "state": "England", "city": "London"},
    {"name": "Europe - Central", "code": "EU-CENTRAL", "country": "Germany", "state": "Hesse", "city": "Frankfurt"},
    {"name": "Asia Pacific - Japan", "code": "APAC-JP", "country": "Japan", "state": "Kanto", "city": "Tokyo"},
    {"name": "Asia Pacific - ANZ", "code": "APAC-ANZ", "country": "Australia", "state": "New South Wales", "city": "Sydney"},
    {"name": "Latin America", "code": "LATAM", "country": "Brazil", "state": "São Paulo", "city": "São Paulo"}
]

SEGMENTS = ["Enterprise", "Mid-Market", "SMB", "Direct Consumer"]
PAYMENT_METHODS = ["Wire Transfer", "Credit Card", "ACH", "PayPal"]
REFUND_REASONS = [
    "Defective Item",
    "Customer Cancellation",
    "Pricing Discrepancy",
    "Late Delivery",
    "Incorrect Product"
]
DISCOUNT_CODES = [
    {"code": "ENTERPRISE20", "type": "Volume", "pct": 20.0, "reason": "Annual Enterprise Volume Commit"},
    {"code": "MIDMARKET15", "type": "Volume", "pct": 15.0, "reason": "Mid-Market Tier Discount"},
    {"code": "GROWTH10", "type": "Promotional", "pct": 10.0, "reason": "Quarterly Growth Incentive"},
    {"code": "SPRINGBOOST", "type": "Promotional", "pct": 12.0, "reason": "Spring Promotional Campaign"},
    {"code": "TECHPARTNER", "type": "Partner", "pct": 18.0, "reason": "Strategic Cloud Partner Rebate"},
    {"code": "RETENTION25", "type": "Retention", "pct": 25.0, "reason": "Contract Renewal Concession"}
]

CUSTOMER_FIRST_NAMES = ["Liam", "Olivia", "Noah", "Emma", "Oliver", "Charlotte", "James", "Amelia", "Sophia", "Lucas", "Ethan", "Isabella", "Mason", "Mia", "Alexander", "Harper", "Benjamin", "Evelyn", "Henry", "Ava"]
CUSTOMER_LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
COMPANY_SUFFIXES = ["Corp", "Technologies", "Logistics", "Ventures", "Systems", "Healthcare", "Financial", "Solutions", "Media", "Digital", "Industries", "Group"]

def seed_database(target_orders: int = 5200, force_recreate: bool = False):
    """Generates 5,000+ realistic transaction records with full relational integrity."""
    print(f"[*] Initializing database schema (target: {target_orders} orders)...")
    if force_recreate:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # Check if already seeded
        existing_orders_count = db.query(Order).count()
        if existing_orders_count >= 1000 and not force_recreate:
            print(f"[!] Database already seeded with {existing_orders_count} orders. Skipping seed.")
            return

        print("[*] Creating categories and products...")
        all_products = []
        for cat_info in CATEGORIES_DATA:
            cat = Category(
                name=cat_info["name"],
                code=cat_info["code"],
                description=cat_info["description"]
            )
            db.add(cat)
            db.flush()

            for p_info in cat_info["products"]:
                prod = Product(
                    category_id=cat.id,
                    sku=p_info["sku"],
                    name=p_info["name"],
                    unit_price=p_info["unit_price"],
                    unit_cost=p_info["unit_cost"],
                    target_margin=p_info["target_margin"],
                    is_active=True
                )
                db.add(prod)
                all_products.append(prod)

        print("[*] Creating regions...")
        all_regions = []
        for reg_info in REGIONS_DATA:
            reg = Region(
                name=reg_info["name"],
                code=reg_info["code"],
                country=reg_info["country"],
                state=reg_info["state"],
                city=reg_info["city"]
            )
            db.add(reg)
            all_regions.append(reg)
        db.flush()

        print("[*] Generating 350 enterprise and business customers...")
        all_customers = []
        for i in range(1, 351):
            fname = random.choice(CUSTOMER_FIRST_NAMES)
            lname = random.choice(CUSTOMER_LAST_NAMES)
            suffix = random.choice(COMPANY_SUFFIXES)
            company_name = f"{lname} {suffix}"
            seg = random.choices(SEGMENTS, weights=[25, 35, 30, 10])[0]
            region = random.choice(all_regions)
            
            cust = Customer(
                customer_code=f"CUST-{i:05d}",
                name=company_name,
                email=f"{fname.lower()}.{lname.lower()}@{lname.lower()}{suffix.lower()}.com",
                segment=seg,
                region_id=region.id,
                created_at=datetime.utcnow() - timedelta(days=random.randint(200, 750))
            )
            db.add(cust)
            all_customers.append(cust)
        db.flush()

        print(f"[*] Generating {target_orders} orders over the past 18 months...")
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=540) # ~18 months
        total_days = (end_date - start_date).days

        # Batch collection lists
        orders_batch = []
        order_items_batch = []
        discounts_batch = []
        refunds_batch = []
        transactions_batch = []

        for order_idx in range(1, target_orders + 1):
            # Non-linear date distribution showing realistic monthly growth trend
            day_offset = int((random.random() ** 0.85) * total_days)
            order_dt = start_date + timedelta(days=day_offset, hours=random.randint(8, 20), minutes=random.randint(0, 59))
            
            customer = random.choice(all_customers)
            region = customer.region
            payment = random.choices(PAYMENT_METHODS, weights=[35, 45, 15, 5])[0]

            order_num = f"ORD-{order_dt.year}-{order_idx:06d}"

            # Items for this order: 1 to 4 distinct products
            item_count = random.choices([1, 2, 3, 4], weights=[50, 30, 15, 5])[0]
            selected_products = random.sample(all_products, k=item_count)

            order_gross = 0.0
            order_discount = 0.0
            order_refund = 0.0

            # Decide if order has discount (38% probability)
            has_discount = random.random() < 0.38
            disc_rule = random.choice(DISCOUNT_CODES) if has_discount else None

            # Temporarily prepare order record
            order_record = Order(
                order_number=order_num,
                customer_id=customer.id,
                region_id=region.id,
                order_date=order_dt,
                status="Completed",
                payment_method=payment,
                shipping_cost=round(random.uniform(25.0, 150.0), 2) if random.random() < 0.4 else 0.0,
                total_gross_amount=0.0,
                total_discount_amount=0.0,
                total_refund_amount=0.0,
                total_net_amount=0.0
            )
            db.add(order_record)
            db.flush() # obtain order_record.id

            # Decide refund probability: ~7% of orders have a refund
            is_refunded = random.random() < 0.075

            for p in selected_products:
                qty = random.choices([1, 2, 3, 5, 10], weights=[55, 25, 12, 5, 3])[0]
                item_gross = round(qty * p.unit_price, 2)
                item_cogs = round(qty * p.unit_cost, 2)
                
                item_discount = 0.0
                if has_discount and disc_rule:
                    item_discount = round(item_gross * (disc_rule["pct"] / 100.0), 2)

                item_net = round(item_gross - item_discount, 2)
                item_profit = round(item_net - item_cogs, 2)

                order_gross += item_gross
                order_discount += item_discount

                order_item = OrderItem(
                    order_id=order_record.id,
                    product_id=p.id,
                    quantity=qty,
                    unit_price=p.unit_price,
                    unit_cost=p.unit_cost,
                    discount_amount=item_discount,
                    gross_revenue=item_gross,
                    net_revenue=item_net,
                    cogs=item_cogs,
                    profit=item_profit
                )
                db.add(order_item)
                db.flush()

                if has_discount and disc_rule:
                    disc = Discount(
                        order_id=order_record.id,
                        order_item_id=order_item.id,
                        discount_code=disc_rule["code"],
                        discount_type=disc_rule["type"],
                        discount_percentage=disc_rule["pct"],
                        discount_amount=item_discount,
                        reason=disc_rule["reason"]
                    )
                    db.add(disc)

                # If refunded, attach to this item
                if is_refunded and order_refund == 0.0:
                    refund_ratio = random.choice([1.0, 0.5]) # full or partial item refund
                    refund_amt = round(item_net * refund_ratio, 2)
                    order_refund += refund_amt
                    ref_dt = order_dt + timedelta(days=random.randint(2, 28))
                    ref_reason = random.choices(REFUND_REASONS, weights=[35, 25, 18, 12, 10])[0]

                    rf = Refund(
                        order_id=order_record.id,
                        order_item_id=order_item.id,
                        refund_date=ref_dt,
                        refund_amount=refund_amt,
                        refund_reason=ref_reason,
                        status="Approved"
                    )
                    db.add(rf)

            # Update order aggregates and status
            order_record.total_gross_amount = round(order_gross, 2)
            order_record.total_discount_amount = round(order_discount, 2)
            order_record.total_refund_amount = round(order_refund, 2)
            order_record.total_net_amount = round(order_gross - order_discount - order_refund, 2)

            if is_refunded:
                if order_refund >= (order_gross - order_discount):
                    order_record.status = "Refunded"
                else:
                    order_record.status = "Partially_Refunded"

            # Create financial transaction ledger records
            t1 = Transaction(
                transaction_reference=f"TXN-CHG-{order_record.id:07d}",
                order_id=order_record.id,
                transaction_type="Charge",
                amount=round(order_gross - order_discount, 2),
                payment_method=payment,
                status="Settled",
                created_at=order_dt
            )
            db.add(t1)

            if is_refunded:
                t2 = Transaction(
                    transaction_reference=f"TXN-REF-{order_record.id:07d}",
                    order_id=order_record.id,
                    transaction_type="Refund",
                    amount=-round(order_refund, 2),
                    payment_method=payment,
                    status="Settled",
                    created_at=order_dt + timedelta(days=random.randint(2, 28))
                )
                db.add(t2)

            # Periodic batch commit for memory efficiency
            if order_idx % 500 == 0:
                db.commit()
                print(f"  -> Generated {order_idx} / {target_orders} orders...")

        # Record sample data upload entry
        upload_entry = DataUpload(
            filename="enterprise_synthetic_dataset_v1.0.csv",
            rows_count=target_orders,
            valid_rows=target_orders,
            invalid_rows=0,
            duplicate_rows=0,
            status="Completed",
            summary_notes="Synthetic baseline dataset with 5,200 orders across 5 categories and 8 global regions."
        )
        db.add(upload_entry)
        db.commit()

        print("[+] Seed completed successfully! Database is primed with realistic enterprise transactions.")
    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database(target_orders=5200, force_recreate=True)

