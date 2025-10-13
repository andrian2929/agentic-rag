from typing import TypedDict, List
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

load_dotenv()


class AgentState(TypedDict):
    messages: List[HumanMessage]

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

def process(state: AgentState) -> AgentState:
    response  = llm.invoke(state["messages"])
    print(f"AI Response: {response.content}")
    return state

graph = StateGraph(AgentState)
graph.add_node("process", process)
graph.add_edge(START, "process")
graph.add_edge("process", END)

builder = graph.compile()

# save draw mermaid 
png_data = builder.get_graph().draw_mermaid_png()
with open("graph.png", "wb") as f:
    f.write(png_data)

user_input = input("Enter your question: ")
builder.invoke({"messages": [HumanMessage(content=user_input)]})