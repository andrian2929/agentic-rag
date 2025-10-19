# Chat Repositori Skripsi USU

Chat assistant with agentic RAG that helps students explore skripsi from the Institutional Repository of Universitas Sumatera Utara.

- Conversational interface with chat threads
- Self-query retriever that translates natural language into structured Elasticsearch filters.
- Data ingestion pipeline that embeds thesis abstracts with Gemini embeddings and stores them in Elasticsearch.

## Prerequisites

- Docker
- Gemini API

## Environment variables

Create a `.env` file in the project root and provide the credentials expected by LangChain:

```
GOOGLE_API_KEY=your_api_key
ELASTICSEARCH_URL=http://elasticsearch:9200
```

## Setup
```bash
uv sync
```

## Ingesting data

Ensure Elasticsearch is running and the `data/translated-detail.json` file is available, then index the documents:

```bash
python ingest.py
```

## Running the chat app

```bash
streamlit run streamlit.py
```

Open the provided URL in your browser
