from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from langchain_elasticsearch import ElasticsearchStore
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import (
    StructuredQueryOutputParser,
    get_query_constructor_prompt,
)
from langchain_community.query_constructors.elasticsearch import ElasticsearchTranslator

load_dotenv()


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
embedding = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


def retriver():
    vector_store = ElasticsearchStore(
        es_url="http://elasticsearch:9200",
        index_name="thesis-index",
        embedding=embedding,
    )

    examples = [
        (
            "Skripsi terbaru tentang algoritma CNN",
            {
                "query": "CNN",
                "filter": 'and(eq("tahun", 2025))',
            },
        ),
        (
            "Apa saja skripsi tentang deteksi judi online pada tahun 2023",
            {
                "query": "deteksi judi online",
                "filter": 'and(eq("tahun", 2023))',
            },
        ),
        (
            "Skripsi yang ditulis dengan nim 201401072 pada tahun 2025",
            {
                "query": "deteksi judi online",
                "filter": 'and(eq("nim", 201401072), eq("tahun", 2025))',
            },
        ),
        (
            "Skripsi yang ditulis oleh Difanie pada tahun 2023",
            {
                "query": "",
                "filter": 'and(contain("penulis", "difanie"), eq("tahun", 2023))',
            },
        ),
    ]
    metadata_field_info = [
        AttributeInfo(
            name="tahun",
            description="Tahun dokumen diterbitkan",
            type="integer",
        ),
        AttributeInfo(
            name="judul",
            description="Judul dari dokumen yang diterbitkan.",
            type="string",
        ),
        AttributeInfo(
            name="penulis",
            description="Nama penulis dokumen.",
            type="string",
        ),
        AttributeInfo(
            name="nim",
            description="Nomor Induk Mahasiswa (NIM) penulis dokumen.",
            type="string",
        ),
        AttributeInfo(
            name="program_studi",
            description="Program studi tempat penulis terdaftar.",
            type="string",
        ),
        AttributeInfo(
            name="jenis",
            description="Jenis dokumen (misalnya Skripsi Sarjana, Tesis, dll.).",
            type="string",
        ),
        AttributeInfo(
            name="uriIdentifier",
            description="URL untuk mengakses dokumen dalam repositori.",
            type="string",
        ),
    ]
    document_content_description = "Metadata skripsi"
    prompt = get_query_constructor_prompt(
        document_content_description,
        metadata_field_info,
        examples=examples,
    )
    output_parser = StructuredQueryOutputParser.from_components()
    query_constructor = prompt | llm | output_parser

    return SelfQueryRetriever(
        llm_chain=query_constructor,
        vectorstore=vector_store,
        structured_query_translator=ElasticsearchTranslator(),
    )
