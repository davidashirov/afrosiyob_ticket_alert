import argparse
import requests
import json
from datetime import datetime, date, time
import random
import time as time_module
import winsound

# Stations, brands, classes, etc. of interest can be hardcoded:
stations = {"t": "2900000", "s": "2900700", "b": "2900800"}
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
    try:
        data = resp.json()
        trains = data["data"]["directions"]["forward"]["trains"]
    except (KeyError, json.JSONDecodeError) as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text[:300]}")
        return []
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

    # Filtering departure time and class
    filtered_trains = []
    for t in inline_trains:
        if train_fits(t, af, sh, from_time, to_time):
            filtered_trains.append(t)
    return filtered_trains

def alert(filtered_trains):
    winsound.Beep(2500, 1000) # frequency, duration
    for t in filtered_trains:
        print(f"Alert: {t['brand']} {t['t_num']} departing at {t['dep_time']} has {t['seats']} {t['cls']} ({t['code']}) seats available at {t['price']} UZS")
    print("---\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Railway Ticket Alert',
        description='Sends a request to the railway API every n seconds and alerts you if requested tickets are available',
        epilog='')
    parser.add_argument('when', type=date.fromisoformat, help='Date of departure in ISO YYYY-MM-DD format')
    parser.add_argument('departure', type=str, help='Departure station')
    parser.add_argument('arrival', type=str, help='Arrival station')
    parser.add_argument('-a', '--afrosiyob', type=str, required=False, default="ae", help='Include Afrosiyob trains (economic: e, business: b, together: aeb)')
    parser.add_argument('-s', '--sharq', type=str, required=False, default="s", help='Include Sharq/Nasaf trains (economic: e, business: b, together: seb)')
    parser.add_argument('--from-time', type=time.fromisoformat, required=False, default=time(0, 0), help='Start of departure time window in HH:MM format')
    parser.add_argument('--to-time', type=time.fromisoformat, required=False, default=time(23, 59), help='End of departure time window in HH:MM format')
    parser.add_argument('-i', '--interval', type=int, required=False, default=60, help='Interval between requests in seconds')
    args = parser.parse_args()

    dep_key = args.departure.lower()[0] # first letter is enough to identify the station, e.g. "t" for Tashkent
    arr_key = args.arrival.lower()[0]
    if dep_key not in stations:
        parser.error(f"Unknown departure station '{args.departure}'. Available: {', '.join(stations.keys())}")
    if arr_key not in stations:
        parser.error(f"Unknown arrival station '{args.arrival}'. Available: {', '.join(stations.keys())}")

    when = args.when.isoformat()
    departure = stations[dep_key]
    arrival = stations[arr_key]
    af = args.afrosiyob
    sh = args.sharq
    from_time = args.from_time
    to_time = args.to_time
    interval = args.interval

    while True:
        trains = request_trains(departure=departure, arrival=arrival, date=when)
        filtered_trains = filter_trains(trains, af, sh, from_time, to_time)
        if filtered_trains:
            alert(filtered_trains)
        else:
            print(".", end="", flush=True)
        time_module.sleep(interval + random.uniform(-10, 10))