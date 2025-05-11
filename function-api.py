from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

model = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    model_name="l3-8b-stheno-v3.1-iq-imatrix"
)

@task
def call_model(messages: list[AnyMessage]):
    response = model.invoke(messages)
    return response

checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def workflow(inputs: list[AnyMessage], *, previous: list[AnyMessage]):
    if previous:
        inputs = add_messages(previous, inputs)

    response = call_model(inputs).result()
    return entrypoint.final(value=response, save=add_messages(inputs, response))

config = {
    "configurable": {
        "thread_id": "1"
    }
}

for chunk in workflow.stream(
    [{"role": "user", "content": "hi! I'm bob"}],
    config,
    stream_mode="values",
):
    chunk.pretty_print()

for chunk in workflow.stream(
    [{"role": "user", "content": "what's my name?"}],
    config,
    stream_mode="values",
):
    chunk.pretty_print()