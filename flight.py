import re
import urllib.request
import json
import asyncio
import os
from collections import deque

FLIGHT_DATA_REGEX = re.compile('(?<=<script id="inline-state" type="application/json">).+(?=</script>)')

# a minute
LONG_HISTORY = 60

altitude_history = deque([0], LONG_HISTORY)
speed_history = deque([0], LONG_HISTORY)
heading_history = deque([0], LONG_HISTORY)


def get_flight_data():
    req = urllib.request.urlopen("https://connect.airfrance.com/")
    res = req.read().decode("UTF-8")

    match = FLIGHT_DATA_REGEX.search(res)
    parsed = json.loads(match.group())

    return parsed


def format_flight_header(data):
    fd = data["flightData"]
    flight_number = fd["flightNumber"]
    tail_number = fd["tailNumber"]
    origin = fd["origin"]
    dest = fd["destination"]

    return f"\x1b[1mFlight {flight_number} • {tail_number} • {origin} -> {dest}\x1b[0m"


def format_dt(delta):
    delta = int(delta)

    if -1 < delta < 1:
        return "\x1b[37m– 0\x1b[0m"
    elif delta <= -1:
        return f"\x1b[31m↓ {-delta}\x1b[0m"
    elif 1 <= delta:
        return f"\x1b[32m↑ {delta}\x1b[0m"


def format_flight_data(data):
    # Currently 39006 ft (↑ 2ft/s, ↑ 120ft/m)
    fd = data["flightData"]
    altitude = int(fd["altitude"])
    
    unf = (altitude - altitude_history[-1]) / len(altitude_history)

    altitude_history.append(altitude)
    
    try:
        unf_s = (altitude - altitude_history[10]) / 10
    except IndexError:
        unf_s = unf
    
    unf_m = unf * 60

    fmt_altitude = f"Currently {altitude} ft ({format_dt(unf_s)} ft/s, {format_dt(unf_m)} ft/m)"

    #           592 kts (– 0kts/s, ↑ 200kts/m)
    speed = fd["groundSpeed"]

    unf = (speed - speed_history[-1]) / len(speed_history)

    speed_history.append(speed)

    try:
        unf_s = (speed - speed_history[10]) / 10
    except IndexError:
        unf_s = unf

    unf_m = unf * 60

    fmt_speed = f"          {int(speed)} kts ({format_dt(unf_s)} kts/s, {format_dt(unf_m)} kts/m)"

    #           73° (– 0 deg/s)
    heading = fd["trueHeading"]

    unf = (heading - heading_history[-1]) / len(heading_history)
    
    try:
        unf_s = (heading - heading_history[10]) / 10
    except IndexError:
        unf_s = unf

    unf_m = unf * 60

    heading_history.append(heading)

    fmt_heading = f"          {int(heading)}° ({format_dt(unf_s)} deg/s, {format_dt(unf_m)} deg/m)"

    time_to_dest = fd["timeToDestination"]

    fmt_time = f"Arriving in {int(time_to_dest / 60)} hours, {int(time_to_dest % 60)} minutes"

    return f"{fmt_time}\n\n{fmt_altitude}\n{fmt_speed}\n{fmt_heading}"


async def _task_print_flight_data():
    data = get_flight_data()

    # I don't fucking care
    os.system("clear")

    print(format_flight_header(data))
    print(format_flight_data(data))


async def _task_loop():
    while True:
        await asyncio.sleep(1)
        asyncio.create_task(_task_print_flight_data())


def main():
    asyncio.run(_task_loop())


if __name__ == "__main__":
    main()
