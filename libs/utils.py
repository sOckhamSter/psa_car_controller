import re
from functools import wraps
from threading import Semaphore, Timer
import socket

import requests

from mylogger import logger


def get_temp(latitude: str, longitude: str, api_key: str) -> float:
    try:
        if not (latitude is None or longitude is None or api_key is None):
            weather_rep = requests.get("https://api.openweathermap.org/data/2.5/onecall",
                                       params={"lat": latitude, "lon": longitude,
                                               "exclude": "minutely,hourly,daily,alerts",
                                               "appid": api_key,
                                               "units": "metric"})
            temp = weather_rep.json()["current"]["temp"]
            logger.debug("Temperature :%fc", temp)
            return temp
    except ConnectionError:
        logger.error("Can't connect to openweathermap :", exc_info=True)
    except KeyError:
        logger.error("Unable to get temperature from openweathermap :", exc_info=True)
    return None


def rate_limit(limit, every):
    def limit_decorator(func):
        semaphore = Semaphore(limit)

        @wraps(func)
        def wrapper(*args, **kwargs):
            semaphore.acquire()
            try:
                return func(*args, **kwargs)
            finally:  # don't catch but ensure semaphore release
                timer = Timer(every, semaphore.release)
                timer.setDaemon(True)  # allows the timer to be canceled on exit
                timer.start()

        return wrapper

    return limit_decorator


def is_port_in_use(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((ip, port)) == 0


def parse_hour(hour_str):
    reg = r"PT([0-9]{1,2})H([0-9]{1,2})?|PT([0-9]{1,2})S"
    hour_minute = re.findall(reg, hour_str)[0]
    second = 0
    if hour_minute[0] == '':
        hour = 0
        second = hour_minute[2]
    else:
        hour = int(hour_minute[0])
    if hour_minute[1] == '':
        minute = 0
    else:
        minute = hour_minute[1]
    return hour, minute, second
