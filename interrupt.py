from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver


class State(TypedDict):
    input: str


def step_1(state):
    print("---Step 1---")
    print(state)
    return {}


def step_2(state):
    print("---Step 2---")
    print(state)
    return {}


def step_3(state):
    print("---Step 3---")
    print(state)
    return {}


builder = StateGraph(State)
builder.add_node("step_1", step_1)
builder.add_node("step_2", step_2)
builder.add_node("step_3", step_3)

builder.add_edge(START, "step_1")
builder.add_edge("step_1", "step_2")
builder.add_edge("step_2", "step_3")
builder.add_edge("step_3", END)

memory = MemorySaver()

graph = builder.compile(checkpointer=memory, interrupt_before=['step_2'])

# 초기 상태 설정
initial_state = {"input": "Hello"}
config = {"configurable": {"thread_id": "1"}}

# 그래프 실행
for chunk in graph.invoke(initial_state, config):
    print(chunk)
    initial_state = graph.get_state(config)
    graph.update_state(config, {"input": "안녕~ 수정했어!"})

print('====')

# interrupt로 실행할 땐 초기 상태가 없어야 됨
for chunk in graph.invoke(None, config):
    print(chunk)


