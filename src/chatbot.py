import os
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from langchain.chat_models import init_chat_model

from langchain_tavily import TavilySearch

from tools import custom_tools

llm = init_chat_model("google_genai:gemini-2.0-flash")


class State(TypedDict):
    messages: Annotated[list, add_messages]


nexus_builder = StateGraph(State)

tools = [*custom_tools, TavilySearch(max_results=2)]
llm_with_tools = llm.bind_tools(tools)


system_message = {
    "role": "system",
    "content": (
        f"You are {os.environ.get('name')}, a helpful and intelligent voice assistant. "
        "You speak with a friendly, slightly witty tone, and always try to be concise and clear. "
        "You help the user with information, daily tasks, and fun facts."
    )
}


def chatbot(state: State):
    """
    The `chatbot` function takes a `State` object as input and returns a dictionary with a list of
    messages processed by the `llm_with_tools` tool.

    :param state: The `state` parameter in the `chatbot` function likely represents the current state of
    the chatbot, which may include information such as previous messages, user input, or any other
    relevant data needed for the chatbot to process and respond to user interactions
    :type state: State
    :return: A dictionary is being returned with a key "messages" containing a list of messages
    generated by invoking the llm_with_tools function on the messages stored in the state.
    """
    state_with_personality = {
        "messages": [system_message] + state["messages"]
    }
    return {"messages": [llm_with_tools.invoke(state_with_personality["messages"])]}


nexus_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
nexus_builder.add_node("tools", tool_node)


nexus_builder.add_conditional_edges(
    "chatbot",
    tools_condition
)

nexus_builder.add_edge(START, "chatbot")
nexus_builder.add_edge("tools", "chatbot")


def should_end(state: State):
    """
    The function `should_end` checks if the last message in the state contains tool calls and returns
    "tools" if it does, otherwise it returns END.

    :param state: The `state` parameter is expected to be a dictionary containing information about the
    current state of the program or application. In this context, it seems to have a key "messages"
    which is a list of messages. The function `should_end` checks the last message in the list and if it
    is
    :type state: State
    :return: "tools" if the last message in the state is a dictionary with a key "tool_calls" that is
    not empty. Otherwise, it is returning the variable END.
    """
    last = state["messages"][-1]
    if isinstance(last, dict) and "tool_calls" in last and last["tool_calls"]:
        return "tools"
    return END


nexus_builder.add_conditional_edges("chatbot", should_end)
nexus_builder.set_entry_point("chatbot")
memory = MemorySaver()
nexus = nexus_builder.compile(checkpointer=memory)
