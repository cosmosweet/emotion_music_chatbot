from openai import OpenAI

#키 설정
def init_chat_key(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)

# 메시지 리스트 초기화
def init_chat_context(system_prompt: str = """
너는 사용자와 편하게 대화하는 감정 공감 챗봇이야.  
절대 설명형 말투나 상담사 말투 쓰지 마.  
절대 너의 이야기를 꺼내거나, 예시로 들거나, 긴 글을 쓰지 마.  

대신 사용자의 감정을 듣고, 친구처럼 짧게 공감해줘.  
말투는 말 줄임표, 반말, 이모지, '~' 등을 써도 괜찮고, 너무 문장 다듬지 마.  
예를 들어 “헐 진짜?”, “헉 너무 좋았겠다~”, “그거 완전 속상했겠다ㅠ” 이런 식으로!  

2문장 이내로 말하고, 가끔 “그땐 어땠어?” 같은 질문도 붙여서 대화 이어줘.  
절대 너의 경험을 말하지 마. 사용자한테만 집중해줘.

지금부터 나랑 반말로 대화해줘.
""") -> list:
    return [{"role": "system", "content": system_prompt}]

# 메시지 히스토리 업데이트 및 GPT 응답 반환
def get_chat_reply(client: OpenAI, messages: list, user_input: str, model: str = "gpt-4o") -> str:
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=1.2,
        max_tokens=120
    )

    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    return reply

#from chatbot_gpt import init_openai_client, init_chat_context, get_gpt_reply

#client = init_openai_client("your-api-key")
#messages = init_chat_context()

#text = "오늘 날씨 어때?"
#response = get_gpt_reply(client, messages, text)

#print("GPT 응답:", response)