from typing import TypedDict, List, Union
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

load_dotenv()


class AgentState(TypedDict):
    messages: List[Union[HumanMessage, AIMessage]]

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

def process(state: AgentState) -> AgentState:
    response  = llm.invoke(state["messages"])
    state["messages"].append(AIMessage(content=response.content))
    print(f"AI Response: {response.content}")
    print("CURRENT STATE", state["messages"])
    return state
    
graph = StateGraph(AgentState)
graph.add_node("process", process)
graph.add_edge(START, "process")
graph.add_edge("process", END)
builder = graph.compile()


converstaional_history = []; 
user_input = input("Enter your question: ")

while user_input.lower() not in ["exit", "quit"]:
    converstaional_history.append(HumanMessage(content=user_input))
    result = builder.invoke({"messages": converstaional_history})
    converstaional_history = result["messages"]
    print("CONVERSATIONAL HISTORY", converstaional_history)
    user_input = input("Enter your question: ")

