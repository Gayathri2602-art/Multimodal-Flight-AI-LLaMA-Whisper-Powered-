"""
ui/gradio_app.py
----------------
Gradio web interface for the AI Flight Booking Agent.
Supports voice input (Whisper) and text input, with voice reply (gTTS).

Usage
-----
    from ui.gradio_app import build_app
    app = build_app(tokenizer, llm_model, asr_pipe)
    app.launch(share=True)
"""

from __future__ import annotations

import gradio as gr

from agent.handler import handle_turn
from agent.session import new_session, append_history, format_history
from utils.audio import transcribe, tts
from config.settings import GRADIO_SHARE, GRADIO_DEBUG


# ─────────────────────────────────────────
# PROCESS FUNCTION
# ─────────────────────────────────────────
def _make_process_fn(tokenizer, llm_model, asr_pipe):
    """
    Factory that closes over the model references and returns the
    Gradio event handler function.
    """

    def process(audio, text_input, session):
        user_text = ""

        # Priority 1: transcribe audio
        if audio:
            user_text = transcribe(audio, asr_pipe)

        # Priority 2: typed text
        if not user_text:
            user_text = (text_input or "").strip()

        if not user_text:
            return (
                "",
                "Please type or speak your travel details "
                "(e.g. 'Goa to Bangalore tomorrow').",
                None,
                "",
                session,
            )

        response, session = handle_turn(user_text, session, llm_model, tokenizer)
        append_history(session, user_text, response)

        audio_reply = tts(response)
        history_txt = format_history(session)

        return user_text, response, audio_reply, history_txt, session

    return process


def _make_reset_fn():
    def reset():
        return (
            "",
            "Tell me where and when you want to fly!",
            None,
            "",
            new_session(),
        )
    return reset


# ─────────────────────────────────────────
# BUILD APP
# ─────────────────────────────────────────
def build_app(tokenizer, llm_model, asr_pipe) -> gr.Blocks:
    """
    Construct and return the Gradio Blocks app.
    Call .launch() on the returned object to start the server.
    """
    process_fn = _make_process_fn(tokenizer, llm_model, asr_pipe)
    reset_fn   = _make_reset_fn()

    with gr.Blocks(title="AI Flight Booking Agent", theme=gr.themes.Soft()) as demo:

        gr.Markdown(
            """
            <div style="text-align:center; padding: 10px 0;">
                <h2>✈️ AI Flight Booking Agent</h2>
                <p style="color:#666;"><b>Project by Gayathri VR</b></p>
            </div>

            **How to use:**
            1. Say or type: *"Goa to Bangalore tomorrow one way"*
            2. Agent scrapes live flights and summarises them
            3. Filter: *"cheapest"* / *"morning"* / *"IndiGo"* / *"non-stop"*
            4. Pick: *"2"*
            5. Done! Type *"reset"* to search again.
            """
        )

        state = gr.State(new_session())

        with gr.Row():
            # ── Left column: inputs ───────────────────────────
            with gr.Column(scale=1):
                audio_in = gr.Audio(
                    sources=["microphone"],
                    type="filepath",
                    label="🎤 Speak",
                )
                text_in = gr.Textbox(
                    label="⌨️  Or type here",
                    placeholder="e.g. Goa to Bangalore tomorrow one way",
                )
                with gr.Row():
                    send_btn  = gr.Button("Send ➤",  variant="primary")
                    reset_btn = gr.Button("Reset 🔄", variant="secondary")

                gr.Markdown(
                    "**Filter examples after results:**\n"
                    "`cheapest`  `morning`  `afternoon`  `evening`\n"
                    "`non-stop`  `IndiGo`  `Air India`  `SpiceJet`\n"
                    "`fastest`  `fewest stops`"
                )

            # ── Right column: outputs ─────────────────────────
            with gr.Column(scale=1):
                said_box  = gr.Textbox(label="You said",    interactive=False)
                reply_box = gr.Textbox(label="Agent reply", interactive=False, lines=14)
                audio_out = gr.Audio(label="🔊 Voice reply", autoplay=True)

        history_box = gr.Textbox(
            label="Conversation history", lines=10, interactive=False
        )

        # ── Event wiring ──────────────────────────────────────
        outputs = [said_box, reply_box, audio_out, history_box, state]

        send_btn.click(
            fn=process_fn,
            inputs=[audio_in, text_in, state],
            outputs=outputs,
        )
        text_in.submit(
            fn=lambda t, s: process_fn(None, t, s),
            inputs=[text_in, state],
            outputs=outputs,
        )
        reset_btn.click(
            fn=reset_fn,
            outputs=outputs,
        )

    return demo
