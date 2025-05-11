from typing import TypedDict, List, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph

# 상태 정의 (위 AdvancedRAGState 재사용)
class AdvancedRAGState(TypedDict):
    query: str
    documents: Annotated[List[str], operator.add]
    agent_scratchpad: Annotated[Sequence[BaseMessage], operator.add]
    final_answer: str
    search_needed: bool

# 메시지를 스크래치패드에 추가하는 노드
def add_message_node(state: AdvancedRAGState) -> dict:
    print("--- 노드: 메시지 추가 ---")
    # 실제로는 LLM 호출 결과 등이 될 수 있음
    new_message = AIMessage(content="새로운 AI 메시지입니다.")
    print(f"추가할 메시지: {new_message.content}")
    # 'agent_scratchpad' 키에 새 메시지 리스트를 반환 (operator.add 덕분에 누적됨)
    return {"agent_scratchpad": [new_message]}

# 그래프 설정
workflow = StateGraph(AdvancedRAGState)
workflow.add_node("message_adder", add_message_node)
workflow.set_entry_point("message_adder")
workflow.set_finish_point("message_adder") # 여기서는 간단히 한 노드만 실행

app = workflow.compile()

# 초기 상태 (query만 존재)
initial_state = {
    "query": "테스트 쿼리",
    "documents": [],
    "agent_scratchpad": [HumanMessage(content="사용자 질문입니다.")], # 초기 메시지
    "final_answer": "",
    "search_needed": True
}

print("--- 첫 번째 실행 ---")
state_after_first_run = app.invoke(initial_state)
print("\n--- 첫 번째 실행 후 상태 ---")
print(state_after_first_run['agent_scratchpad'])

print("\n--- 두 번째 실행 (첫 실행 결과를 입력으로) ---")
# 이전 상태를 그대로 다시 입력으로 넣어 두 번 실행되는 효과
state_after_second_run = app.invoke(state_after_first_run)
print("\n--- 두 번째 실행 후 상태 ---")
print(state_after_second_run['agent_scratchpad'])