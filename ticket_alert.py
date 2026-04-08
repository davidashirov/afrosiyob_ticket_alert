import argparse
import requests
import json
from datetime import datetime, date, time
import random
import time as time_module

departure = '2900000'  # Tashkent
arrival = '2900700'    # Samarkand
when = "2026-05-20"
af = 'ae'
sh = 'sb'
from_time = time.fromisoformat("00:00")
to_time = time.fromisoformat("23:59")
interval = 60

# Stations, brands, classes, etc. of interest can be hardcoded:
stations = {"tashkent": "2900000", "samarkand": "2900700", "bukhara": "2900800"}
brands = ["Afrosiyob", "Sharq", "Nasaf"] # There are more, I typically care only about Afrosiyob
classes = {
    "Afrosiyob": {"2Е": "e", "1С": "b"},
    "Sharq": {"2В": "e", "1С": "b", "1В": "v"},
    "Nasaf": {"2В": "e"},
} # class codes differ by brand, so we need to specify them separately. 


def request_trains(date, departure="2900000", arrival="2900700"):
    session = requests.Session()
    session.get("https://eticket.railway.uz/api/v1/csrf-token")
    csrf_token = session.cookies.get("XSRF-TOKEN")
    resp = session.post(
        "https://eticket.railway.uz/api/v3/handbook/trains/list",
        headers={
            "X-XSRF-TOKEN": csrf_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Language": "ru",
            "Referer": "https://eticket.railway.uz/ru/home",
            "Origin": "https://eticket.railway.uz",
            "device-type": "BROWSER",
        },
        json={
            "directions": {
                "forward": {
                    "date": date,
                    "depStationCode": departure,
                    "arvStationCode": arrival,
                }
            }
        },
    )
    trains = resp.json()["data"]["directions"]["forward"]["trains"]
    return trains

def train_fits(t: dict, af: str, sh: str, from_time: time, to_time: time) -> bool:
    if t["brand"] == 'Afrosiyob' and t["cls"] in af and from_time <= t["dep_time"] <= to_time:
        return True
    if (t["brand"] == 'Sharq' or t["brand"] == 'Nasaf') and t["cls"] in sh and from_time <= t["dep_time"] <= to_time:
        return True
    return False

def filter_trains(trains, af, sh, from_time, to_time):
    
    ## Flatten trains data structure
    inline_trains = []
    for t in trains:
        if len(t["cars"]) > 0:
            for car in t["cars"]:
                for tariff in car["tariffs"]:
                    brand = t["brand"]
                    t_num = t["number"]
                    seats = tariff["freeSeats"]
                    cls = classes.get(brand, {}).get(tariff["classServiceType"], "?") # get class code (e,b,v), default to "?" if not found
                    code = tariff["classServiceType"]
                    price = tariff["tariff"]
                    dep_time = datetime.strptime(t['departureDate'], "%d.%m.%Y %H:%M").time()
                    
                    inline_trains.append({"brand": brand, "t_num": t_num, "dep_time": dep_time, "seats": seats, "cls": cls, "code": code, "price": price})
                    #print(f"{brand} {t_num} departing at {dep_time} has {seats} {cls} ({code}) seats available at {price} UZS")

    # Filtering departure time and class
    filtered_trains = []
    for t in inline_trains:
        if train_fits(t, af, sh, from_time, to_time):
            filtered_trains.append(t)
            #print(f"{t['brand']} {t['t_num']} departing at {t['dep_time']} has {t['seats']} {t['cls']} ({t['code']}) seats available at {t['price']} UZS")
    return filtered_trains

def alert(filtered_trains):
    if filtered_trains:
        play_sound()  # Implement this function to play a sound alert
        for t in filtered_trains:
            print(f"Alert: {t['brand']} {t['t_num']} departing at {t['dep_time']} has {t['seats']} {t['cls']} ({t['code']}) seats available at {t['price']} UZS")
            print("---\n")

def play_sound():
    import winsound
    # Play a system sound
    for _ in range(3):
        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)


while True:
    trains = request_trains(departure=departure, arrival=arrival, date=when)
    filtered_trains = filter_trains(trains, af, sh, from_time, to_time)
    alert(filtered_trains)
    time_module.sleep(interval + random.uniform(-5, 5))  # add some jitter to avoid looking like a bot