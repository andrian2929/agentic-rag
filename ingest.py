import json
from langchain.schema import Document
from pathlib import Path
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from dotenv import load_dotenv

load_dotenv()

def load_data():
    """Load data from a JSON file"""
    file_path = Path("data/translated-detail.json")
    if not file_path.exists():
        raise FileNotFoundError(f"The file does not exist.")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    docs: List[Document] = [
        Document(
            page_content=item["abstract"],
            metadata={
                "penulis": item["author"][0].get("name", "") if item["author"] else "",
                "nim": item["author"][0].get("nim", "") if item["author"] else "",
                "tahun": item["yearIssued"],
                "judul": item["title"],
                "program_studi": item["studyProgram"],
                "jenis": item["type"],
                "uriIdentifier": item["uriIdentifier"],
            },
        )
        for item in data
    ]
    return docs

def ingest():
    documents = load_data()
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    elastic_vector_search = ElasticsearchStore(
        es_url="http://elasticsearch:9200", index_name="thesis-index", embedding=embeddings
    )
    elastic_vector_search.add_documents(documents)
    print("Data ingested successfully.")


if __name__ == "__main__":
    ingest()
