from typing import Annotated
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
from utils import retriver as SelfQueryRetriever
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()


class ChatState(TypedDict):
    messages: Annotated[list, add_messages]


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
embedding = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

retriever_tool = create_retriever_tool(
    SelfQueryRetriever(),
    "retrieve_document",
    "Cari dokumen skripsi dari repositori institusi USU.",
)


def generate_query_or_respond(state: MessagesState):
    """Call the model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or simply respond to the user.
    """
    response = llm.bind_tools(tools=[retriever_tool]).invoke(state["messages"])
    print("response:", response)
    return {"messages": [response]}


def generate_answer(state: MessagesState):
    """Generate an answer."""
    GENERATE_PROMPT = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question. "
        "If you don't know the answer, just say that you don't know. "
        "Use three sentences maximum and keep the answer concise.\n"
        "Question: {question} \n"
        "Context: {context}"
    )
    question = state["messages"][0].content
    context = state["messages"][-1]
    print(state["messages"])
    prompt = GENERATE_PROMPT.format(question=question, context=context)

    response = llm.invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}


workflow = StateGraph(MessagesState)
workflow.add_node("generate_query_or_respond", generate_query_or_respond)
workflow.add_node("retrieve", ToolNode([retriever_tool]))
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

graph = workflow.compile()

png_data = graph.get_graph().draw_mermaid_png()
with open("graph2.png", "wb") as f:
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

# while True:
#     try:
#         user_input = input("User: ")
#         if user_input.lower() in ["quit", "exit", "q"]:
#             print("Goodbye!")
#             break
#         events = graph.stream(
#             {"messages": [{"role": "user", "content": user_input}]},
#             config,
#             stream_mode="values",
#         )
#         for event in events:
#             event["messages"][-1].pretty_print()
#         print(list(graph.get_state_history(config)))
#     except:
#         # fallback if input() is not available
#         user_input = "What do you know about LangGraph?"
#         print("User: " + user_input)
#         graph.invoke({"messages": [{"role": "user", "content": user_input}]})
#         break

if __name__ == "__main__":
    graph.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Carilah skripsi yang ditulis oleh difanie",
                }
            ]
        }
    )
