from langgraph.graph import StateGraph, MessagesState, START
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

model = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    model_name="l3-8b-stheno-v3.1-iq-imatrix"
)

def call_model(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": response}


builder = StateGraph(MessagesState)
builder.add_node("call_model", call_model)
builder.add_edge(START, "call_model")

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "1"}}

input_message = {"type": "user", "content": "안녕, 나의 이름은 홍길동이야"}
for chunk in graph.stream({"messages": [input_message]}, config=config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()

input_message = {"type": "user", "content": "내 이름이 뭐야?"}
for chunk in graph.stream({"messages": [input_message]}, config=config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
