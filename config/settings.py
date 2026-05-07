"""
config/settings.py
------------------
Central configuration for the AI Flight Booking Agent.
Edit these values to customise paths, models, and behaviour.
"""

import os
from pathlib import Path

# ─────────────────────────────────────────
# ENVIRONMENT DETECTION
# ─────────────────────────────────────────
IS_COLAB = "COLAB_GPU" in os.environ or os.path.exists("/content")

# ─────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────
if IS_COLAB:
    DRIVE_DIR  = Path("/content/drive/MyDrive/flight_agent")
    CACHE_DIR  = DRIVE_DIR / "flight_cache"
    AIRPORTS_CSV = DRIVE_DIR / "airports.csv"
else:
    BASE_DIR   = Path(__file__).resolve().parent.parent
    CACHE_DIR  = BASE_DIR / "flight_cache"
    AIRPORTS_CSV = BASE_DIR / "airports.csv"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────
# MODEL NAMES
# ─────────────────────────────────────────
LLM_MODEL_ID  = "meta-llama/Llama-3.2-3B-Instruct"
ASR_MODEL_ID  = "openai/whisper-medium.en"

# ─────────────────────────────────────────
# QUANTIZATION (4-bit via bitsandbytes)
# ─────────────────────────────────────────
USE_4BIT_QUANT        = True
BNB_4BIT_DOUBLE_QUANT = True
BNB_COMPUTE_DTYPE     = "bfloat16"   # "float16" on older GPUs
BNB_QUANT_TYPE        = "nf4"

# ─────────────────────────────────────────
# INFERENCE
# ─────────────────────────────────────────
LLM_MAX_NEW_TOKENS       = 200
LLM_CONFIRM_MAX_TOKENS   = 100
LLM_DO_SAMPLE            = False

# ─────────────────────────────────────────
# SCRAPER
# ─────────────────────────────────────────
SCRAPER_MAX_RETRIES  = 3
SCRAPER_DEFAULT_SEAT = "economy"
SCRAPER_DEFAULT_TRIP = "one-way"

# ─────────────────────────────────────────
# UI
# ─────────────────────────────────────────
GRADIO_SHARE = True   # set False for local-only
GRADIO_DEBUG = True
HISTORY_TURNS_SHOWN = 8

# ─────────────────────────────────────────
# HUGGINGFACE TOKEN (Colab: uses userdata)
# ─────────────────────────────────────────
HF_TOKEN_ENV_VAR = "HF_TOKEN"   # env var name for local runs
