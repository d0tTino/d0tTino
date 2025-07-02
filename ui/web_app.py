from __future__ import annotations

import streamlit as st

from scripts.ai_router import send_prompt
from scripts.thm import apply_palette, PALETTES_DIR, REPO_ROOT


st.title("LLM Router")

prompt = st.text_area("Prompt")
if st.button("Send"):
    if prompt:
        result = send_prompt(prompt)
        st.write(result)

st.header("Apply Palette")
options = [p.stem for p in PALETTES_DIR.glob("*.toml")]
palette = st.selectbox("Palette", options)
if st.button("Apply"):
    if palette:
        apply_palette(palette, REPO_ROOT)
        st.success(f"Applied {palette}")

