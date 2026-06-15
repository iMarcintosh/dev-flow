"""Real web tools implementation for custom agents."""

import logging
import os
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for information. Returns titles, URLs, and snippets."""
    max_results = min(max_results, 10)

    searxng_url = os.environ.get("SEARXNG_URL", "http://searxng:8080")

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                f"{searxng_url}/search",
                params={
                    "q": query,
                    "format": "json",
                    "categories": "general",
                    "language": "de-DE",
                    "pageno": 1,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

        results = data.get("results", [])[:max_results]
        if not results:
            return f"No results found for: {query}"

        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(
                f"{i}. {r.get('title', 'No title')}\n"
                f"   URL: {r.get('url', '')}\n"
                f"   {r.get('content', '')}"
            )
        return "\n\n".join(formatted)

    except Exception as e:
        logger.error(f"Web search error: {e}")
        return f"Search error: {str(e)}"


@tool
def read_url(url: str) -> str:
    """
    Fetch and extract text content from a URL.
    
    Args:
        url: The URL to fetch
    
    Returns:
        Extracted text content from the webpage (up to 20,000 characters)
    """
    try:
        # Fetch URL
        response = httpx.get(
            url,
            timeout=15,
            follow_redirects=True,
            verify=False,  # Disable SSL verification for development
            headers={"User-Agent": "Mozilla/5.0 (compatible; DevFlowBot/1.0)"}
        )
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type.lower():
            return f"Unsupported content-type: {content_type}\nURL: {url}"
        
        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script, style, and other non-content tags
        for tag in soup(["script", "style", "noscript", "iframe", "nav", "footer", "header"]):
            tag.decompose()
        
        # Extract text
        text = soup.get_text(separator=" ", strip=True)
        
        # Clean up whitespace
        text = " ".join(text.split())
        
        # Limit length
        if len(text) > 20000:
            text = text[:20000] + "\n\n[Content truncated...]"
        
        return f"Content from {url}:\n\n{text}"
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error reading URL {url}: {e}")
        return f"Failed to fetch URL: {str(e)}"
    except Exception as e:
        logger.error(f"Error reading URL {url}: {e}")
        return f"Error reading URL: {str(e)}"


@tool
def read_url_jina(url: str) -> str:
    """
    Fetch and extract text from a URL using Jina AI Reader (fallback for JavaScript-heavy sites).
    
    Args:
        url: The URL to fetch
    
    Returns:
        Extracted text content in markdown format
    """
    try:
        # Use Jina AI Reader API
        jina_url = f"https://r.jina.ai/{url}"
        
        response = httpx.get(
            jina_url,
            timeout=30,
            headers={"User-Agent": "DevFlow/1.0"}
        )
        response.raise_for_status()
        
        content = response.text
        
        # Limit length
        if len(content) > 20000:
            content = content[:20000] + "\n\n[Content truncated...]"
        
        return f"Content from {url} (via Jina Reader):\n\n{content}"
        
    except Exception as e:
        logger.error(f"Error reading URL with Jina {url}: {e}")
        return f"Error reading URL with Jina Reader: {str(e)}"


@tool
def get_weather(location: str) -> str:
    """
    Get current weather for a location using Open-Meteo API (no API key needed).
    
    Args:
        location: City name (e.g., "Berlin", "Gelnhausen", "München")
    
    Returns:
        Current weather information including temperature, conditions, humidity, wind speed
    """
    import httpx
    
    try:
        # Step 1: Geocode city name to lat/lon
        geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        geocode_params = {
            "name": location,
            "count": 1,
            "language": "de",
            "format": "json"
        }
        
        with httpx.Client(timeout=10.0) as client:
            geo_response = client.get(geocode_url, params=geocode_params)
            geo_response.raise_for_status()
            geo_data = geo_response.json()
        
        if not geo_data.get("results"):
            return f"❌ Stadt '{location}' nicht gefunden. Bitte überprüfe die Schreibweise."
        
        result = geo_data["results"][0]
        lat = result["latitude"]
        lon = result["longitude"]
        city_name = result["name"]
        country = result.get("country", "")
        
        # Step 2: Get weather data
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation",
            "timezone": "auto"
        }
        
        with httpx.Client(timeout=10.0) as client:
            weather_response = client.get(weather_url, params=weather_params)
            weather_response.raise_for_status()
            weather_data = weather_response.json()
        
        current = weather_data["current"]
        
        # Map weather code to German description
        weather_codes = {
            0: "Klar",
            1: "Überwiegend klar",
            2: "Teilweise bewölkt",
            3: "Bewölkt",
            45: "Nebelig",
            48: "Nebel mit Reifablagerung",
            51: "Leichter Nieselregen",
            53: "Mäßiger Nieselregen",
            55: "Starker Nieselregen",
            61: "Leichter Regen",
            63: "Mäßiger Regen",
            65: "Starker Regen",
            71: "Leichter Schneefall",
            73: "Mäßiger Schneefall",
            75: "Starker Schneefall",
            77: "Schneegriesel",
            80: "Leichte Regenschauer",
            81: "Mäßige Regenschauer",
            82: "Starke Regenschauer",
            85: "Leichte Schneeschauer",
            86: "Starke Schneeschauer",
            95: "Gewitter",
            96: "Gewitter mit leichtem Hagel",
            99: "Gewitter mit starkem Hagel"
        }
        
        weather_code = current.get("weather_code", 0)
        condition = weather_codes.get(weather_code, "Unbekannt")
        
        # Format response
        temp = current.get("temperature_2m", "N/A")
        humidity = current.get("relative_humidity_2m", "N/A")
        wind = current.get("wind_speed_10m", "N/A")
        precip = current.get("precipitation", 0)
        time = current.get("time", "N/A")
        
        result_text = f"""🌤️ Wetter in {city_name}, {country}

📍 Standort: {lat}°N, {lon}°E
🌡️ Temperatur: {temp}°C
☁️ Bedingung: {condition}
💧 Luftfeuchtigkeit: {humidity}%
💨 Wind: {wind} km/h
🌧️ Niederschlag: {precip} mm
🕐 Messung: {time}

Quelle: Open-Meteo.com"""

        return result_text
        
    except httpx.HTTPError as e:
        return f"❌ Netzwerkfehler beim Abrufen der Wetterdaten: {str(e)}"
    except KeyError as e:
        return f"❌ Unerwartetes Datenformat von der Wetter-API: Feld {str(e)} fehlt"
    except Exception as e:
        return f"❌ Fehler beim Abrufen der Wetterdaten: {str(e)}"

