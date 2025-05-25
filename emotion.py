from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import json
import requests

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 허깅페이스 모델 ID
MODEL_ID = "cosmosweet/emotion_music_chatbot"

# 모델 및 토크나이저 로드 (최초 1회)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID).to(device)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
labels = json.loads(requests.get(
    f"https://huggingface.co/{MODEL_ID}/resolve/main/label_classes.json"
).text)

# 감정 예측 함수
def predict_emotion_with_probs(text: str):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128).to(device)
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=1).cpu().numpy().flatten()
        pred_idx = int(torch.argmax(logits, dim=1))
        pred_emotion = labels[pred_idx]
    return pred_emotion, probs  # 감정, 확률분포 리턴

# main.py 안에서 사용 예시
# from emotion_predictor import predict_emotion

# text = "오늘 너무 기분 좋아!"
# emotion = predict_emotion(text)

# print("예측 감정:", emotion)