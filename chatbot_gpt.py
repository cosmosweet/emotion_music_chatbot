from openai import OpenAI

#키 설정
def init_chat_key(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)

# 메시지 리스트 초기화
def init_chat_context(system_prompt: str = "당신은 사용자와 자연스럽게 대화를 이어가는 챗봇입니다.\
당신의 목적은 사용자의 말을 잘 이해하고, 부드럽고 친근하게 응답하는 것입니다.\
당신의 응답은 시스템에서 감정을 분석하는 데 사용되므로, 자연스럽고 맥락 있게 대화만 해주세요.\
긴 답변은 피하고, 실제 사람과 사람이 채팅하듯 간결하게 답장해주세요.\
일상을 되묻는 등, 공감하는 말하기를 해주세요.") -> list:
    return [{"role": "system", "content": system_prompt}]

# 메시지 히스토리 업데이트 및 GPT 응답 반환
def get_chat_reply(client: OpenAI, messages: list, user_input: str, model: str = "gpt-3.5-turbo") -> str:
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=model,
        messages=messages
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