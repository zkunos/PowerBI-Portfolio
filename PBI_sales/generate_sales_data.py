import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from faker import Faker
import uuid

# Initialize Faker
fake = Faker()
Faker.seed(64648)
np.random.seed(64649)


def generate_customer_data(num_customers=100):
    """Generate customer dimension table"""
    segments = ['Consumer', 'Corporate', 'Small Business', 'Enterprise']
    regions = ['North', 'South', 'East', 'West', 'Central']
    countries = ['United States', 'Canada', 'United Kingdom', 'Germany', 'France',
                 'Spain', 'Italy', 'Australia', 'Japan', 'Brazil']

    customers = []
    for i in range(1, num_customers + 1):
        customer = {
            'CustomerID': i,
            'CustomerName': fake.company() if random.random() > 0.5 else fake.name(),
            'Country': random.choice(countries),
            'Region': random.choice(regions),
            'Segment': random.choice(segments),
            'JoinDate': fake.date_between(start_date='-2y', end_date='today'),
            'CreditLimit': random.choice([1000, 2000, 5000, 10000, 20000, 50000]),
            'PreferredPayment': random.choice(['Credit Card', 'Bank Transfer', 'PayPal']),
            'Email': fake.email(),
            'Phone': fake.phone_number()
        }
        customers.append(customer)

    df = pd.DataFrame(customers)
    # Introduce some missing values
    df.loc[np.random.choice(df.index, size=5), 'Email'] = None
    df.loc[np.random.choice(df.index, size=5), 'Phone'] = None
    return df


def generate_product_data(num_products=80):
    """Generate product dimension table"""
    categories = ['Electronics', 'Furniture', 'Office Supplies', 'Software', 'Hardware']
    subcategories = {
        'Electronics': ['Phones', 'Laptops', 'Tablets', 'Monitors', 'Accessories'],
        'Furniture': ['Chairs', 'Desks', 'Tables', 'Storage', 'Furnishings'],
        'Office Supplies': ['Paper', 'Binders', 'Art', 'Supplies', 'Labels'],
        'Software': ['Operating Systems', 'Security', 'Utilities', 'Business', 'Design'],
        'Hardware': ['Processors', 'Memory', 'Storage', 'Peripherals', 'Networking']
    }

    products = []
    for i in range(1, num_products + 1):
        category = random.choice(categories)
        product = {
            'ProductID': i,
            'ProductName': fake.catch_phrase(),
            'Category': category,
            'SubCategory': random.choice(subcategories[category]),
            'UnitPrice': round(random.uniform(10, 2000), 2),
            'Cost': 0,  # Will be calculated later
            'Weight': round(random.uniform(0.1, 50), 2),
            'StockLevel': random.randint(0, 500),
            'ReorderPoint': random.randint(10, 100),
            'MinimumOrderQuantity': random.randint(1, 10)
        }
        # Set cost as percentage of price
        product['Cost'] = round(product['UnitPrice'] * random.uniform(0.4, 0.7), 2)
        products.append(product)

    df = pd.DataFrame(products)
    # Introduce some data issues
    df.loc[np.random.choice(df.index, size=3), 'UnitPrice'] = 0  # Invalid prices
    df.loc[np.random.choice(df.index, size=3), 'Cost'] = None  # Missing costs
    return df


def generate_date_dimension(start_date='2022-01-01', end_date='2024-12-31'):
    """Generate date dimension table"""
    dates = pd.date_range(start=start_date, end=end_date)

    date_dimension = []
    for date in dates:
        record = {
            'DateKey': int(date.strftime('%Y%m%d')),
            'Date': date,
            'Year': date.year,
            'Quarter': (date.month - 1) // 3 + 1,
            'Month': date.month,
            'MonthName': date.strftime('%B'),
            'WeekDay': date.weekday() + 1,
            'WeekDayName': date.strftime('%A'),
            'IsWeekend': 1 if date.weekday() >= 5 else 0,
            'IsHoliday': 0,  # Could be enhanced with actual holiday data
            'FiscalYear': date.year if date.month < 7 else date.year + 1,
            'FiscalQuarter': (date.month - 1) // 3 + 1
        }
        date_dimension.append(record)

    return pd.DataFrame(date_dimension)


