import os
from dotenv import load_dotenv

load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="IoDoc",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Init DB
from db.schema import init_db
init_db()

# Create documents dir
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "documents"), exist_ok=True)

# Start background scheduler (once per process)
from notifications.scheduler import start_scheduler
start_scheduler()

# Navigation
pg = st.navigation([
    st.Page("pages/dashboard.py",       title="Dashboard",       icon="🏠"),
    st.Page("pages/profilo.py",         title="Profilo",         icon="👤"),
    st.Page("pages/upload.py",          title="Carica documento",icon="📄"),
    st.Page("pages/piano_sanitario.py", title="Piano sanitario", icon="🏥"),
    st.Page("pages/misurazioni.py",     title="Misurazioni",     icon="📊"),
    st.Page("pages/timeline.py",        title="Timeline",        icon="📅"),
])

pg.run()
