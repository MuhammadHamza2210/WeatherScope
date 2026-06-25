# WeatherScope 🌤️

> 🔴 **Live demo:** **https://weatherscope-stlgpbewcgqufpmrbossmt.streamlit.app/**

A premium weather app built with **Python + Streamlit** and an animated
Three.js front-end. Shows current weather, air quality, a 7-day forecast and
30-day history, blending OpenWeatherMap and Open-Meteo data.

By **Muhammad Hamza**.

## Run locally

```bash
pip install -r requirements.txt
streamlit run weatherscope_app.py
```

## API key (kept out of GitHub)

This app calls the OpenWeatherMap API. The key is **never hardcoded** — it is
read from Streamlit secrets or an environment variable.

- **Local:** create `.streamlit/secrets.toml` (gitignored) with:
  ```toml
  OWM_KEY = "your_openweathermap_key"
  ```
- **Streamlit Cloud:** add the same key under **App → Settings → Secrets**.

Get a free key at https://openweathermap.org/api.
