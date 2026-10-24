import streamlit as st

st.title("About Us")

st.header("Project Scope")
st.write(
    "**Open Shop Go Where?** is an AI-powered chatbot designed to help prospective tenants "
    "explore and understand HDB commercial property listings available on the "
    "[Place2Lease](https://place2lease.hdb.gov.sg/public) portal. "
    "The application provides an intuitive conversational interface for querying "
    "unit details, tenancy conditions, bidding rules, and frequently asked questions — "
    "all in one place."
)

st.divider()

st.header("Objectives")
st.markdown("""
1. **Simplify information access** — Replace the need to manually browse individual listings and read through lengthy terms and conditions by enabling user-centric, natural language queries such as:
    - *(location-related)* I want to open shop in the west
    - *(trade-related)* I want to open a cafe
2. **Provide up-to-date data** — Scrape live listing data from the Place2Lease API on every app startup, ensuring users always see current availability.
3. **Consolidate knowledge sources** — Combine scraped listings with reference documents (FAQ, e-Bidding T&C, town-region mapping) into a single searchable knowledge base.
4. **Deliver accurate, grounded answers** — Use Retrieval-Augmented Generation (RAG) to ensure responses are based on actual data rather than general knowledge.
""")

st.divider()

st.header("Data Sources")
st.markdown("""
| Source | Type | Description |
|--------|------|-------------|
| [Place2Lease API](https://place2lease.hdb.gov.sg/public) | Live API (scraped) | All current HDB commercial unit listings — unit details, floor area, tenure, allowed trades, and important unit conditions |
| FAQ.txt | Text file | Frequently asked questions about the Place2Lease portal |
| e-Bidding Terms and Conditions | PDF | Rules, requirements, and terms for the e-bidding process |
| town_region.txt | Text file | Town-to-region mapping for location-based queries (e.g. Bedok → East) |
""")

st.divider()

st.header("Features")
st.markdown("""
- **Live Data Scraping** — Automatically fetches all available unit listings from the Place2Lease public API on startup, with full pagination support.
- **Region & Trade Awareness** — Units are enriched with region data, and the chatbot understands allowed/excluded trades and "Open Trade" designations.
- **RAG-Powered Chatbot** — Ask questions in natural language and get answers grounded in actual listing data and reference documents, with direct links to unit listings.
- **Source Transparency** — Every chatbot response includes expandable source citations showing which document chunks were used.
- **Multi-Document Knowledge Base** — Ingests PDF, text files, and scraped web data into a unified vector store for comprehensive search.
- **Secure Access** — Password-protected login to control access to the application.
""")
