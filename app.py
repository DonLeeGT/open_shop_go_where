import streamlit as st
import hmac
import json
import os
from dotenv import load_dotenv

load_dotenv()

from scraper import scrape_all_units, build_corpus
from rag import build_rag_pipeline, get_vector_store

st.set_page_config(page_title="OpenShopGoWhere", layout="wide")

UNITS_JSON = "resources/place2lease_units.json"
CORPUS_TXT = "resources/place2lease_corpus.txt"


def check_password():
    """Returns True if the user entered the correct password."""
    if st.session_state.get("password_correct", False):
        return True

    st.title("Open Shop Go Where?")
    st.text_input("Password", type="password", key="password_input")

    if st.button("Login"):
        if hmac.compare_digest(st.session_state.password_input, st.secrets["password"]):
            st.session_state.password_correct = True
            st.success("Login successful")
            with st.spinner("Scraping HDB Place2Lease listings..."):
                all_units, corpus = load_place2lease_data()
                st.session_state["place2lease_units"] = all_units
                st.session_state["place2lease_corpus"] = corpus

            with st.spinner("Building RAG pipeline..."):
                vector_store = init_rag()
                st.session_state["vector_store"] = vector_store

            st.session_state["data_loaded"] = True
            st.rerun()
        else:
            st.error("Incorrect password")

    return False


@st.cache_data(show_spinner=False)
def load_place2lease_data():
    all_units = scrape_all_units()

    os.makedirs("resources", exist_ok=True)
    with open(UNITS_JSON, "w", encoding="utf-8") as f:
        json.dump(all_units, f, indent=2, ensure_ascii=False)

    corpus = build_corpus(all_units)
    with open(CORPUS_TXT, "w", encoding="utf-8") as f:
        f.write(corpus)

    return all_units, corpus


@st.cache_resource(show_spinner=False)
def init_rag():
    return build_rag_pipeline()


if not check_password():
    st.stop()

if "place2lease_units" not in st.session_state:
    all_units, corpus = load_place2lease_data()
    st.session_state["place2lease_units"] = all_units
    st.session_state["place2lease_corpus"] = corpus
if "vector_store" not in st.session_state:
    vector_store = init_rag()
    st.session_state["vector_store"] = vector_store

chatbot = st.Page("pages/chatbot.py", title="Chatbot")
about_us = st.Page("pages/about_us.py", title="About Us")
methodology = st.Page("pages/methodology.py", title="Methodology")

pg = st.navigation([chatbot, about_us, methodology])
pg.run()
