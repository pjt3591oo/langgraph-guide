from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage # 상태 관리용
from typing import TypedDict, Annotated, Sequence # 상태 정의용
import operator
import dotenv
from langchain import hub # LangChain Hub에서 프롬프트 등을 가져오기 위함
from langchain.agents import AgentExecutor, create_react_agent
from langgraph.graph import MessagesState # 미리 정의된 상태 타입 활용 가능


dotenv.load_dotenv()

# 1. LLM 준비 (도구 호출 기능 지원 모델)
# !! OpenAI API Key 설정 필요 !!
llm = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    temperature=0.7, 
    model_name="l3-8b-stheno-v3.1-iq-imatrix"
)

# 2. Tools 정의
@tool
def get_current_weather(location: str) -> str:
    """주어진 위치의 현재 날씨를 가져옵니다."""
    # 실제 API 호출 대신 더미 데이터 반환
    if "seoul" in location.lower():
        return "서울의 날씨는 맑음, 기온은 15도입니다."
    elif "busan" in location.lower():
        return "부산의 날씨는 흐림, 기온은 18도입니다."
    else:
        return f"{location}의 날씨 정보는 알 수 없습니다."

@tool
def simple_calculator(expression: str) -> str:
    """간단한 수학 표현식을 계산합니다. 예: '2+2', '10*5'"""
    try:
        # 주의: 실제 환경에서는 보안상 eval 사용에 매우 신중해야 합니다!
        result = eval(expression)
        return f"{expression}의 계산 결과는 {result}입니다."
    except Exception as e:
        return f"계산 오류: {e}"

tools = [get_current_weather, simple_calculator]

# prompt 정의
prompt = hub.pull("hwchase17/react")
print(prompt)

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

# 에이전트 실행
input_message = HumanMessage(content="서울 날씨는 어때? 그리고 5 * 8은 얼마야?")

# invoke 대신 stream 사용 시 중간 과정 확인 가능
for chunk in agent_executor.stream({"input": [input_message]}):
    print(chunk)
    print("---")

# # 최종 결과만 확인
# final_result = agent_executor.invoke({"input": [input_message]})

# # 최종 결과 출력 (AIMessage 포함)
# print("\n--- 최종 결과 ---")
# # 결과는 'input' 키 아래에 전체 대화 기록(AIMessage 포함)으로 반환됨
# ai_response = final_result['input'][-1] # 마지막 메시지가 AI의 최종 답변
# print(ai_response.content)