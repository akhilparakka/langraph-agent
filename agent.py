# chatbot.py
import os
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from tools import tools, BasicToolNode
from dotenv import load_dotenv

load_dotenv()

grok_token = os.getenv("GROQ_API_KEY")
if not grok_token:
    raise ValueError("GROQ_API_KEY not found in environment variables")


class State(TypedDict):
    messages: Annotated[list, add_messages]


memory = MemorySaver()

graph_builder = StateGraph(State)

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=grok_token,
    temperature=0,
)

llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


tool_node = BasicToolNode(tools)


def route_tools(state: State):
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END


graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges(
    "chatbot", route_tools, {"tools": "tools", END: END}
)
graph_builder.add_edge("tools", "chatbot")
graph = graph_builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "1"}}


def process_chat(user_input: str) -> str:
    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values",
    )
    response = ""
    for event in events:
        response = event["messages"][-1].content
    return response
