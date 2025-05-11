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

class ConditionalMemorySaver(MemorySaver):
    def __init__(self, condition_func):
        super().__init__()
        self.condition_func = condition_func

    def put(self, config, metadata, values):
        if self.condition_func(values):
            super().put(config, metadata, values)

def should_checkpoint(state):
    # 예: 중요한 변경사항이 있을 때만 체크포인트 생성
    return len(state['messages']) % 2 == 0  # 5개 메시지마다 체크포인트

condition_memory = ConditionalMemorySaver(should_checkpoint)
graph = builder.compile(checkpointer=condition_memory)

config1 = {"configurable": {"thread_id": "1"}}

input_message = {"type": "user", "content": "안녕, 나의 이름은 홍길동이야"}
for chunk in graph.stream({"messages": [input_message]}, config=config1, stream_mode="values"):
    chunk["messages"][-1].pretty_print()

input_message = {"type": "user", "content": "내 이름이 뭐야?"}
for chunk in graph.stream({"messages": [input_message]}, config=config1, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
