import asyncio
import os
from twikit import Client
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Get credentials from environment variables
USERNAME = os.getenv('TWITTER_USERNAME')
EMAIL = os.getenv('TWITTER_EMAIL')
PASSWORD = os.getenv('TWITTER_PASSWORD')


# Initialize client
client = Client('en-US')

async def main():
    await client.login(
        auth_info_1=USERNAME,
        auth_info_2=EMAIL,
        password=PASSWORD,
        cookies_file='cookies.json'
    )

    client.save_cookies('cookies.json')

    print("Login successful")
    print("Cookies saved to cookies.json")

asyncio.run(main())
