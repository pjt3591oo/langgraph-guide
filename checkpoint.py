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

config1 = {"configurable": {"thread_id": "1"}}
config2 = {"configurable": {"thread_id": "2"}}

input_message = {"type": "user", "content": "안녕, 나의 이름은 홍길동이야"}
for chunk in graph.stream({"messages": [input_message]}, config=config1, stream_mode="values"):
    chunk["messages"][-1].pretty_print()

input_message = {"type": "user", "content": "내 이름이 뭐야?"}
for chunk in graph.stream({"messages": [input_message]}, config=config1, stream_mode="values"):
    chunk["messages"][-1].pretty_print()


input_message = {"type": "user", "content": "안녕, 나의 이름은 박정태야"}
for chunk in graph.stream({"messages": [input_message]}, config=config2, stream_mode="values"):
    chunk["messages"][-1].pretty_print()

# state 가져오기
print(graph.get_state(config1))
print()
print(graph.get_state(config2))

# state 복구
graph.update_state(config1, graph.get_state(config1))

input_message = {"type": "user", "content": "내 이름이 뭐야?"}
for chunk in graph.stream({"messages": [input_message]}, config=config1, stream_mode="values"):
    chunk["messages"][-1].pretty_print()

def analyze_state_changes(config):
    history = list(graph.get_state_history(config))
    for i, checkpoint in enumerate(history):
        print(f"Checkpoint {i}:")
        print(f"  Time: {checkpoint.created_at}")
        print(f"  State: {checkpoint.values}")

analyze_state_changes(config1)