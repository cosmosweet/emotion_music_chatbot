from flask import Flask, request, jsonify, render_template, session
from emotion import predict_emotion_with_probs
from chatbot_gpt import init_chat_key, init_chat_context, get_chat_reply
from recommender import recommend_music_by_emotion
from db import (
    init_db,
    register_user,
    login_user,
    save_user_messages,
    get_user_messages,
    get_user_emotion_history,
    save_emotion_for_user
)
from datetime import datetime, timedelta
import os
import json
from dotenv import load_dotenv

init_db()
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = init_chat_key(api_key)
messages = init_chat_context()

main = Flask(__name__)
main.secret_key = os.getenv("FLASK_SECRET_KEY", "my_default_secret_key")

user_emotion_counter = {}
user_last_recommend_time = {}

@main.route("/")
def index():
    return render_template("website.html")

@main.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    nickname = data.get("nickname")

    success = register_user(email, password, nickname)
    if not success:
        return jsonify({"success": False, "message": "이미 가입된 이메일입니다."})
    return jsonify({"success": True})

@main.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    success, nickname = login_user(email, password)
    if not success:
        return jsonify({"success": False, "message": "이메일 또는 비밀번호가 틀렸습니다."})

    session["user_id"] = email
    session["nickname"] = nickname
    messages = get_user_messages(email)

    return jsonify({
        "success": True,
        "nickname": nickname,
        "messages": messages
    })

@main.route("/emotion_history", methods=["GET"])
def emotion_history():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "로그인이 필요합니다."})

    emotion_data = get_user_emotion_history(user_id)
    today = datetime.now().date()
    past_7_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    filtered = {day: emotion_data.get(day, {}) for day in past_7_days}

    return jsonify({"success": True, "history": filtered})

@main.route("/chat", methods=["POST"])
def chat():
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"success": False, "message": "로그인이 필요합니다."})

        user_input = request.json.get("message", "").strip()
        if not user_input:
            return jsonify({"success": False, "message": "메시지가 비어 있습니다."})

        emotion, probs = predict_emotion_with_probs(user_input)
        confidence = max(probs)

        if confidence >= 0.6:
            save_emotion_for_user(user_id, emotion)
            user_emotion_counter.setdefault(user_id, {})
            user_emotion_counter[user_id][emotion] = user_emotion_counter[user_id].get(emotion, 0) + 1

        now = datetime.now()
        last_time = user_last_recommend_time.get(user_id)

        print(f"[쿨다운 체크] user: {user_id}")
        print(f"마지막 추천 시각: {last_time}")
        print(f"현재 시각: {now}")

        cooldown_passed = not last_time or (now - last_time >= timedelta(minutes=10))
        print(f"쿨다운 통과 여부: {cooldown_passed}")

        recommend = False
        if user_emotion_counter.get(user_id, {}).get(emotion, 0) >= 2 and cooldown_passed:
            recommend = True
            user_last_recommend_time[user_id] = now
            user_emotion_counter[user_id][emotion] = 0

        messages = get_user_messages(user_id)
        if not messages:
            messages = init_chat_context()
        messages.append({"role": "user", "content": user_input})

        reply = get_chat_reply(client, messages, user_input)
        messages.append({"role": "assistant", "content": reply})

        save_user_messages(user_id, messages)

        song = None
        if recommend:
            reply += f"\n\n지금 감정이 '{emotion}'인 것 같아요. 노래 하나 추천해드릴게요!"
            song_data = recommend_music_by_emotion(user_input, emotion)
            if song_data and song_data.get("songs"):
                first_song = song_data["songs"][0]
                song = {
                    "recommended": True,
                    "content": f"{first_song['name']} - {first_song['artist']}\n🔗 {first_song['url']}"
                }
            else:
                song = {
                    "recommended": True,
                    "content": "죄송해요, 노래 추천을 가져오지 못했어요."
                }

        response = {
            "success": True,
            "emotion": emotion,
            "reply": reply
        }
        if song:
            response["song"] = song
        return jsonify(response)

    except Exception as e:
        return jsonify({"success": False, "reply": f"서버 오류: {str(e)}"})

@main.route("/visualization")
def visualization():
    return render_template("visualization.html")

@main.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

if __name__ == "__main__":
    main.run(host="0.0.0.0", port=5001, debug=True)