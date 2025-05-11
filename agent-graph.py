import operator
from typing import Annotated, Literal

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    # The operator.add reducer fn makes this append-only
    aggregate: Annotated[list, operator.add]


def host(state: State):
    print(f'Node A sees {state["aggregate"]}')
    return {"aggregate": ["host"]}


def tool(state: State):
    print(f'Node B sees {state["aggregate"]}')
    return {"aggregate": ["tool"]}


# Define nodes
builder = StateGraph(State)
builder.add_node(host)
builder.add_node(tool)


# Define edges
def route(state: State) -> Literal["tool", END]:
    if len(state["aggregate"]) < 7:
        return "tool"
    else:
        return END


builder.add_edge(START, "host")
builder.add_conditional_edges("host", route)
builder.add_edge("tool", "host")
graph = builder.compile()

print(graph.get_graph().print_ascii())
mermaid_code = graph.get_graph().draw_mermaid()

with open("graph_mermaid.md", "w") as f:
    f.write(mermaid_code)
