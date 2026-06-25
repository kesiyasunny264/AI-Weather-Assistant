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

    return f"Current weather in {query}: {temp}°C, {description}"


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
root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="You are a helpful AI assistant designed to provide accurate and useful information.",
    tools=[get_weather, get_current_time],
)

app = App(
    root_agent=root_agent,
    name="app",
)
