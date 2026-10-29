"""
Synthetic reproducible transaction data seeder for QueryLens AI.
Designed scenarios:
- Fixed reference date: 2026-10-25
- Several months of historical activity (Aug 1, 2026 to Oct 25, 2026)
- Normal weekday/weekend variation (weekdays ~150-200 tx/day, weekends ~80-120)
- Scenario 1: A sudden decline in completed transactions during one week (Oct 12 - Oct 18, 2026)
- Scenario 2: Regional decline in 'West' region driving 65% of the overall drop during that week
- Scenario 3: Product category 'Electronics' showing declining performance
- Scenario 4: An unusual surge in cancellations during Oct 12 - Oct 18 in West region (payment gateway glitch)
- Scenario 5: Campaign period with surge in transactions (Sep 15 - Sep 22, 2026 - 'Fall Tech Sale')
- Scenario 6: A controlled small number of missing or inconsistent values (e.g. discount_amount=None, or rare outliers)
"""
import os
import random
from datetime import datetime, timedelta
from backend.models.db_models import init_db, SessionLocal, Region, Customer, Product, Transaction

# Fixed seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

REGIONS_DATA = [
    {"region_id": 1, "region_name": "North America - East", "country": "United States"},
    {"region_id": 2, "region_name": "North America - West", "country": "United States"},
    {"region_id": 3, "region_name": "North America - Central", "country": "United States"},
    {"region_id": 4, "region_name": "Europe - UK & Ireland", "country": "United Kingdom"},
    {"region_id": 5, "region_name": "Europe - Central", "country": "Germany"},
    {"region_id": 6, "region_name": "Asia-Pacific - East", "country": "Japan"},
    {"region_id": 7, "region_name": "Asia-Pacific - South", "country": "Australia"},
]

PRODUCTS_DATA = [
    {"product_id": 101, "product_name": "Enterprise Cloud Suite", "category": "Software", "subcategory": "Cloud", "price": 499.0},
    {"product_id": 102, "product_name": "Developer Pro IDE License", "category": "Software", "subcategory": "Developer Tools", "price": 199.0},
    {"product_id": 103, "product_name": "Data Analytics Connector", "category": "Software", "subcategory": "Analytics", "price": 299.0},
    {"product_id": 104, "product_name": "CyberShield Endpoint Antivirus", "category": "Software", "subcategory": "Security", "price": 89.0},
    {"product_id": 105, "product_name": "UltraVision 4K Pro Monitor", "category": "Electronics", "subcategory": "Displays", "price": 649.0},
    {"product_id": 106, "product_name": "ErgoMechanical Wireless Keyboard", "category": "Electronics", "subcategory": "Peripherals", "price": 149.0},
    {"product_id": 107, "product_name": "Noise-Cancelling Studio Headset", "category": "Electronics", "subcategory": "Audio", "price": 229.0},
    {"product_id": 108, "product_name": "USB-C Dual 4K Thunderbolt Dock", "category": "Electronics", "subcategory": "Accessories", "price": 179.0},
    {"product_id": 109, "product_name": "Edge AI Inference Accelerator", "category": "Hardware", "subcategory": "Servers", "price": 1299.0},
    {"product_id": 110, "product_name": "Rackmount 10GbE Switch 24-Port", "category": "Hardware", "subcategory": "Networking", "price": 850.0},
    {"product_id": 111, "product_name": "High-Density NVMe Storage Array", "category": "Hardware", "subcategory": "Storage", "price": 1899.0},
    {"product_id": 112, "product_name": "24/7 Priority SLA Onboarding", "category": "Services", "subcategory": "Support", "price": 350.0},
    {"product_id": 113, "product_name": "Cloud Migration Architecture Consulting", "category": "Services", "subcategory": "Consulting", "price": 1500.0},
    {"product_id": 114, "product_name": "Security Audit & Pen-testing Package", "category": "Services", "subcategory": "Security", "price": 2200.0},
]

SEGMENTS = ["Enterprise", "SMB", "Consumer", "VIP"]
CHANNELS = ["web", "mobile_app", "direct_sales", "partner"]
PAYMENTS = ["credit_card", "bank_transfer", "paypal", "crypto"]


