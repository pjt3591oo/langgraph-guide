from typing import TypedDict, List, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, END # END 임포트
import matplotlib.pyplot as plt

# 1. 상태 정의 (문서 개수를 쉽게 확인하도록 documents 필드 유지)
class ConditionalRAGState(TypedDict):
    query: str
    documents: List[str]
    answer: str
    needs_clarification: bool # 사용자 요청 필요 여부 플래그

# 2. 노드 정의
def search_node(state: ConditionalRAGState) -> dict:
    print("--- 노드: 문서 검색 ---")
    query = state['query']
    # 예시: 쿼리 길이에 따라 검색 결과 개수 조절 (실제로는 검색 결과에 따라 달라짐)
    if len(query) < 10:
        documents = ["짧은 쿼리에 대한 문서 1"]
    else:
        documents = ["긴 쿼리에 대한 문서 1", "긴 쿼리에 대한 문서 2", "긴 쿼리에 대한 문서 3"]
    print(f"검색된 문서 개수: {len(documents)}")
    return {"documents": documents}

def generate_answer_node(state: ConditionalRAGState) -> dict:
    print("--- 노드: 답변 생성 ---")
    documents = state['documents']
    answer = f"'{state['query']}'에 대해 {len(documents)}개의 문서를 바탕으로 생성된 답변입니다."
    print(f"생성된 답변: {answer}")
    return {"answer": answer}

def request_clarification_node(state: ConditionalRAGState) -> dict:
    print("--- 노드: 사용자에게 추가 정보 요청 ---")
    # 실제로는 사용자에게 되묻는 로직 구현
    print("검색된 문서가 부족합니다. 질문을 더 구체적으로 해주시겠어요?")
    return {"needs_clarification": True} # 상태 플래그 설정

# 3. 조건 함수 정의
def check_document_sufficiency(state: ConditionalRAGState) -> str:
    """
    검색된 문서 개수를 확인하여 다음 단계를 결정하는 함수.
    문자열 "generate" 또는 "clarify" 를 반환합니다.
    """
    print("--- 조건 평가: 문서 충분한가? ---")
    document_count = len(state['documents'])
    print(f"현재 문서 개수: {document_count}")
    if document_count >= 2:
        print("결정: 답변 생성으로 이동")
        return "generate" # 엣지 매핑의 키
    else:
        print("결정: 추가 정보 요청으로 이동")
        return "clarify" # 엣지 매핑의 키

# 4. 그래프 빌드
workflow = StateGraph(ConditionalRAGState)

# 노드 추가
workflow.add_node("search", search_node)
workflow.add_node("generate_answer", generate_answer_node)
workflow.add_node("request_clarification", request_clarification_node)

# 진입점 설정
workflow.set_entry_point("search")

# 조건부 엣지 추가!
workflow.add_conditional_edges(
    "search", # search 노드 실행 후 조건을 평가
    check_document_sufficiency, # 사용할 조건 함수
    {
        # 조건 함수가 "generate"를 반환하면 -> generate_answer 노드로 이동
        "generate": "generate_answer",
        # 조건 함수가 "clarify"를 반환하면 -> request_clarification 노드로 이동
        "clarify": "request_clarification"
    }
)

# 일반 엣지 (워크플로우 종료 설정)
workflow.add_edge("generate_answer", END) # 답변 생성 후 종료
workflow.add_edge("request_clarification", END) # 추가 정보 요청 후 종료 (실제로는 다시 입력 받거나 다른 처리 가능)

# 그래프 컴파일
app = workflow.compile()

mermaid_code = app.get_graph().draw_mermaid()
with open("graph_mermaid.md", "w") as f:
    f.write(mermaid_code)
print(f"Mermaid 코드가 'graph_mermaid.md' 파일로 저장되었습니다.")
print("이 코드를 https://mermaid.live/ 사이트에 붙여넣어 시각화할 수 있습니다.")

# 5. 그래프 실행 테스트

print("--- 테스트 1: 짧은 쿼리 (문서 부족 예상) ---")
initial_state_short = {"query": "안녕?", "documents": [], "answer": "", "needs_clarification": False}
final_state_short = app.invoke(initial_state_short)
print("\n--- 최종 상태 (짧은 쿼리) ---")
print(final_state_short)

print("\n" + "="*30 + "\n")

print("--- 테스트 2: 긴 쿼리 (문서 충분 예상) ---")
initial_state_long = {"query": "LangGraph 조건부 엣지 사용법 알려줘", "documents": [], "answer": "", "needs_clarification": False}
final_state_long = app.invoke(initial_state_long)
print("\n--- 최종 상태 (긴 쿼리) ---")
print(final_state_long)

