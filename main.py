from flask import Flask, request, jsonify, render_template
from emotion import predict_emotion_with_probs
from chatbot_gpt import init_chat_key, init_chat_context, get_chat_reply
from recommender import recommend_music_by_emotion
from datetime import datetime, timedelta
import os
import json
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
current_user_email = None

USER_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def save_emotion_for_user(email, emotion):
    users = load_users()
    today = datetime.now().strftime("%Y-%m-%d")
    if email in users:
        users[email].setdefault("emotions", {})
        users[email]["emotions"].setdefault(today, {})
        users[email]["emotions"][today][emotion] = users[email]["emotions"][today].get(emotion, 0) + 1
        save_users(users)

@main.route("/")
def index():
    return render_template("website.html")

@main.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    nickname = data.get("nickname")

    users = load_users()
    if email in users:
        return jsonify({"success": False, "message": "이미 가입된 이메일입니다."})

    users[email] = {
        "password": password,
        "nickname": nickname,
        "emotions": {}
    }
    save_users(users)
    return jsonify({"success": True})

@main.route("/login", methods=["POST"])
def login():
    global current_user_email
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    users = load_users()
    if email not in users:
        return jsonify({"success": False, "message": "등록되지 않은 이메일입니다."})
    if users[email]["password"] != password:
        return jsonify({"success": False, "message": "비밀번호가 틀렸습니다."})

    current_user_email = email
    return jsonify({"success": True, "nickname": users[email]["nickname"]})

@main.route("/emotion_history", methods=["GET"])
def emotion_history():
    if not current_user_email:
        return jsonify({"success": False, "message": "로그인이 필요합니다."})

    users = load_users()
    emotions = users.get(current_user_email, {}).get("emotions", {})

    today = datetime.now().date()
    past_7_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    filtered = {day: emotions.get(day, {}) for day in past_7_days}

    return jsonify({"success": True, "history": filtered})

@main.route("/chat", methods=["POST"])
def chat():
    global emotion_counter, last_recommend_time, messages
    try:
        user_input = request.json["message"]

        # 감정 분석
        emotion, probs = predict_emotion_with_probs(user_input)
        confidence = max(probs)

        # 감정 누적 저장
        if confidence >= 0.6:
            emotion_counter[emotion] = emotion_counter.get(emotion, 0) + 1
            if current_user_email:
                save_emotion_for_user(current_user_email, emotion)

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

        # GPT 응답 생성
        reply = get_chat_reply(client, messages, user_input)
        if recommend:
            reply += f"\n\n지금 감정이 {emotion}인 것 같은데, 괜찮은 노래 하나 추천해드릴게요"

        if len(messages) > 20:
            messages = messages[:1] + messages[-19:]

        song = None
        if recommend:
            song_data = recommend_music_by_emotion(user_input, emotion)
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

        response = {
            "emotion": emotion,
            "reply": reply
        }
        if song:
            response["song"] = song

        return jsonify(response)

    except Exception as e:
        return jsonify({"reply": f"서버 오류: {str(e)}"})

# 새로 추가된 감정 시각화 페이지
@main.route("/visualization")
def visualization():
    return render_template("visualization.html")

if __name__ == "__main__":
    main.run(host="0.0.0.0", port=5000, debug=True)
