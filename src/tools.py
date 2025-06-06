from langchain.tools import tool
import datetime
import requests
import os


@tool
def get_date() -> str:
    """Returns the current date."""
    return datetime.datetime.now().strftime("%A, %d %B %Y")


@tool
def get_time() -> str:
    """Returns the current time."""
    return datetime.datetime.now().strftime("%I:%M %p")


@tool
def get_weather(city: str) -> str:
    """Returns the current weather in the given city."""
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    if not API_KEY:
        return "Weather API key not found."
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        res = requests.get(url).json()
        if res.get("cod") != 200:
            return f"Could not fetch weather: {res.get('message', 'Unknown error')}"
        temp = res["main"]["temp"]
        desc = res["weather"][0]["description"]
        return f"The current temperature in {city} is {temp}°C with {desc}."
    except Exception as e:
        return f"Failed to fetch weather data: {str(e)}"


@tool
def get_news(topic: str) -> str:
    """Returns top 3 headlines from India."""
    API_KEY = os.getenv("NEWSAPI_KEY")
    if not API_KEY:
        return "News API key not found."
    url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={API_KEY}"
    try:
        res = requests.get(url).json()
        if res["status"] != "ok":
            return "Unable to fetch news."
        headlines = [article["title"] for article in res["articles"][:3]]
        return "Top headlines:\n" + "\n".join(headlines)
    except Exception as e:
        return f"Failed to fetch news: {str(e)}"
