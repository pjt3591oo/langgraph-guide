from typing import TypedDict, Annotated, Optional
import operator
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, AIMessage # 메시지 타입

# 1. 상태 정의 (HITL 관련 필드 추가)
class ContentApprovalState(TypedDict):
    topic: str
    draft_content: str
    # waiting_for_human: 사용자가 검토/승인해야 하는지 여부
    waiting_for_human: bool
    # human_feedback: 사용자의 피드백 또는 승인 여부 (Optional)
    human_feedback: Optional[str]
    final_content: Optional[str] # 최종 발행될 콘텐츠

# 2. 노드 정의
def draft_generator_node(state: ContentApprovalState) -> dict:
    print("--- 노드: 초안 생성 ---")
    topic = state['topic']
    # 실제로는 LLM 호출
    draft = f"'{topic}'에 대한 AI 생성 블로그 초안입니다. 내용은..."
    print(f"생성된 초안: {draft[:50]}...")
    # 초안 생성 후 사람의 승인이 필요하므로 waiting_for_human을 True로 설정
    return {"draft_content": draft, "waiting_for_human": True, "human_feedback": None}

def finalyze_content_node(state: ContentApprovalState) -> dict:
    print("--- 노드: 콘텐츠 최종화 ---")
    feedback = state.get('human_feedback', '승인됨') # 피드백 없으면 승인으로 간주
    if "수정" in feedback: # 간단한 피드백 처리 예시
        # 실제로는 피드백 기반으로 LLM이 수정
        final_content = state['draft_content'] + f"\n\n[수정됨: {feedback}]"
        print("피드백 반영하여 콘텐츠 수정")
    else:
        final_content = state['draft_content']
        print("콘텐츠 승인됨")
    return {"final_content": final_content}

# 3. 조건 함수 정의
def check_human_approval(state: ContentApprovalState) -> str:
    """ waiting_for_human 플래그를 확인하여 진행 또는 종료 결정 """
    print("--- 조건 평가: 사람의 개입 필요 여부 ---")
    if state.get('waiting_for_human', False):
        print("결정: 사람의 승인 대기, 그래프 중단")
        return END # 사람 입력 대기를 위해 일단 종료
    else:
        print("결정: 사람의 승인 완료 (또는 불필요), 최종화 진행")
        return "finalize" # 다음 단계 노드 이름

# 4. 그래프 빌드
workflow = StateGraph(ContentApprovalState)

workflow.add_node("generator", draft_generator_node)
workflow.add_node("finalyzer", finalyze_content_node)

workflow.set_entry_point("generator")

# 조건부 엣지: generator 노드 후에 사람 승인 여부 체크
workflow.add_conditional_edges(
    "generator",
    check_human_approval,
    # 매핑: "finalize" 문자열을 반환하면 "finalyzer" 노드로 이동
    {
        "finalize": "finalyzer",
        END: END
    }
)

# 최종화 노드 후 종료
workflow.add_edge("finalyzer", END)

# 그래프 컴파일
approval_app = workflow.compile()

print(approval_app.get_graph().print_ascii())

# 5. 외부 애플리케이션 로직 (HITL 처리)
def run_with_human_in_loop(app, initial_state):
    print("\n--- 워크플로우 시작 ---")
    current_state = initial_state

    while True:
        print(f"\n--- LangGraph 실행 (현재 상태: { {k:v for k,v in current_state.items() if k != 'draft_content'} }) ---")
        # 상태를 가지고 그래프 실행 (stream 또는 invoke)
        # 여기서는 간단히 invoke 사용
        output_state = app.invoke(current_state, {"recursion_limit": 5})

        # 그래프 실행 후 상태 업데이트
        current_state.update(output_state) # 최신 상태 반영

        print(f"--- LangGraph 실행 완료 (업데이트된 상태: { {k:v for k,v in current_state.items() if k != 'draft_content'} }) ---")

        # 사람의 개입이 필요한지 확인
        if current_state.get("waiting_for_human", False):
            print("\n--- 사람의 개입 필요 ---")
            print(f"생성된 초안:\n{current_state['draft_content']}")
            feedback = input("초안을 승인하시겠습니까? (승인 시 Enter, 수정 필요 시 내용 입력): ")

            # 사용자 입력을 상태에 반영하고 대기 플래그 해제
            current_state["human_feedback"] = feedback if feedback else "승인"
            current_state["waiting_for_human"] = False
            # 이제 업데이트된 상태로 다음 루프에서 그래프를 다시 실행
        else:
            # 더 이상 사람의 개입이 필요 없으면 루프 종료
            print("\n--- 워크플로우 완료 ---")
            break

        print('')
        print('')
        print('')
        print('')
    return current_state

# 실행
initial_state = {"topic": "LangGraph HITL 예제", "draft_content": "", "waiting_for_human": False, "human_feedback": None, "final_content": None}
final_result_state = run_with_human_in_loop(approval_app, initial_state)

print("\n--- 최종 결과 ---")
print(f"최종 콘텐츠:\n{final_result_state.get('final_content')}")