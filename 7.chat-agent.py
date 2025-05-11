from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END

from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    model_name="l3-8b-stheno-v3.1-iq-imatrix"
)


@tool
def get_weather(query: str) -> list:
    """Search weatherapi to get the current weather"""
    print('>>>>>> get_weather <<<<<<<')

    if query:
        return f"It will rain in {query} today"
    else:
        return "Weather Data Not Found"

@tool
def search_web(query: str) -> list:
    """Search the web for a query"""
    results = "search results"
    print('>>>>>> search_web <<<<<<<')
    return results

tools = [search_web, get_weather]
tool_node = ToolNode(tools)

llm_with_tools = llm.bind_tools(tools)

# res = llm_with_tools.invoke(
#     [
#         {"role": "user", "content": "Will it rain in Seoul today?"}
#     ]
# )

# print(res)

# define functions to call the LLM or the tools
def call_model(state: MessagesState):
    messages = state["messages"]
    print('>>>>>> call_model <<<<<<<')
    print(messages)
    response = llm_with_tools.invoke(messages)
    print('>>>>>> response <<<<<<<')
    print(response)
    return {"messages": [response]}

def call_tools(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

# initialize the workflow from StateGraph
workflow = StateGraph(MessagesState)

# add a node named LLM, with call_model function. This node uses an LLM to make decisions based on the input given
workflow.add_node("LLM", call_model)

# Our workflow starts with the LLM node
workflow.add_edge(START, "LLM")

# Add a tools node
workflow.add_node("tools", tool_node)

# Add a conditional edge from LLM to call_tools function. It can go tools node or end depending on the output of the LLM. 
workflow.add_conditional_edges("LLM", call_tools)

# tools node sends the information back to the LLM
workflow.add_edge("tools", "LLM")

agent = workflow.compile()
# display(Image(agent.get_graph().draw_mermaid_png()))

print(' chat with weather tool--------------------------------')
for chunk in agent.stream( {"messages": [("user", "Will it rain in Seoul today?")]}, stream_mode="values",):
    chunk["messages"][-1].pretty_print()

print(' chat with web search tool--------------------------------')
for chunk in agent.stream( {"messages": [("user", "what is Google?")]}, stream_mode="values",):
    chunk["messages"][-1].pretty_print()

