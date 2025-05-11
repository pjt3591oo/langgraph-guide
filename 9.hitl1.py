from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver # Checkpointer (선택 사항이지만 HITL에 유용)
from typing import TypedDict, Annotated, Union
import operator
import uuid # 고유한 스레드 ID 생성을 위해

# 1. 상태 정의
class GraphState(TypedDict):
    original_query: str
    suggestion: str
    human_verdict: Union[str, None] # "approved", "rejected", 또는 None (초기값)
    final_result: str

# 2. 노드 함수 정의
def generate_suggestion(state: GraphState) -> dict:
    print("---AI가 제안 생성 중---")
    query = state["original_query"]
    # 실제 LLM 호출 대신 간단한 로직 사용
    suggestion = f"'{query}'에 대한 제안: '간단한 계획을 실행하세요.'"
    print(f"생성된 제안: {suggestion}")
    return {"suggestion": suggestion, "human_verdict": None} # human_verdict 초기화

def human_approval_node(state: GraphState) -> dict:
    print("---인간의 승인 대기 중---")
    # 이 노드는 interrupt_before에 의해 실행 전에 멈추므로,
    # 이 노드 자체의 로직은 중요하지 않을 수 있습니다.
    # 주된 역할은 인터럽트 포인트가 되는 것입니다.
    return {}

def process_approved(state: GraphState) -> dict:
    print("---제안이 승인됨---")
    return {"final_result": f"최종 결과 (승인됨): {state['suggestion']}"}

def process_rejected(state: GraphState) -> dict:
    print("---제안이 거부됨---")
    return {"final_result": "최종 결과: 제안이 사용자에 의해 거부되었습니다."}

def decide_next_step(state: GraphState) -> str:
    print("---다음 단계 결정 중---")
    if state.get("human_verdict") == "approved":
        print("경로: 승인됨")
        return "approved_branch"
    elif state.get("human_verdict") == "rejected":
        print("경로: 거부됨")
        return "rejected_branch"
    else:
        print("경로: 결정되지 않음 (오류 가능성)")
        return END # 또는 오류 처리 노드로


workflow = StateGraph(GraphState)

workflow.add_node("generator", generate_suggestion)
workflow.add_node("human_approval", human_approval_node) # 인터럽트 대상 노드
workflow.add_node("approved_action", process_approved)
workflow.add_node("rejected_action", process_rejected)

workflow.set_entry_point("generator")
workflow.add_edge("generator", "human_approval")

# human_approval 노드 이후, 사용자의 결정에 따라 분기
workflow.add_conditional_edges(
    "human_approval", # 이 노드 *이후* (실제로는 인터럽트 후 상태 업데이트를 통해) 결정
    decide_next_step,
    {
        "approved_branch": "approved_action",
        "rejected_branch": "rejected_action",
    }
)

workflow.add_edge("approved_action", END)
workflow.add_edge("rejected_action", END)

memory_saver = MemorySaver()

app = workflow.compile(
    checkpointer=memory_saver,
    interrupt_before=["human_approval"] # 'human_approval' 노드 실행 *전에* 인터럽트
)

if __name__ == "__main__":
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_input = {"original_query": "새로운 마케팅 캠페인 아이디어가 필요해"}
    
    print(f"스레드 ID: {thread_id} 로 실행 시작")
    print(f"초기 입력: {initial_input}")

    current_state_after_interrupt = app.invoke(initial_input, config)

    print("\n---인간의 개입 필요---")
    print(f"현재 상태: {current_state_after_interrupt}")
    
    if current_state_after_interrupt and "suggestion" in current_state_after_interrupt:
        print(f"AI의 제안: {current_state_after_interrupt['suggestion']}")
        
        user_decision = ""
        while user_decision.lower() not in ["approved", "rejected"]:
            user_decision = input("이 제안을 승인하시겠습니까? (approved/rejected): ").strip().lower()

        update_with_human_feedback = {"human_verdict": user_decision}
        app.update_state(config, update_with_human_feedback)
        
        print(f"\n사용자 결정 '{user_decision}'으로 그래프 재개...")
        final_output = app.invoke(None, config) 

        print("\n---최종 실행 결과---")
        print(final_output.get("final_result", "결과 없음"))

    else:
        print("오류: 제안이 생성되지 않았거나 상태가 올바르지 않습니다.")

    print(f"\n스레드 ID {thread_id}의 최종 상태 스냅샷:")
    final_snapshot = app.get_state(config)
    print(final_snapshot)