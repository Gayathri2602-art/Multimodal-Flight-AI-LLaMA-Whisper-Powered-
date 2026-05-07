# ✈️ Flight AI — Multimodal AI Flight Booking Agent
### Whisper + LLaMA + Google Flights Scraper

An intelligent end-to-end AI-powered flight booking assistant that allows users to search, filter, and select flights using **voice or text input**. The system integrates LLMs, speech recognition, web scraping, and a Gradio UI to simulate a real-world travel booking experience.

> **Project by Gayathri VR**

---

## 🚀 Overview

Flight AI is a multimodal AI-powered flight booking assistant that lets users:

- 🎤 **Speak or type** travel requests
- ✈️ **Search real-time** flight data
- 🧠 **Use natural language** to filter flights
- 💬 **Chat with an AI** travel agent
- 🔊 **Receive voice responses**

It simulates a real conversational flight booking experience using LLMs + live flight data.

---

## 🎬 Demo

▶ [Demo Video: demo_flightAI.mp4](./demo_flightAI.mp4)

---

## 🖼️ UI Preview

![Gradio UI](webpage_image.png)

---

## 📖 Story Behind This Project

This project started with a simple idea:

> *"Can I build an AI that books flights like a real travel agent?"*

I wanted users to speak naturally:

```
"Goa to Bangalore tomorrow one way"
```

and get a full:

```
flight search  →  comparison  →  recommendation  →  booking flow
```

---

## ❌ The Problem

There was **no usable flight API**:

| API | Problem |
|---|---|
| Google Flights API | Discontinued |
| RapidAPI | Limited & expensive |
| Amadeus API | Restricted access |
| Playwright scraping | Slow & unstable |

So the core challenge was: **no reliable way to get real-time flight data.**

---

## 💡 The Breakthrough

Instead of scraping UI, I discovered:

👉 **[https://github.com/AWeirdDev/flights](https://github.com/AWeirdDev/flights)**

This library:
- Builds Google Flights query URLs
- Extracts structured flight data
- Avoids browser automation

This became the **backbone of the system.**

---

## 🔧 What I Built On Top

I modified and extended the scraper for my AI system:

### ✅ My Improvements
- Added city → IATA mapping system
- Integrated Google Drive caching for Colab
- Added robust retry system
- Fixed datetime parsing issues
- Structured output for LLM consumption
- Converted raw flight objects → clean DataFrame

### ✨ Modified Scraper Behavior

Instead of raw scraping, my system works like this:

```python
scrape("Mumbai", "Delhi", "2026-05-08")
```

Internally becomes:

```
1. Convert city → IATA  (Mumbai → BOM, Delhi → DEL)
2. Build query using fast-flights
3. Fetch structured results
4. Normalize: price, duration, stops, airline
5. Cache CSV to Drive
6. Return clean dataset to LLM
```

---

## 🗣️ Example Conversation

```
You:    "Goa to Bangalore tomorrow one way"

Agent:  "I found 12 flights from Goa to Bangalore on May 8.
         Prices range from Rs 3,200 to Rs 11,500.
         The cheapest is IndiGo at Rs 3,200.
         Do you prefer cheapest, fastest, non-stop, or a specific airline?"

You:    "non-stop morning"

Agent:  "Top 3 flights (non-stop, morning, sorted by price):
         1. IndiGo     06:10 → 07:45  1h 35m  Non-stop  Rs.3,200
         2. Air India  07:30 → 09:05  1h 35m  Non-stop  Rs.4,800
         3. Vistara    09:15 → 10:50  1h 35m  Non-stop  Rs.5,100"

You:    "1"

Agent:  "Great choice! Your IndiGo flight departing 06:10
         for Rs.3,200 is confirmed. Our support agent will
         contact you for payment. Safe travels! ✈️"
```

---

## 📁 Project Structure

```
flight_agent/
├── config/
│   └── settings.py          # All constants, paths, model names
├── scraper/
│   ├── __init__.py
│   ├── iata.py              # City → IATA code lookup
│   ├── date_parser.py       # Natural language date parsing
│   └── flights.py           # Core Google Flights scraper
├── agent/
│   ├── __init__.py
│   ├── intent.py            # NLP intent extraction (route + date)
│   ├── filter.py            # Flight preference filtering & sorting
│   ├── session.py           # Conversation session state management
│   ├── responder.py         # LLM response generation
│   └── handler.py           # Main turn-by-turn conversation logic
├── ui/
│   ├── __init__.py
│   └── gradio_app.py        # Gradio web UI (voice + text)
├── utils/
│   ├── __init__.py
│   ├── audio.py             # Whisper ASR + gTTS TTS helpers
│   └── models.py            # Model loading (LLaMA + Whisper)
├── tests/
│   ├── test_scraper.py
│   ├── test_intent.py
│   └── test_filter.py
├── airports.csv             # Airport data for IATA lookup
├── demo_flightAI.mp4        # demo how project works
├── requirements.txt
├── .gitignore
└── main.py                  # Entry point
```

---

## 🧪 Tech Stack

| Component | Technology |
|---|---|
| 🧠 LLM | LLaMA 3.2 3B Instruct (via HuggingFace) |
| 🎤 Speech Recognition | OpenAI Whisper medium.en |
| ✈️ Flight Data | fast-flights (Google Flights backend) |
| 📊 Data Processing | Pandas |
| 🔊 Text-to-Speech | gTTS |
| 🎛️ Web UI | Gradio |

---

## ⚙️ Compute Environment

This project was developed and tested on:

-  **Visual Studio**
-  **Google Colab**
-  **T4 GPU** (NVIDIA Tesla T4)
-  **Python 3.10+**
-  **Google Drive** mounted storage for caching flight data

---

## 🚀 Quick Start

### Google Colab (Recommended)

```python
# Step 1: Run setup
exec(open('scripts/colab_setup.py').read())

# Step 2: Launch
exec(open('main.py').read())
```

### Local Setup

```bash
git clone https://github.com/YOUR_USERNAME/flight-agent.git
cd flight-agent

pip install -r requirements.txt

export HF_TOKEN=your_huggingface_token

python main.py
```

---

## ⚠️ Limitations

- Google Flights structure may change over time
- Scraping depends on third-party library stability
- No real payment / booking API integrated yet

---

## 🔮 Future Improvements

**Real Booking System**
- Live ticketing API integration
- Payment gateway

**Smarter AI Agent**
- Tool-calling LLM agent
- Personalized recommendations

**Production Version**
- React frontend
- Mobile app
- Cloud deployment (HuggingFace / AWS)

---

## 🧠 Summary

This project is the result of:

> multiple failed APIs + broken scrapers + debugging ASR/LLM pipelines → finally converging into a **stable multimodal flight assistant.**

---

## 📄 License

MIT — free to use, modify, and distribute.
