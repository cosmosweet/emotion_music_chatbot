import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
import re
from collections import Counter
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_class_weight
from konlpy.tag import Okt

df_train = pd.read_csv('train_mapped.csv')
df_test = pd.read_csv('valid_mapped.csv')

df_train = df_train.rename(columns={'mapped_label': 'label'})
df_test = df_test.rename(columns={'mapped_label': 'label'})

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 2. 감정별 30,000개로 균등 샘플링
df_train_balanced = (
    df_train.groupby('label')
    .apply(lambda x: x.sample(n=30000, random_state=42) if len(x) > 30000 else x)
    .reset_index(drop=True)
    .sample(frac=1, random_state=42)
)

# 3. 라벨 인코딩
le = LabelEncoder()
le.fit(pd.concat([df_train_balanced['label'], df_test['label']]))
df_train_balanced['label_id'] = le.transform(df_train_balanced['label'])
df_test['label_id'] = le.transform(df_test['label'])

# 4. Okt tokenizer 기반 vocab 생성
okt = Okt()

def tokenize(text):
    return okt.morphs(text, stem=True)

vocab_counter = Counter()
for text in df_train_balanced['text']:
    vocab_counter.update(tokenize(text))

most_common = vocab_counter.most_common(30000 - 2)
word2idx = {word: idx + 2 for idx, (word, _) in enumerate(most_common)}
word2idx['<PAD>'] = 0
word2idx['<UNK>'] = 1

def encode(text, max_len=100):
    tokens = tokenize(text)
    encoded = [word2idx.get(t, 1) for t in tokens]
    return encoded[:max_len] + [0] * max(0, max_len - len(encoded))

# 5. Dataset 정의
class EmotionDataset(Dataset):
    def __init__(self, texts, labels):
        self.X = torch.tensor([encode(t) for t in texts], dtype=torch.long)
        self.y = torch.tensor(labels, dtype=torch.long)
    def __len__(self): return len(self.X)
    def __getitem__(self, idx): return self.X[idx], self.y[idx]

train_dataset = EmotionDataset(df_train_balanced['text'], df_train_balanced['label_id'])
test_dataset = EmotionDataset(df_test['text'], df_test['label_id'])

train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=16)


class TransformerClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_heads, num_layers, output_dim, dropout=0.1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=embed_dim * 4,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc = nn.Linear(embed_dim, output_dim)

    def forward(self, x):
        x = self.embedding(x)
        x = self.transformer_encoder(x)
        return self.fc(x[:, 0, :])  # 첫 번째 토큰 사용

# 모델 정의
model = TransformerClassifier(
    vocab_size=len(word2idx),
    embed_dim=128,
    num_heads=4,
    num_layers=2,
    output_dim=len(le.classes_)
).to(device)

# Xavier 초기화
def init_weights(m):
    if isinstance(m, nn.Linear):
        nn.init.xavier_uniform_(m.weight)
        if m.bias is not None:
            nn.init.zeros_(m.bias)
model.apply(init_weights)

# 손실함수와 옵티마이저
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-3)

# 학습 함수
def train_one_epoch():
    model.train()
    total_loss = 0
    for X, y in train_loader:
        X, y = X.to(device), y.to(device)
        optimizer.zero_grad()
        output = model(X)
        loss = criterion(output, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss

# 학습 실행
for epoch in range(10):
    loss = train_one_epoch()
    print(f"Epoch {epoch+1}, Loss: {loss:.4f}")


def predict(text):
    model.eval()
    x = torch.tensor([encode(text)], dtype=torch.long).to(device)
    with torch.no_grad():
        out = model(x)
        pred = torch.argmax(out, dim=1).item()
        return le.inverse_transform([pred])[0]
  
# Test  
print(predict("오늘 기분이 너무 좋고 날씨도 화창해"))
print(predict("짜증나고 화가 나는 날"))
print(predict("슬퍼서 울고 싶어"))
print(predict("마음이 좀 편안해졌어"))