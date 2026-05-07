"""
agent/responder.py
------------------
All responses that involve calling the LLM or building templated strings.

The LLM (llm_model / tokenizer) is passed in at call time rather than
imported as a global — this keeps the module testable without GPU.

Public API
----------
    describe_flights(df, dep, dst, pretty_date) -> str
    confirm_booking(chosen, llm_model, tokenizer)  -> str
"""

from __future__ import annotations

import pandas as pd
import torch

from config.settings import LLM_MAX_NEW_TOKENS, LLM_CONFIRM_MAX_TOKENS, LLM_DO_SAMPLE


# ─────────────────────────────────────────
# LOW-LEVEL LLM CALL
# ─────────────────────────────────────────
def llm_call(prompt: str, llm_model, tokenizer, max_tokens: int = LLM_MAX_NEW_TOKENS) -> str:
    """
    Run a single completion through the loaded LLaMA model.

    Parameters
    ----------
    prompt      : Full prompt string (including 'Assistant:' suffix)
    llm_model   : AutoModelForCausalLM instance (already on GPU)
    tokenizer   : Matching AutoTokenizer instance
    max_tokens  : Max new tokens to generate

    Returns
    -------
    The generated text after 'Assistant:' in the output.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(llm_model.device)

    with torch.no_grad():
        out = llm_model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=LLM_DO_SAMPLE,
            eos_token_id=tokenizer.eos_token_id,
        )

    full = tokenizer.decode(out[0], skip_special_tokens=True)
    return full.split("Assistant:")[-1].strip()


# ─────────────────────────────────────────
# TEMPLATED RESPONSES (no LLM needed)
# ─────────────────────────────────────────
def describe_flights(df: pd.DataFrame, dep: str, dst: str, pretty_date: str) -> str:
    """
    Build a concise flight summary without calling the LLM.
    Cheaper and more predictable than free-form generation.
    """
    total     = len(df)
    cheapest  = df.loc[df["price"].idxmin()]
    fastest   = df.loc[df["duration_min"].idxmin()]
    min_price = df["price"].min()
    max_price = df["price"].max()

    return (
        f"I found {total} flights from {dep} to {dst} on {pretty_date}. "
        f"Prices range from Rs {min_price:,} to Rs {max_price:,}. "
        f"The cheapest is {cheapest['airline']} at Rs {cheapest['price']:,}. "
        f"The fastest takes {fastest['duration']}. "
        "Do you prefer cheapest, fastest, non-stop, or a specific airline?"
    )


# ─────────────────────────────────────────
# LLM-POWERED CONFIRMATION
# ─────────────────────────────────────────
_CONFIRM_FALLBACK = (
    "Great choice! Your {airline} flight departing {departure} "
    "for {price} is confirmed. "
    "Our support agent will contact you for payment details. Safe travels! ✈️"
)

_CONFIRM_PROMPT_TEMPLATE = """\
You are a friendly flight booking assistant. Reply in 2 sentences only.
Airline: {airline}
Departure: {departure}
Arrival: {arrival}
Price: {price}
Duration: {duration}
Stops: {stops}

Confirm the booking warmly. Say a support agent will contact for payment.
Assistant:"""


def confirm_booking(chosen: dict, llm_model, tokenizer) -> str:
    """
    Generate a warm booking confirmation using the LLM.
    Falls back to a template if the LLM output looks garbled.
    """
    prompt = _CONFIRM_PROMPT_TEMPLATE.format(
        airline=chosen["airline"],
        departure=chosen["departure_str"],
        arrival=chosen["arrival_str"],
        price=chosen["price_str"],
        duration=chosen["duration"],
        stops=chosen["stops"],
    )

    result = llm_call(prompt, llm_model, tokenizer, max_tokens=LLM_CONFIRM_MAX_TOKENS)

    # Sanity check — if the model outputs something weird, use the template
    bad_signs = ["A)", "B)", "1.", "2.", "option", "?"]
    if any(s in result for s in bad_signs) or len(result) < 20:
        return _CONFIRM_FALLBACK.format(
            airline=chosen["airline"],
            departure=chosen["departure_str"],
            price=chosen["price_str"],
        )

    return result
