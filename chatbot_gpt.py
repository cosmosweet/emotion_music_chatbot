from openai import OpenAI

# 사용자에게 API 키 입력받기
api_key = input("🔑 OpenAI API 키를 입력하세요: ").strip()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=api_key)

# 대화 메시지 초기화
messages = [{"role": "system", "content": "You are a helpful assistant."}]

print("🧠 GPT 챗봇 시작 (종료하려면 'exit' 입력)")

while True:
    user_input = input("나: ")
    if user_input.lower() == "exit":
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})

    print("GPT:", reply)