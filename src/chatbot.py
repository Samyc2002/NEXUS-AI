from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from langchain.chat_models import init_chat_model

from langchain_tavily import TavilySearch

load_dotenv()

llm = init_chat_model("google_genai:gemini-2.0-flash")


class State(TypedDict):
    messages: Annotated[list, add_messages]


nexus_builder = StateGraph(State)

tool = TavilySearch(max_results=2)
tools = [tool]
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


nexus_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=[tool])
nexus_builder.add_node("tools", tool_node)


nexus_builder.add_conditional_edges(
    "chatbot",
    tools_condition
)

nexus_builder.add_edge(START, "chatbot")
nexus_builder.add_edge("tools", "chatbot")


def should_end(state: State):
    last = state["messages"][-1]
    if isinstance(last, dict) and "tool_calls" in last and last["tool_calls"]:
        return "tools"
    return END


nexus_builder.add_conditional_edges("chatbot", should_end)
nexus_builder.set_entry_point("chatbot")
memory = MemorySaver()
nexus = nexus_builder.compile(checkpointer=memory)
