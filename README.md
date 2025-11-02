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

## Running with Docker

Build the application image:

```bash
docker build -t skripsi-chat .
```

Run the container (exposes Streamlit on port 8501):

```bash
docker run --rm -p 8501:8501 --env-file .env skripsi-chat
```

Ensure your `.env` file includes the required `GOOGLE_API_KEY` and `ELASTICSEARCH_URL` values.

## Running with Docker Compose

Spin up both the Streamlit app and an Elasticsearch instance:

```bash
docker compose up --build
```

This expects a `.env` file in the project root that defines `GOOGLE_API_KEY`. The app container automatically points to the bundled Elasticsearch service at `http://elasticsearch:9200`.

When the services are running, visit `http://localhost:8501` to use the chat interface. To ingest data into Elasticsearch from within the containers:

```bash
docker compose run --rm app python ingest.py
```
