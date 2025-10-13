from typing import TypedDict, List, Union, Sequence, Annotated
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

load_dotenv()


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


@tool
def add(a: int, b: int) -> int:
    """This is a tool that adds two numbers."""
    return a + b

tools = [add]

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash").bind_tools(tools)

def model_call(state: AgentState) -> AgentState:
    response  = llm.invoke(state["messages"])
    print(f"AI Response: {response.content}")
    return state

def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1] 
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"


graph =  StateGraph(AgentState)
graph.add_node("model_call", model_call)
graph.add_node("tool", ToolNode(tools=tools))
graph.set_entry_point("model_call")
graph.add_conditional_edges("model_call", should_continue, {
    "continue": "tool",
    "end": END
})
graph.add_edge("tool", "model_call")
builder = graph.compile()

# save draw mermaid 
png_data = builder.get_graph().draw_mermaid_png()
with open("graph.png", "wb") as f:
    f.write(png_data)