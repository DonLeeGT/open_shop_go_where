import os
import json
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from scraper import TOWN_REGION

RESOURCES_DIR = "resources"
CHROMA_DIR = "./chroma_langchain_db"
COLLECTION_NAME = "place2lease_rag"

DOCUMENT_SOURCES = [
    os.path.join(RESOURCES_DIR, "FAQ.txt"),
    os.path.join(RESOURCES_DIR, "e-Bidding Terms and Conditions.pdf"),
    os.path.join(RESOURCES_DIR, "place2lease_corpus.txt"),
    os.path.join(RESOURCES_DIR, "town_region.txt"),
]

UNIT_LINK_BASE = "https://place2lease.hdb.gov.sg/public/view-properties/true/unit-details"

SYSTEM_PROMPT = """You are a helpful assistant for HDB Place2Lease, Singapore's portal for leasing HDB commercial properties.
Use the following context to answer the question. If you don't know the answer, say so — don't make things up.
Use the town_region.txt to answer location-related questions.
Keep your answer concise and relevant.
When mentioning specific units, always append a markdown link ([View listing](url)) using the unit's URL provided in the context.
Note: "Open Trade" means the unit can be used for any trade. When answering questions about businesses or trades, pay attention to each unit's Allowed Trades and Excluded Trades.

Context:
```
{context}
```

Question: {input}
"""


# ── Step 1: Document Loading ──

def load_txt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def load_pdf(filepath):
    reader = PdfReader(filepath)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def load_all_documents():
    docs = []
    for path in DOCUMENT_SOURCES:
        filename = os.path.basename(path)
        if path.endswith(".pdf"):
            text = load_pdf(path)
        else:
            text = load_txt(path)
        docs.append({"source": filename, "text": text})
        print(f"  Loaded {filename} ({len(text)} chars)")
    return docs


# ── Step 2: Splitting & Chunking ──

def split_documents(docs, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " ", ""],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    all_chunks = []
    all_metadatas = []
    for doc in docs:
        chunks = splitter.split_text(doc["text"])
        metadatas = [{"source": doc["source"]} for _ in chunks]
        all_chunks.extend(chunks)
        all_metadatas.extend(metadatas)
    print(f"  Split into {len(all_chunks)} chunks")
    return all_chunks, all_metadatas


# ── Step 3: Storage (Embedding & Vector Store) ──

def create_vector_store(chunks, metadatas):
    embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")

    existing = Chroma(COLLECTION_NAME, persist_directory=CHROMA_DIR, embedding_function=embeddings_model)
    if existing._collection.count() > 0:
        existing.delete_collection()

    vector_store = Chroma.from_texts(
        collection_name=COLLECTION_NAME,
        texts=chunks,
        metadatas=metadatas,
        embedding=embeddings_model,
        persist_directory=CHROMA_DIR,
    )
    print(f"  Stored {vector_store._collection.count()} vectors in Chroma")
    return vector_store


def get_vector_store():
    embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings_model,
    )


# ── Step 4: Retrieval ──

def retrieve(vector_store, query, k=10):
    return vector_store.similarity_search(query, k=k)


# ── Step 5: Output (LLM Generation) ──

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def build_units_summary(units):
    """Build a compact summary of all units with region info for aggregation queries."""
    lines = []
    for unit in units:
        d = unit["unit_details"]
        town = d.get("HDB Town", "Unknown")
        region = TOWN_REGION.get(town, "Unknown")
        unit_id = d.get("Unit ID", "")
        link = f"{UNIT_LINK_BASE}/{unit_id}" if unit_id else ""
        trades = d.get("Allowed Trades", [])
        if isinstance(trades, list):
            trades = ", ".join(trades) if trades else "N/A"
        lines.append(
            f"- {d.get('Address')} | Town: {town} | Region: {region} "
            f"| Type: {d.get('Property Type')} | Area: {d.get('Floor Area (sqm)')} sqm "
            f"| Trades: {trades} | Link: {link}"
        )
    return "\n".join(lines)


def ask(vector_store, question, model="gpt-4o-mini", units=None):
    retrieved = retrieve(vector_store, question)
    context = format_docs(retrieved)

    if units:
        units_summary = build_units_summary(units)
        context = (
            f"=== All Available Units ===\n{units_summary}\n\n"
            f"=== Additional Context ===\n{context}"
        )

    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
    llm = ChatOpenAI(model=model)

    formatted = prompt.format(context=context, input=question)
    response = llm.invoke(formatted)

    return response.content, retrieved


# ── Full Pipeline: Build from scratch ──

def build_rag_pipeline():
    print("Step 1: Loading documents...")
    docs = load_all_documents()

    print("Step 2: Splitting & chunking...")
    chunks, metadatas = split_documents(docs)

    print("Step 3: Embedding & storing in vector store...")
    vector_store = create_vector_store(chunks, metadatas)

    print("RAG pipeline ready.")
    return vector_store
