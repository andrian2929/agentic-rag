from typing import Annotated, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_community.query_constructors.elasticsearch import ElasticsearchTranslator
from langchain.tools.retriever import create_retriever_tool
from langgraph.graph import MessagesState
from utils import retriver
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, ToolCall
from langchain_core.tools import tool
from langchain.schema import Document

load_dotenv()


class ChatState(TypedDict):
    messages: Annotated[list, add_messages]


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, tags=["chat"])
embedding = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


@tool("document_retriever", parse_docstring=True)
def retrieve_documents(query: str) -> List[Document]:
    """Mengambil dokumen dari repositori institusi USU berdarkan query yang diberikan.

    Args:
        query: Pertanyaan lengkap dari user.
    """
    results = retriver().invoke(query)
    return results


tools = [retrieve_documents]
tool_node = ToolNode(tools)


def generate_query_or_respond(state: MessagesState):
    """Call the model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or simply respond to the user.
    """
    print("CURRENT STATE", state["messages"])
    response = llm.bind_tools(tools).invoke(state["messages"])
    return {"messages": [response]}


def generate_answer(state: MessagesState):
    """Generate an answer."""
    GENERATE_PROMPT = (
        "Kamu adalah asisten dari perpustakaan universitas sumatera utara untuk menjawab pertanyaan seputar skripsi mahasiswa "
        "Untuk menjawab pertanyaannya. Gunakan data dibawah ini supaya kamu bisa memberikan jawaban yang tepat dan relevan. "
        "Jika kamu tidak tahu jawabannya, cukup katakan bahwa kamu tidak tahu. "
        "Pertanyaan: {question} \n"
        "Data: {context}"
    )

    messages = state["messages"]
    question = messages[-3].content
    last_message = messages[-1]
    docs = last_message.content

    prompt = GENERATE_PROMPT.format(question=question, context=docs)
    response = llm.invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}


workflow = StateGraph(MessagesState)
workflow.add_node("generate_query_or_respond", generate_query_or_respond)
workflow.add_node("retrieve", tool_node)
workflow.add_node("generate_answer", generate_answer)

workflow.add_edge(START, "generate_query_or_respond")
workflow.add_conditional_edges(
    "generate_query_or_respond",
    tools_condition,
    {
        "tools": "retrieve",
        END: END,
    },
)
workflow.add_edge("retrieve", "generate_answer")
workflow.add_edge("generate_answer", END)

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "abc123"}}


png_data = graph.get_graph().draw_mermaid_png()

# 2. Define a filename
file_name = "my_chat_graph.png"

# 3. Write the bytes to a file in 'write binary' ('wb') mode
with open(file_name, "wb") as f:
    f.write(png_data)


# def generate(state: State):
#     return {"messages": [llm.invoke(state["messages"])]}


# graph_builder = StateGraph(State)
# graph_builder.add_node("chatbot", chatbot)
# graph_builder.add_edge(START, "chatbot")
# graph_builder.add_edge("chatbot", END)

# checkpointer = InMemorySaver()
# graph = graph_builder.compile(checkpointer=checkpointer)

# config = {"configurable": {"thread_id": "1"}}

if __name__ == "__main__":
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            events = graph.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                config,
                stream_mode="values",
            )
            for event in events:
                print(event)
                if isinstance(event["messages"][-1], AIMessage):
                    event["messages"][-1].pretty_print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
