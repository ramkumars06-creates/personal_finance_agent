"""
Sample Data Generator: Generates ~12 weeks of realistic synthetic INR transactions for testing and presentation demo.
"""
import random
import pandas as pd
from datetime import datetime, timedelta


def generate_synthetic_transactions(output_filepath: str = "data/sample_transactions.csv") -> pd.DataFrame:
    """
    Generate synthetic transactions with noisy merchant names, duplicates, nulls, and injected anomalies.
    """
    random.seed(42)
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=12)

    categories_merchants = {
        "food": ["SWIGGY*ORDER 8843", "swiggy order", "ZOMATO RESTAURANT", "Starbucks Cafe", "Chai Point"],
        "groceries": ["BLINKIT*GROCERY", "ZEPTO QUICK", "BigBasket", "DMART RETAIL"],
        "transport": ["UBER INDIA RIDE", "OLA CABS", "NAMMA METRO BMRCL", "HPCL PETROL PUMP"],
        "bills": ["BESCOM ELECTRICITY", "AIRTEL BROADBAND", "JIO RECHARGE", "BANGALORE WATER"],
        "shopping": ["AMZN Mktp IN", "FLIPKART ONLINE", "MYNTRA FASHION", "ZARA RETAIL"],
        "entertainment": ["NETFLIX MONTHLY", "BOOKMYSHOW MOVIE", "HOTSTAR SUBSCRIPTION"],
        "health": ["APOLLO PHARMACY", "PHARMEASY ORDER", "MANIPAL HOSPITAL"]
    }

    records = []

    # Generate 12 weeks of background realistic transactions
    current_date = start_date
    while current_date < end_date - timedelta(days=7):
        num_txns = random.randint(2, 6)
        for _ in range(num_txns):
            cat = random.choice(list(categories_merchants.keys()))
            merch = random.choice(categories_merchants[cat])
            
            if cat == "food":
                amt = round(random.uniform(150, 800), 2)
            elif cat == "groceries":
                amt = round(random.uniform(400, 2500), 2)
            elif cat == "transport":
                amt = round(random.uniform(50, 600), 2)
            elif cat == "bills":
                amt = round(random.uniform(500, 3000), 2)
            elif cat == "shopping":
                amt = round(random.uniform(500, 3500), 2)
            else:
                amt = round(random.uniform(200, 1500), 2)

            records.append({
                "Date": current_date.strftime("%Y-%m-%d"),
                "Description": merch,
                "Amount": amt,
                "Type": "debit"
            })
        current_date += timedelta(days=random.randint(1, 3))

    # Add Presentation Demo Week Transactions (Last 7 Days)
    demo_week_start = end_date - timedelta(days=7)
    demo_txns = [
        (demo_week_start + timedelta(days=1), "SWIGGY*ORDER 8843", 450.0),
        (demo_week_start + timedelta(days=2), "AMZN Mktp IN", 1200.0),
        (demo_week_start + timedelta(days=3), "NAMMA METRO BMRCL", 80.0),
        (demo_week_start + timedelta(days=4), "UNKNOWN TECH CORP CHARGE", 5000.0),  # Injected Anomaly
        (demo_week_start + timedelta(days=5), "BESCOM ELECTRICITY", 2000.0)
    ]

    for d_date, desc, amt in demo_txns:
        records.append({
            "Date": d_date.strftime("%Y-%m-%d"),
            "Description": desc,
            "Amount": amt,
            "Type": "debit"
        })

    # Inject noisy edge cases: duplicate row & null description
    records.append(records[5].copy())  # Duplicate
    records.append({"Date": end_date.strftime("%Y-%m-%d"), "Description": None, "Amount": 100.0, "Type": "debit"})

    df = pd.DataFrame(records)
    df.to_csv(output_filepath, index=False)
    print(f"Generated {len(df)} synthetic transactions and saved to '{output_filepath}'.")
    return df


if __name__ == "__main__":
    generate_synthetic_transactions()
