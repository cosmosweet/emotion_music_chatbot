from flask import Flask, request, jsonify, render_template
from emotion import predict_emotion_with_probs
from chatbot_gpt import init_chat_key, init_chat_context, get_chat_reply
from recommender import recommend_music_by_emotion
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# .env 파일에서 키 로드
load_dotenv()

# GPT 전역 상태 초기화
api_key = os.getenv("OPENAI_API_KEY")
client = init_chat_key(api_key)
messages = init_chat_context()

# Flask 앱 초기화
main = Flask(__name__)

# 감정 카운터 및 마지막 추천 시각
emotion_counter = {}
last_recommend_time = None

# 웹 UI 라우팅
@main.route("/")
def index():
    return render_template("website.html")

# 사용자 메시지 처리
@main.route("/chat", methods=["POST"])
def chat():
    global emotion_counter, last_recommend_time, messages
    user_input = request.json["message"]

    # 감정 분석
    emotion, probs = predict_emotion_with_probs(user_input)
    confidence = max(probs)

    # 감정 누적
    if confidence >= 0.6:
        emotion_counter[emotion] = emotion_counter.get(emotion, 0) + 1

    # 음악 추천 조건 확인
    now = datetime.now()
    cooldown_passed = (
        last_recommend_time is None or
        (now - last_recommend_time) >= timedelta(minutes=10)
    )
    recommend = False
    if emotion_counter.get(emotion, 0) >= 2 and cooldown_passed:
        recommend = True
        last_recommend_time = now
        emotion_counter[emotion] = 0

    # GPT 응답 생성 with 예외 처리
    try:
        reply = get_chat_reply(client, messages, user_input)
        #음악 추천 멘트
        if recommend:
            reply += f"\n\n지금 감정이 {emotion}인 것 같은데, 괜찮은 노래 하나 추천해드릴게요"
    except Exception as e:
        reply = f"GPT 응답 오류: {str(e)}"

    # GPT 세션 길이 제한
    if len(messages) > 20:
        messages = messages[:1] + messages[-19:]

    # 음악 추천 결과 구성
    song = None  # 추천 없으면 포함 X
    if recommend:
        song_data = recommend_music_by_emotion(emotion)
        if song_data:
            first_song = song_data['songs'][0]
            song = {
                "recommended": True,
                "content": f"{first_song['name']} - {first_song['artist']}\n🔗 {first_song['url']}"
            }
        else:
            song = {
                "recommended": True,
                "content": "추천 결과를 가져오지 못했습니다."
            }

    # 응답 구성
    response = {
        "emotion": emotion,
        "reply": reply
    }
    if song:
        response["song"] = song

    return jsonify(response)

# 서버 실행
if __name__ == "__main__":
    main.run(host="0.0.0.0", port=5000, debug=True)
