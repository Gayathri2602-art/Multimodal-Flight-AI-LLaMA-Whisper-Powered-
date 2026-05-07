"""
main.py
-------
Entry point for the AI Flight Booking Agent.

Run locally:
    python main.py

Run in Google Colab:
    exec(open('main.py').read())   # after running scripts/colab_setup.py
"""

import os
import sys

# ── HuggingFace login ─────────────────────────────────────────
from config.settings import IS_COLAB, HF_TOKEN_ENV_VAR

if IS_COLAB:
    try:
        from google.colab import userdata
        from huggingface_hub import login

        hf_token = userdata.get("myHF_TOKEN")
        login(hf_token, add_to_git_credential=True)
        print("[main] ✅ HuggingFace login successful (Colab)")
    except Exception as exc:
        print(f"[main] ⚠️  HuggingFace login warning: {exc}")
else:
    token = os.environ.get(HF_TOKEN_ENV_VAR)
    if token:
        from huggingface_hub import login
        login(token)
        print("[main] ✅ HuggingFace login successful (env var)")
    else:
        print(
            f"[main] ⚠️  {HF_TOKEN_ENV_VAR} not set. "
            "Set it if accessing gated models (e.g. LLaMA)."
        )

# ── Load models ───────────────────────────────────────────────
from utils.models import load_models

print("\n[main] Loading models — this may take a few minutes on first run…\n")
tokenizer, llm_model, asr_pipe = load_models()

# ── Build and launch UI ───────────────────────────────────────
from ui.gradio_app import build_app
from config.settings import GRADIO_SHARE, GRADIO_DEBUG

app = build_app(tokenizer, llm_model, asr_pipe)

print("\n[main] ✅ All systems ready. Launching Gradio…\n")
app.launch(share=GRADIO_SHARE, debug=GRADIO_DEBUG)
