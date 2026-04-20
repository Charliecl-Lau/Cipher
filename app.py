"""
Cipher — Streamlit front-end entry point.
"""
from __future__ import annotations
import os

# Suppress gRPC/ALTS noise printed to stderr by the google-genai native layer
os.environ.setdefault("GRPC_VERBOSITY", "NONE")

import streamlit as st
from ui.state import init_state
from ui.pages.landing import landing_page
from ui.pages.game import game_page
from ui.pages.reveal import reveal_page

st.set_page_config(
    page_title="Cipher",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_state()
page = st.session_state.get("page", "landing")

if page == "landing":
    landing_page()
elif page == "game":
    game_page()
elif page == "reveal":
    reveal_page()
