from openai import OpenAI

#키 설정
def init_chat_key(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)

# 메시지 리스트 초기화
def init_chat_context(system_prompt: str = "You are a helpful assistant.") -> list:
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