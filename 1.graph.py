from typing import TypedDict, List
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableLambda # LCEL Runnable 사용 예시
import operator # 상태 업데이트 예시 (리스트 추가 등)

# 1. 상태 정의
class SearchSummarizeState(TypedDict):
    query: str
    documents: List[str]
    summary: str

# 2. 노드 정의 (Python 함수 사용)

def search_documents(state: SearchSummarizeState) -> dict:
    """주어진 쿼리로 문서를 검색하는 (가짜) 함수"""
    print(f"--- 노드: 검색 수행 ---")
    query = state['query']
    # 실제로는 여기서 검색 API 호출 등이 이루어집니다.
    # 여기서는 간단하게 가짜 문서를 반환합니다.
    documents = [
        f"{query}에 대한 문서 1: LangGraph는 상태 관리에 유용합니다.",
        f"{query}에 대한 문서 2: 노드와 엣지로 그래프를 정의합니다.",
    ]
    print(f"검색된 문서: {documents}")
    # 상태 업데이트: 'documents' 키에 검색 결과 저장
    return {"documents": documents}

def summarize_documents(state: SearchSummarizeState) -> dict:
    """검색된 문서를 요약하는 (가짜) 함수"""
    print(f"--- 노드: 요약 수행 ---")
    documents = state['documents']
    # 실제로는 여기서 LLM 요약 Chain을 호출합니다.
    # 여기서는 간단하게 요약 결과를 생성합니다.
    summary = f"'{state['query']}' 검색 결과 요약: " + " ".join(doc.split(': ')[1] for doc in documents)
    print(f"생성된 요약: {summary}")
    # 상태 업데이트: 'summary' 키에 요약 결과 저장
    return {"summary": summary}

# 3. 그래프 빌더 생성 및 노드 추가
workflow = StateGraph(SearchSummarizeState)

workflow.add_node("searcher", search_documents)
workflow.add_node("summarizer", summarize_documents)

# 4. 엣지 및 진입점/종료점 설정
workflow.set_entry_point("searcher") # 검색 노드에서 시작
workflow.add_edge("searcher", "summarizer") # 검색 후 요약 노드로 이동
workflow.set_finish_point("summarizer") # 요약 노드에서 종료 (명시적 지정)

# 5. 그래프 컴파일
app = workflow.compile()

# 6. 그래프 실행
initial_state = {"query": "LangGraph란 무엇인가?", "documents": [], "summary": ""}
final_state = app.invoke(initial_state)

print("\n--- 최종 상태 ---")
print(final_state)