def generate_sales_data(customers_df, products_df, date_df, num_transactions=20000):
    """Generate sales fact table with intentional data quality issues"""
    sales = []
    order_id = 1001

    # Get valid IDs
    customer_ids = customers_df['CustomerID'].tolist()
    product_ids = products_df['ProductID'].tolist()
    dates = date_df['Date'].tolist()

    for _ in range(num_transactions):
        # Introduce random data quality issues
        has_error = random.random() < 0.1  # 10% chance of having an error

        order_date = random.choice(dates)
        product_id = random.choice(product_ids)
        product = products_df[products_df['ProductID'] == product_id].iloc[0]

        sale = {
            'SalesOrderID': order_id,
            'OrderDate': order_date if random.random() > 0.02 else None,  # 2% missing dates
            'CustomerID': random.choice(customer_ids) if random.random() > 0.02 else None,  # 2% missing customers
            'ProductID': product_id,
            'Quantity': random.randint(-5, 20) if has_error else random.randint(1, 10),
            'UnitPrice': product['UnitPrice'] if random.random() > 0.02 else None,
            'DiscountAmount': round(random.uniform(0, product['UnitPrice'] * 0.3), 2) if random.random() > 0.8 else 0,
            'ShipDate': order_date + timedelta(days=random.randint(1, 7)),
            'ShipMode': random.choice(['Standard', 'Express', 'Next Day']),
            'SalesPersonID': random.randint(1, 10)
        }

        # Calculate derived fields (with potential errors)
        try:
            if all(x is not None for x in [sale['Quantity'], sale['UnitPrice']]):
                sale['SalesAmount'] = sale['Quantity'] * sale['UnitPrice'] - sale['DiscountAmount']
                sale['Cost'] = product['Cost'] * sale['Quantity'] if random.random() > 0.05 else None
                sale['Profit'] = sale['SalesAmount'] - sale['Cost'] if sale['Cost'] is not None else None
            else:
                sale['SalesAmount'] = None
                sale['Cost'] = None
                sale['Profit'] = None
        except:
            sale['SalesAmount'] = None
            sale['Cost'] = None
            sale['Profit'] = None

        sales.append(sale)
        order_id += 1

    return pd.DataFrame(sales)


def generate_quality_metrics(sales_df):
    """Generate data quality metrics"""
    quality_metrics = []
    dates = pd.date_range(start='2022-01-01', end='2024-12-31', freq='D')

    for date in dates:
        daily_data = sales_df[sales_df['OrderDate'].dt.date == date.date()]

        metric = {
            'Date': date,
            'TotalRecords': len(daily_data),
            'MissingData': len(daily_data[daily_data.isnull().any(axis=1)]),
            'InvalidQuantities': len(daily_data[daily_data['Quantity'] <= 0]),
            'HighDiscounts': len(daily_data[daily_data['DiscountAmount'] > daily_data['SalesAmount'] * 0.5]),
            'DataQualityScore': random.uniform(0.9, 1.0)  # Simplified score calculation
        }
        quality_metrics.append(metric)

    return pd.DataFrame(quality_metrics)


def main():
    """Generate all datasets and save to CSV"""
    print("Generating customer data...")
    customers_df = generate_customer_data()
    customers_df.to_csv('dim_customer.csv', index=False)

    print("Generating product data...")
    products_df = generate_product_data()
    products_df.to_csv('dim_product.csv', index=False)

    print("Generating date dimension...")
    date_df = generate_date_dimension()
    date_df.to_csv('dim_date.csv', index=False)

    print("Generating sales data...")
    sales_df = generate_sales_data(customers_df, products_df, date_df)
    sales_df.to_csv('fact_sales.csv', index=False)

    print("Generating quality metrics...")
    quality_df = generate_quality_metrics(sales_df)
    quality_df.to_csv('data_quality_metrics.csv', index=False)

    # Generate summary of data quality issues
    print("\nData Quality Summary:")
    print(f"Total Sales Records: {len(sales_df)}")
    print(f"Records with Missing Data: {len(sales_df[sales_df.isnull().any(axis=1)])}")
    print(f"Invalid Quantities: {len(sales_df[sales_df['Quantity'] <= 0])}")
    print(f"Missing Costs: {len(sales_df[sales_df['Cost'].isnull()])}")
    print(f"High Discounts: {len(sales_df[sales_df['DiscountAmount'] > sales_df['SalesAmount'] * 0.5])}")


if __name__ == "__main__":
    main()