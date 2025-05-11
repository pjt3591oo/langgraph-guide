from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
import random # 평가 결과 시뮬레이션용

# 1. 상태 정의
class SelfCorrectionState(TypedDict):
    query: str
    generated_text: str
    evaluation_passed: bool
    # 반복 횟수 카운터 (operator.add 로 누적)
    iterations: Annotated[int, operator.add]

# 2. 노드 정의
def generate_text_node(state: SelfCorrectionState) -> dict:
    print(f"--- 노드: 텍스트 생성 (시도: {state['iterations'] + 1}) ---") # 다음 시도 횟수 표시
    query = state['query']
    # 실제로는 LLM 호출
    # 여기서는 길이를 랜덤하게 생성하여 시뮬레이션
    text_length = random.randint(5, 15)
    generated_text = f"'{query}'에 대한 {text_length} 단어 길이의 텍스트"
    print(f"생성된 텍스트: {generated_text}")
    return {"generated_text": generated_text, "iterations": 1} # 반복 횟수 1 증가

def evaluate_text_node(state: SelfCorrectionState) -> dict:
    print("--- 노드: 텍스트 평가 ---")
    generated_text = state['generated_text']
    # 실제로는 평가 로직 (LLM 호출 또는 규칙 기반)
    # 여기서는 텍스트 길이가 10 이상이면 통과로 간주
    passed = len(generated_text.split()) >= 12 # 단어 개수 기준 (예시)
    print(f"평가 결과: {'통과' if passed else '실패'}")
    return {"evaluation_passed": passed}

# 3. 조건 함수 정의 (순환 제어)
MAX_ITERATIONS = 3
def check_evaluation_and_iterations(state: SelfCorrectionState) -> str:
    """
    평가 결과와 반복 횟수를 확인하여 다음 단계를 결정.
    "finish" 또는 "regenerate" 반환.
    """
    print("--- 조건 평가: 평가 통과 및 최대 반복 도달 여부 ---")
    passed = state['evaluation_passed']
    iterations = state['iterations']
    print(f"평가 통과: {passed}, 현재 반복 횟수: {iterations}")

    if passed:
        print("결정: 평가 통과, 종료")
        return "finish"
    elif iterations >= MAX_ITERATIONS:
        print(f"결정: 최대 반복 ({MAX_ITERATIONS}) 도달, 종료")
        return "finish"
    else:
        print("결정: 평가 실패 및 재시도 가능, 재생성")
        return "regenerate"

# 4. 그래프 빌드
workflow = StateGraph(SelfCorrectionState)

# 노드 추가
workflow.add_node("generator", generate_text_node)
workflow.add_node("evaluator", evaluate_text_node)

# 진입점 설정
workflow.set_entry_point("generator")

# 엣지 추가
workflow.add_edge("generator", "evaluator") # 생성 후 평가

# 조건부 엣지 (순환 구현!)
workflow.add_conditional_edges(
    "evaluator", # 평가 노드 후에 조건 평가
    check_evaluation_and_iterations, # 사용할 조건 함수
    {
        "finish": END, # "finish" 반환 시 그래프 종료
        "regenerate": "generator" # "regenerate" 반환 시 generator 노드로 되돌아감! (순환)
    }
)

# 그래프 컴파일
app = workflow.compile()

# 5. 그래프 실행
print("--- 순환 그래프 실행 시작 ---")
initial_state = {"query": "LangGraph 순환 예제", "generated_text": "", "evaluation_passed": False, "iterations": 0}
final_state = app.invoke(initial_state)

print("\n--- 최종 상태 ---")
print(final_state)