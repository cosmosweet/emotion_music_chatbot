# ✅ IA3 기반 감정 분류기 파인튜닝 코드
# 모델: monologg/koelectra-base-v3-discriminator

from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from peft import IA3Config, get_peft_model, TaskType
from datasets import load_dataset, Dataset
from sklearn.preprocessing import LabelEncoder
import numpy as np
import torch
import pandas as pd

# 1. 데이터 로드 및 라벨 인코딩
df_train = pd.read_csv("train_mapped.csv")
df_test = pd.read_csv("valid_mapped.csv")

df_train = df_train.rename(columns={'mapped_label': 'label'})
df_test = df_test.rename(columns={'mapped_label': 'label'})

df_train = df_train[df_train['label'] != '불안'].copy()
df_test = df_test[df_test['label'] != '불안'].copy()

df_train = (
    df_train.groupby('label')
    .apply(lambda x: x.sample(n=10000, random_state=42))
    .reset_index(drop=True)
    .sample(frac=1, random_state=42)
)

# 테스트셋도 클래스당 2,500개 샘플링 후 셔플
df_test = (
    df_test.groupby('label')
    .apply(lambda x: x.sample(n=2000, random_state=42))
    .reset_index(drop=True)
    .sample(frac=1, random_state=42)
)

label_encoder = LabelEncoder()
df_train['label'] = label_encoder.fit_transform(df_train['label'])
df_test['label'] = label_encoder.transform(df_test['label'])

# 2. 🤗 Dataset 포맷으로 변환
dataset = Dataset.from_pandas(df_train[['text', 'label']])
dataset_test = Dataset.from_pandas(df_test[['text', 'label']])

tokenizer = AutoTokenizer.from_pretrained("monologg/koelectra-base-v3-discriminator")

def tokenize_fn(example):
    return tokenizer(example["text"], padding="max_length", truncation=True, max_length=128)

tokenized_train = dataset.map(tokenize_fn, batched=True)
tokenized_test = dataset_test.map(tokenize_fn, batched=True)

# 3. 모델 로드 및 IA3 설정
base_model = AutoModelForSequenceClassification.from_pretrained(
    "monologg/koelectra-base-v3-discriminator", num_labels=3
)

ia3_config = IA3Config(
    task_type=TaskType.SEQ_CLS,
    target_modules=["query", "value", "dense", "intermediate.dense"],
    feedforward_modules=["dense", "intermediate.dense"],
    inference_mode=False
)
model2 = get_peft_model(base_model, ia3_config)

# 4. TrainingArguments 설정
targs = TrainingArguments(
    output_dir="./koelectra_ia3_ckpt",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    num_train_epochs=5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    logging_dir="./logs",
    logging_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    report_to="none"
)

# 5. 평가지표
from sklearn.metrics import accuracy_score, f1_score

def compute_metrics(p):
    preds = np.argmax(p.predictions, axis=1)
    return {
        "accuracy": accuracy_score(p.label_ids, preds),
        "f1": f1_score(p.label_ids, preds, average="macro")
    }

# 6. Trainer 구성
trainer = Trainer(
    model=model2,
    args=targs,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_test,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)

# 7. 학습 시작
trainer.train()