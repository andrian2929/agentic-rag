from llama_index.llms.gemini import Gemini
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.embeddings.gemini import GeminiEmbedding
from dotenv import load_dotenv

load_dotenv()

Settings.embed_model = GeminiEmbedding(model_name="models/embedding-001")
Settings.llm = Gemini(model="gemini-2.5-flash", temperature=0)


def main():

    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()
    response = query_engine.query("Bagaimana isi dari UUD 1945?")
    print(response)
    # llm = Gemini(model="gemini-2.5-flash", temperature=0)
    # response = llm.complete("Write a haiku about the sea.")
    # print(response)


if __name__ == "__main__":
    main()
