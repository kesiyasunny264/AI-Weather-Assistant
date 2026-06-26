# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo
import requests
import os

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

#import os
#import google.auth

#_, project_id = google.auth.default()
#os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
#os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
#os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

def get_weather_advice(temp: float, description: str) -> str:
    description = description.lower()

    if temp >= 35:
        return "Extreme heat! Stay indoors and drink water."

    elif 30 <= temp < 35:
        return "Very hot. Avoid direct sunlight."

    elif "thunder" in description:
        return "Thunderstorm expected. Stay safe indoors."

    elif "rain" in description:
        return "Rain expected. Carry an umbrella."

    elif temp <= 10:
        return "Very cold. Wear warm clothes."

    elif 10 < temp <= 18:
        return "Cool weather. Wear a light jacket."

    elif "fog" in description or "mist" in description:
        return "Low visibility. Be careful while traveling."

    elif "cloud" in description:
        return "Cloudy weather. Good for outdoor plans."

    else:
        return "Nice weather. Good day to go outside."
def get_weather(query: str) -> str:
    """
    Get live weather information from OpenWeatherMap.
    """

    api_key = os.getenv("OPENWEATHER_API_KEY")

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={query}&appid={api_key}&units=metric"
    )

    response = requests.get(url)

    if response.status_code != 200:
        return f"Error {response.status_code}: {response.text}"

    data = response.json()

    temp = data["main"]["temp"]
    description = data["weather"][0]["description"]

    advice = get_weather_advice(temp, description)

    return (
        f"Current weather in {query}: {temp}°C, {description}\n"
        f"Advice: {advice}"
    )


def get_current_time(query: str) -> str:
    """
    Get the current time for any city.
    """

    geolocator = Nominatim(user_agent="weatherwise_ai")

    location = geolocator.geocode(query)

    if not location:
        return f"Could not find location: {query}"

    tf = TimezoneFinder()

    timezone_name = tf.timezone_at(
        lat=location.latitude,
        lng=location.longitude
    )

    if not timezone_name:
        return f"Could not determine timezone for {query}"

    tz = ZoneInfo(timezone_name)
    now = datetime.datetime.now(tz)

    return (
        f"The current time in {query} is "
        f"{now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"
    )


def get_time_difference(city1: str, city2: str) -> str:
    geolocator = Nominatim(user_agent="weatherwise_ai")
    tf = TimezoneFinder()

    loc1 = geolocator.geocode(city1)
    loc2 = geolocator.geocode(city2)

    if not loc1 or not loc2:
        return f"Could not find one of the cities: {city1}, {city2}"

    tz1 = tf.timezone_at(lng=loc1.longitude, lat=loc1.latitude)
    tz2 = tf.timezone_at(lng=loc2.longitude, lat=loc2.latitude)

    if not tz1 or not tz2:
        return "Timezone not found"

    # ✅ FIX: compare UTC offsets (correct method)
    now = datetime.datetime.utcnow()

    offset1 = ZoneInfo(tz1).utcoffset(now).total_seconds()
    offset2 = ZoneInfo(tz2).utcoffset(now).total_seconds()

    diff_hours = abs(offset1 - offset2) / 3600

    return f"""
🌍 Time Comparison

{city1}: {tz1}
{city2}: {tz2}

⏱ Difference: ~{diff_hours:.1f} hours
"""


def get_forecast(query: str) -> str:
    """
    Get a 5-day weather forecast.
    """

    api_key = os.getenv("OPENWEATHER_API_KEY")

    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?q={query}&appid={api_key}&units=metric"
    )

    response = requests.get(url)

    if response.status_code != 200:
        return f"Error {response.status_code}: {response.text}"

    data = response.json()

    forecast = f"5-Day Forecast for {query}\n\n"

    for item in data["list"]:
        date_time = item["dt_txt"]

        if "12:00:00" in date_time:
            temp = item["main"]["temp"]
            description = item["weather"][0]["description"]

            forecast += (
                f"📅 {date_time.split()[0]}\n"
                f"🌡 Temperature: {temp}°C\n"
                f"☁ Weather: {description}\n\n"
            )

    return forecast

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="You are a helpful AI assistant designed to provide accurate and useful information.",
    tools=[
    get_weather,
    get_current_time,
    get_time_difference,
    get_forecast,
]
)

app = App(
    root_agent=root_agent,
    name="app",
)
