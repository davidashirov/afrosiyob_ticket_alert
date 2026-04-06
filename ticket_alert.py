import requests

session = requests.Session()

# GET the homepage — server sets the XSRF-TOKEN cookie
session.get("https://eticket.railway.uz/ru/home")

# Extract the token from the cookie jar
csrf_token = session.cookies.get("XSRF-TOKEN")
print(f"CSRF token: {csrf_token}")