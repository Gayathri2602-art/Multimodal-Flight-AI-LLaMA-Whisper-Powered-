"""
utils/models.py
---------------
Load LLaMA 3.2 (4-bit quantised) and Whisper ASR pipeline.

Returns
-------
    load_models() -> (tokenizer, llm_model, asr_pipe)

Call this once at startup and pass the objects into the agent.
"""

from __future__ import annotations

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline,
)

from config.settings import (
    LLM_MODEL_ID,
    ASR_MODEL_ID,
    USE_4BIT_QUANT,
    BNB_4BIT_DOUBLE_QUANT,
    BNB_COMPUTE_DTYPE,
    BNB_QUANT_TYPE,
)


def _build_quant_config() -> BitsAndBytesConfig | None:
    if not USE_4BIT_QUANT:
        return None

    dtype_map = {"bfloat16": torch.bfloat16, "float16": torch.float16}
    compute_dtype = dtype_map.get(BNB_COMPUTE_DTYPE, torch.bfloat16)

    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=BNB_4BIT_DOUBLE_QUANT,
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_quant_type=BNB_QUANT_TYPE,
    )


def load_llm(model_id: str = LLM_MODEL_ID):
    """Load and return (tokenizer, model)."""
    print(f"[models] Loading LLM: {model_id} …")
    quant_config = _build_quant_config()

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="auto",
        quantization_config=quant_config,
    )
    print("[models] ✅ LLM ready")
    return tokenizer, model


def load_asr(model_id: str = ASR_MODEL_ID):
    """Load and return Whisper ASR pipeline."""
    print(f"[models] Loading ASR: {model_id} …")
    asr = pipeline(
        "automatic-speech-recognition",
        model=model_id,
        dtype=torch.float16,
        device=0,
        return_timestamps=True,
    )
    print("[models] ✅ ASR ready")
    return asr


def load_models(llm_id: str = LLM_MODEL_ID, asr_id: str = ASR_MODEL_ID):
    """
    Load both models and return (tokenizer, llm_model, asr_pipe).
    This is the main entry point used by main.py.
    """
    tokenizer, llm_model = load_llm(llm_id)
    asr_pipe              = load_asr(asr_id)
    return tokenizer, llm_model, asr_pipe
