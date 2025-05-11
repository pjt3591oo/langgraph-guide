from typing import TypedDict, Annotated, List, Optional, Sequence
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# 각 Worker는 별도의 Runnable (Chain, AgentExecutor 등) 이라고 가정
# from some_module import research_agent, code_writer_agent

# 1. 상태 정의 (Supervisor가 라우팅에 사용할 정보 포함)
class SupervisorState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add] # 전체 대화/작업 기록
    next_worker: Optional[str] # 다음에 호출할 Worker 이름 (또는 END)

# 2. Worker 정의 (여기서는 간단한 함수로 가정)
def research_worker(state: SupervisorState) -> dict:
    print("--- Worker: 연구 수행 ---")
    # 실제로는 research_agent.invoke(...) 등 호출
    last_message = state['messages'][-1].content
    result = f"'{last_message}'에 대한 연구 결과입니다."
    return {"messages": [AIMessage(content=result)]}

def code_writer_worker(state: SupervisorState) -> dict:
    print("--- Worker: 코드 작성 ---")
    # 실제로는 code_writer_agent.invoke(...) 등 호출
    last_message = state['messages'][-1].content
    result = f"'{last_message}' 요청에 따른 코드:\n```python\nprint('Hello World!')\n```"
    return {"messages": [AIMessage(content=result)]}

# 각 Worker를 식별하는 이름과 실제 실행 객체 매핑
worker_map = {
    "Researcher": research_worker, # 실제로는 Runnable 객체
    "CodeWriter": code_writer_worker, # 실제로는 Runnable 객체
}

# 3. Supervisor 노드 정의
supervisor_llm = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    model_name="l3-8b-stheno-v3.1-iq-imatrix"
)

def supervisor_node(state: SupervisorState) -> dict:
    print("--- Supervisor: 다음 작업자 결정 ---")
    messages = state['messages']
    # LLM에게 현재 상태를 주고 다음 Worker를 결정하도록 요청
    # 실제 프롬프트는 더 정교해야 함 (Worker 설명, 종료 조건 등 포함)
    prompt = f"""현재 대화 내용: {messages}.
    당신은 Supervisor입니다. 다음으로 어떤 Worker를 호출해야 할까요?
    선택지: [{', '.join(worker_map.keys())}, FINISH]
    가장 적합한 Worker 이름 하나만 또는 FINISH를 반환하세요:"""

    response = supervisor_llm.invoke(prompt)
    next_node_name = response.content.strip()
    print(f"Supervisor 결정: {next_node_name}")

    if next_node_name == "FINISH":
        return {"next_worker": END}
    elif next_node_name in worker_map:
        return {"next_worker": next_node_name}
    else: # 예외 처리 (잘못된 이름 반환 시)
        print(f"경고: 알 수 없는 Worker 이름 '{next_node_name}'. 종료합니다.")
        return {"next_worker": END}

# 4. 그래프 빌드
workflow = StateGraph(SupervisorState)

# Supervisor 노드 추가
workflow.add_node("supervisor", supervisor_node)

# Worker 노드들 추가
for name, worker_runnable in worker_map.items():
    workflow.add_node(name, worker_runnable)
    # 각 Worker 실행 후에는 Supervisor에게 결과를 보고하러 돌아감
    workflow.add_edge(name, "supervisor")

# 조건부 엣지: Supervisor의 결정에 따라 Worker로 라우팅
workflow.add_conditional_edges(
    "supervisor",           # Supervisor 노드 실행 후
    lambda state: state["next_worker"], # 상태의 next_worker 값을 보고
    {name: name for name in worker_map.keys()}.update({END: END}) # 각 Worker 이름에 해당하는 노드로 매핑
)

# 진입점 설정
workflow.set_entry_point("supervisor")

# 그래프 컴파일
multi_agent_app = workflow.compile()
multi_agent_app.get_graph().print_ascii()

# 5. 실행 예시
initial_state = {"messages": [HumanMessage(content="LangGraph에 대해 조사하고 간단한 예제 코드를 작성해줘.")]}

print("--- Multi-Agent 시스템 실행 시작 ---")
for step in multi_agent_app.stream(initial_state, {"recursion_limit": 10}):
    step_name = list(step.keys())[0]
    print(f"\n--- 실행된 노드/엣지: {step_name} ---")
    # Supervisor 상태에서 메시지만 출력 (간결성 위해)
    if 'supervisor' in step and 'messages' in step['supervisor']:
         print(step['supervisor']['messages'][-1]) # 마지막 메시지만 표시
    elif step_name in worker_map:
        print(step[step_name]['messages'][-1]) # Worker 결과 메시지
    # else: # 조건부 엣지 등 다른 단계는 상세 정보 생략
    #     print(step[step_name])

print("\n--- Multi-Agent 시스템 실행 완료 ---")