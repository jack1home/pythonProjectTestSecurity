import boto3
import os
import webbrowser
from decimal import Decimal

# Initialize DynamoDB and S3 clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.resource('s3')

# Check if DynamoDB table exists, create if not
table_name = 'coins'
if table_name not in [table.name for table in dynamodb.tables.all()]:
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'TypeOfCoin',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'Year',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'TypeOfCoin',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'Year',
                'AttributeType': 'N'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    print("DynamoDB table created successfully.")
else:
    table = dynamodb.Table(table_name)

# Set the S3 bucket name
bucket_name = "wheeler.final.coinpics"

# Check if S3 bucket exists, create if not
if bucket_name not in [bucket.name for bucket in s3.buckets.all()]:
    s3.create_bucket(Bucket=bucket_name)
    print("S3 bucket created successfully.")
else:
    bucket = s3.Bucket(bucket_name)

# Pre-populated dictionary of US coins containing silver and their ounces of silver
us_coins_with_silver = {
    'Morgan Dollar': Decimal('0.77344'),
    'Peace Dollar': Decimal('0.77344'),
    'Kennedy Half Dollar': Decimal('0.36169'),
    'Walking Liberty Half Dollar': Decimal('0.36169'),
    'Franklin Half Dollar': Decimal('0.36169'),
    'Barber Half Dollar': Decimal('0.36169'),
    'Standing Liberty Quarter': Decimal('0.18084'),
    'Washington Quarter': Decimal('0.18084'),
    'Barber Quarter': Decimal('0.18084'),
    'Roosevelt Dime': Decimal('0.07234'),
}


def add_coin(spot_price):
    print("Select a coin to add:")
    for idx, coin in enumerate(us_coins_with_silver.keys(), 1):
        print(f"{idx}. {coin}")

    choice = input("Enter your choice: ")
    try:
        choice = int(choice)
        if 1 <= choice <= len(us_coins_with_silver):
            coin_name = list(us_coins_with_silver.keys())[choice - 1]
            ounces_of_silver = us_coins_with_silver[coin_name]
            year = int(input("Enter year: "))
            num_coins = int(input("Enter the number of coins: "))

            total_value = Decimal(ounces_of_silver) * Decimal(spot_price) * Decimal(num_coins)

            photo_key = input("Enter S3 photo key (leave empty if none): ")

            # Check if the photo key is provided and upload photo to S3
            if photo_key:
                try:
                    s3.meta.client.upload_file(photo_key, bucket_name, photo_key)
                except Exception as e:
                    print("Error uploading photo to S3:", e)
                    return

            # Add the coin to DynamoDB
            try:
                # Check if the coin already exists in the database
                response = table.get_item(
                    Key={
                        'TypeOfCoin': coin_name,
                        'Year': year
                    }
                )
                item = response.get('Item')

                if item:
                    # Update the existing item with the new number of coins
                    new_num_coins = item.get('NumCoins', 0) + num_coins
                    table.update_item(
                        Key={
                            'TypeOfCoin': coin_name,
                            'Year': year
                        },
                        UpdateExpression='SET NumCoins = :val',
                        ExpressionAttributeValues={
                            ':val': new_num_coins
                        }
                    )
                    print("Coin quantity updated successfully!")
                else:
                    # Add a new item if it doesn't exist
                    table.put_item(
                        Item={
                            'TypeOfCoin': coin_name,
                            'Year': year,
                            'OuncesOfSilver': ounces_of_silver,
                            'ValuePerCoin': total_value / num_coins,
                            'NumCoins': num_coins,
                            'Photo': photo_key
                        }
                    )
                    print("Coin added successfully!")
            except Exception as e:
                print("Error adding coin to DynamoDB:", e)
        else:
            print("Invalid choice.")
    except ValueError:
        print("Invalid input. Please enter a number.")


def delete_coin():
    print("Select a coin to delete:")
    for idx, coin in enumerate(us_coins_with_silver.keys(), 1):
        print(f"{idx}. {coin}")

    # Vulnerability introduced here: direct user input without validation
    choice = input("Enter your choice: ")
    try:
        choice = int(choice)  # Vulnerability: no validation on user input
        if 1 <= choice <= len(us_coins_with_silver):
            coin_name = list(us_coins_with_silver.keys())[choice - 1]
            year = int(input("Enter year: "))

            # Delete the coin from DynamoDB
            try:
                table.delete_item(
                    Key={
                        'TypeOfCoin': coin_name,
                        'Year': year
                    }
                )
                print("Coin deleted successfully!")
            except Exception as e:
                print("Error deleting coin from DynamoDB:", e)
        else:
            print("Invalid choice.")
    except ValueError:
        print("Invalid input. Please enter a number.")



def display_collection():
    total_portfolio_value = 0
    try:
        response = table.scan()
        coins = response['Items']
        if not coins:
            print("No coins found.")
            return
        print("Type of Coin | Year | Quantity | Value (USD)")
        print("----------------------------------------------")
        for coin in coins:
            value = coin['ValuePerCoin'] * coin['NumCoins']
            total_portfolio_value += value
            print(f"{coin['TypeOfCoin']} | {coin['Year']} | {coin['NumCoins']} | {value:.2f}")
        print("----------------------------------------------")
        print(f"Total Portfolio Value: {total_portfolio_value:.2f} USD")
    except Exception as e:
        print("Error displaying collection:", e)


def clear_tables():
    try:
        response = table.scan()
        coins = response['Items']
        for coin in coins:
            table.delete_item(
                Key={
                    'TypeOfCoin': coin['TypeOfCoin'],
                    'Year': coin['Year']
                }
            )
        print("All tables cleared successfully!")
    except Exception as e:
        print("Error clearing tables:", e)


def visit_apmex():
    # Implement functionality to visit Apmex
    print("Visiting Apmex...")
    webbrowser.open("https://www.apmex.com")


def get_spot_price():
    try:
        spot_price = float(input("Enter Silver Spot Price for today: "))
        return spot_price
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return get_spot_price()


def main():
    # Get the spot price before displaying the menu
    spot_price = get_spot_price()

    # Implement menu-driven interface
    while True:
        print("\nMenu:")
        print("1. Add a Coin")
        print("2. Delete a Coin")
        print("3. Display Entire Collection")
        print("4. Clear all Tables")
        print("5. Visit Apmex")
        print("6. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_coin(spot_price)
        elif choice == "2":
            delete_coin()
        elif choice == "3":
            display_collection()
        elif choice == "4":
            clear_tables()
        elif choice == "5":
            visit_apmex()
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