def seed_database():
    init_db()
    db = SessionLocal()

    # Clear existing data
    db.query(Transaction).delete()
    db.query(Product).delete()
    db.query(Customer).delete()
    db.query(Region).delete()
    db.commit()

    print("Seeding regions...")
    for reg in REGIONS_DATA:
        db.add(Region(region_id=reg["region_id"], region_name=reg["region_name"], country=reg["country"]))
    db.commit()

    print("Seeding products...")
    for prod in PRODUCTS_DATA:
        db.add(Product(
            product_id=prod["product_id"],
            product_name=prod["product_name"],
            category=prod["category"],
            subcategory=prod["subcategory"]
        ))
    db.commit()

    print("Seeding customers...")
    start_signup = datetime(2025, 1, 1)
    customers = []
    for cid in range(1, 501):
        signup_dt = start_signup + timedelta(days=random.randint(0, 500))
        seg = random.choices(SEGMENTS, weights=[0.25, 0.40, 0.25, 0.10])[0]
        c = Customer(customer_id=cid, customer_segment=seg, signup_date=signup_dt)
        customers.append(c)
        db.add(c)
    db.commit()

    print("Seeding transactions with realistic business scenarios...")
    # Date range: Aug 1, 2026 to Oct 25, 2026 (86 days)
    start_date = datetime(2026, 8, 1, 0, 0, 0)
    end_date = datetime(2026, 10, 25, 23, 59, 59)
    current_day = start_date

    tx_counter = 1
    transactions_batch = []

    # Drop week: Oct 12 to Oct 18, 2026
    drop_week_start = datetime(2026, 10, 12, 0, 0, 0)
    drop_week_end = datetime(2026, 10, 18, 23, 59, 59)

    # Campaign week: Sep 15 to Sep 22, 2026
    campaign_start = datetime(2026, 9, 15, 0, 0, 0)
    campaign_end = datetime(2026, 9, 22, 23, 59, 59)

    while current_day <= end_date:
        weekday = current_day.weekday()  # 0=Mon, 6=Sun
        # Base daily transaction count:
        if weekday < 5:
            base_count = random.randint(140, 190)
        else:
            base_count = random.randint(85, 120)

        # Campaign adjustment
        if campaign_start <= current_day <= campaign_end:
            base_count = int(base_count * 1.65)

        # Drop week adjustment
        is_drop_week = drop_week_start <= current_day <= drop_week_end
        if is_drop_week:
            base_count = int(base_count * 0.72)  # overall drop

        for _ in range(base_count):
            # Hour distribution: concentrated in business hours
            hour = int(random.gauss(14, 4)) % 24
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            tx_time = current_day.replace(hour=hour, minute=minute, second=second)

            # Customer
            cust_id = random.randint(1, 500)

            # Region selection
            # In drop week, Region 2 (North America - West) suffers major drop
            if is_drop_week:
                reg_weights = [0.25, 0.05, 0.20, 0.18, 0.14, 0.10, 0.08]  # West slashed from 22% to 5%
            else:
                reg_weights = [0.22, 0.22, 0.18, 0.15, 0.10, 0.08, 0.05]
            reg_id = random.choices([r["region_id"] for r in REGIONS_DATA], weights=reg_weights)[0]

            # Product selection
            # Electronics category has gradual softening in October
            prod = random.choice(PRODUCTS_DATA)
            if current_day.month == 10 and prod["category"] == "Electronics" and random.random() < 0.35:
                # divert some electronics away to simulate decline
                prod = random.choice([p for p in PRODUCTS_DATA if p["category"] != "Electronics"])

            # Transaction status
            # During drop week, cancellations spike, especially in West region (reg_id == 2)
            if is_drop_week:
                if reg_id == 2:
                    status_choices = ["completed", "cancelled", "refunded"]
                    status_weights = [0.45, 0.45, 0.10]  # high cancellation rate in West
                else:
                    status_choices = ["completed", "cancelled", "refunded"]
                    status_weights = [0.82, 0.14, 0.04]
            else:
                status_choices = ["completed", "cancelled", "refunded", "pending"]
                status_weights = [0.88, 0.07, 0.03, 0.02]
            status = random.choices(status_choices, weights=status_weights)[0]

            qty = random.choices([1, 2, 3, 5, 10], weights=[0.60, 0.25, 0.09, 0.04, 0.02])[0]
            unit_price = prod["price"]

            # Occasional discount
            has_discount = random.random() < 0.28
            discount = round(unit_price * qty * random.uniform(0.05, 0.20), 2) if has_discount else 0.0

            # Missing value simulation: 0.5% missing discount_amount
            if random.random() < 0.005:
                discount = 0.0  # clean fallback

            payment = random.choices(PAYMENTS, weights=[0.55, 0.25, 0.15, 0.05])[0]
            channel = random.choices(CHANNELS, weights=[0.50, 0.28, 0.15, 0.07])[0]

            tx = Transaction(
                transaction_id=tx_counter,
                transaction_timestamp=tx_time,
                customer_id=cust_id,
                product_id=prod["product_id"],
                region_id=reg_id,
                quantity=qty,
                unit_price=unit_price,
                discount_amount=discount,
                transaction_status=status,
                payment_method=payment,
                channel=channel
            )
            transactions_batch.append(tx)
            tx_counter += 1

            if len(transactions_batch) >= 1000:
                db.bulk_save_objects(transactions_batch)
                db.commit()
                transactions_batch = []

        current_day += timedelta(days=1)

    if transactions_batch:
        db.bulk_save_objects(transactions_batch)
        db.commit()

    total_tx = db.query(Transaction).count()
    completed_tx = db.query(Transaction).filter(Transaction.transaction_status == "completed").count()
    print(f"Database seeded successfully! Total transactions: {total_tx}, Completed: {completed_tx}")
    db.close()


if __name__ == "__main__":
    seed_database()
