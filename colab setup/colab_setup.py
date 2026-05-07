"""
scripts/colab_setup.py
----------------------
One-click setup for Google Colab.

Run this cell FIRST in your Colab notebook before anything else.
It installs all dependencies, mounts Google Drive, and adds the
project folder to sys.path.

Usage
-----
    !python scripts/colab_setup.py
    # OR paste the contents into a Colab cell and run it
"""

import subprocess
import sys
import os

# ── 1. Install packages ───────────────────────────────────────
PACKAGES = [
    "fast-flights @ git+https://github.com/AWeirdDev/flights.git@dev",
    "selectolax",
    "pandas",
    "gradio",
    "gtts",
    "librosa",
    "soundfile",
    "numpy",
]

UPGRADE_PACKAGES = [
    "bitsandbytes",
    "accelerate",
    "transformers==4.57.6",
    "tenacity",
    "huggingface_hub",
]

print("📦 Installing packages…")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--force-reinstall"] + PACKAGES)
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-U"] + UPGRADE_PACKAGES)
print("✅ Packages installed\n")

# ── 2. Mount Google Drive ─────────────────────────────────────
try:
    from google.colab import drive
    drive.mount("/content/drive")
    print("✅ Google Drive mounted\n")
except Exception:
    print("⚠️  Not in Colab or Drive already mounted\n")

# ── 3. Add project to sys.path ────────────────────────────────
DRIVE_DIR = "/content/drive/MyDrive/flight_agent"

if DRIVE_DIR not in sys.path:
    sys.path.insert(0, DRIVE_DIR)
    print(f"✅ Added {DRIVE_DIR} to sys.path\n")

# ── 4. Verify key files exist ─────────────────────────────────
required = [
    os.path.join(DRIVE_DIR, "airports.csv"),
    os.path.join(DRIVE_DIR, "main.py"),
]

all_ok = True
for f in required:
    if os.path.exists(f):
        print(f"  ✅ Found: {f}")
    else:
        print(f"  ❌ Missing: {f}  ← upload this file to Drive")
        all_ok = False

if all_ok:
    print("\n🚀 Setup complete! Run: exec(open('main.py').read())")
else:
    print("\n⚠️  Some files are missing. Upload them to My Drive/flight_agent/ and re-run.")
