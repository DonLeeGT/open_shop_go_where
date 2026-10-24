# Open Shop Go Where?

A Streamlit-based RAG chatbot that helps users explore HDB commercial property listings from [Place2Lease](https://place2lease.hdb.gov.sg/public).

## What It Does

1. **Scrapes** all current HDB commercial unit listings from the Place2Lease public API
2. **Enriches** each unit with region data from a town-to-region mapping file
3. **Ingests** the scraped data alongside reference documents (FAQ, e-Bidding T&C, town-region mapping)
4. **Builds a RAG pipeline** — chunks the documents, embeds them with OpenAI, and stores vectors in ChromaDB
5. **Answers questions** about available units, lease conditions, tendering processes, regions, trades, and more — with direct links to listings

## Project Structure

```
app.py                  # Streamlit entry point (login, scraper init, RAG init)
scraper.py              # Fetches unit listings & details from Place2Lease API
rag.py                  # RAG pipeline: load, chunk, embed, retrieve, generate
run.command             # One-click launcher (installs deps, opens Chrome, runs app)
terminal.command        # Opens a terminal in the project directory
pages/
  chatbot.py            # RAG chatbot interface
  about_us.py           # Project scope, objectives, data sources, and features
  methodology.py        # Data flows, implementation details, and flowcharts
resources/
  FAQ.txt               # Place2Lease FAQ
  e-Bidding Terms and Conditions.pdf
  town_region.txt       # Town-to-region mapping (e.g. Bedok → East)
  trade.txt             # Trade-related reference data
  place2lease_units.json   # Scraped unit data (generated at startup)
  place2lease_corpus.txt   # Plain-text corpus with region info (generated at startup)
.env                    # OpenAI API key (not committed)
requirements.txt        # Python dependencies
build_rag.ipynb         # Reference notebook for RAG pipeline
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure secrets

Create `.streamlit/secrets.toml`:

```toml
password = "your-app-password"
```

Create `.env` in the project root:

```
OPENAI_API_KEY=sk-...
```

### 3. Run the app

**Option A** — Double-click `run.command` (installs deps, opens Chrome, launches app)

**Option B** — Run manually:

```bash
streamlit run app.py
```

## How It Works

### Scraper (`scraper.py`)

- Calls the Place2Lease search API to discover all available unit IDs (with full pagination)
- For each unit, fetches detailed info via the unit detail API
- Uses **BeautifulSoup** to parse HTML in the "Important Unit Conditions" field into clean text
- Outputs structured JSON and a plain-text corpus

### RAG Pipeline (`rag.py`)

| Step | What Happens |
|------|-------------|
| **Pre-Retrieval Enhancement** | Enriches each unit's corpus entry with region data from `town_region.txt` |
| **Document Loading** | Loads 1 PDF (via pypdf), FAQ.txt, town_region.txt, and the scraped corpus |
| **Splitting & Chunking** | `RecursiveCharacterTextSplitter` (500 chars, 50 overlap) |
| **Storage** | Embeds with `text-embedding-3-small`, stores in ChromaDB |
| **Retrieval** | Top-10 similarity search + structured all-units summary (with region, trades, and listing links) |
| **Output** | `gpt-4o-mini` generates an answer from retrieved context, with links to unit listings |

### App Flow

1. User logs in with password
2. Scraper fetches latest Place2Lease listings (cached per session)
3. Each unit is enriched with region info from `town_region.txt`
4. RAG pipeline ingests all documents and builds the vector store (cached per session)
5. Chatbot queries the RAG with both retrieved chunks and a structured all-units summary for complete coverage

## Data Sources

- **Place2Lease API** — live unit listings, details, and conditions
- **FAQ.txt** — Place2Lease frequently asked questions
- **e-Bidding Terms and Conditions.pdf** — e-bidding rules and requirements
- **town_region.txt** — town-to-region mapping for location-based queries
- **trade.txt** — trade-related reference data
