# 🎵 감정 기반 음악 추천 챗봇 - 챗플리 (Chatply)

사용자의 감정을 분석하고, 그 감정에 어울리는 음악을 Spotify에서 추천해주는 감정 공감 챗봇입니다.

> 좋은노래듣구십구조 (19조)  
> 김유담 (32220981) • 이철진 (32213627) • 최인준 (32214636)

---

### 🧠 프로젝트 개요

- 자연어 입력에서 사용자의 감정을 실시간 분석
- 감정에 적합한 맞춤형 Spotify 음악 추천
- 사용자의 감정 이력을 저장하고 시각화
- 모든 기능은 웹 기반 인터페이스로 제공

---

### 🛠 기술 스택

- **감정 분석**: KoELECTRA + IA3 (Fine-tuning)
- **음악 추천**: Spotify Web API (Spotipy), Sentence-BERT
- **대화 시스템**: GPT-4o (OpenAI API)
- **웹 서버**: Flask
- **프론트엔드**: HTML, JavaScript
- **데이터베이스**: SQLite (3개 테이블 구조: 사용자, 감정 이력, 메시지 로그)
- **형상 관리**: Git + GitHub (브랜치 전략 활용)

---

### 🚀 주요 기능 및 브랜치 구성

#### 1. 감정 분석기 (`feature/emotion`)
- AI-HUB 공감형 대화 데이터셋 (36,000건) 기반 파인튜닝
- KoELECTRA + IA3 구조 활용, 정확도 약 69%
- `기쁨`, `슬픔`, `분노` 3가지 감정 분류
- 확률값 기반 감정 예측
- 동일 감정이 2회 연속 60% 이상일 때 추천기 작동 (쿨다운 기능 포함)

#### 2. 음악 추천기 (`feature/recommender`)
- Spotify API로 감정별 플레이리스트 50개 검색
- KoNLPy Okt 기반 키워드 추출 → 감정별 대표 사전 구축
- Sentence-BERT 임베딩 → 사용자 입력과 플레이리스트 제목 간 유사도 계산
- 유사도 기반 상위 플레이리스트 중 무작위로 1개 선택 → 곡 추천
- 10분 쿨다운 로직 포함 → 동일 감정 반복 시 중복 추천 방지

#### 3. 챗봇 시스템 (`feature/chatbot`)
- OpenAI GPT-4o 모델 API 사용
- 프롬프트 엔지니어링 → 반말, 친구 말투 설정
- 사용자 발화 내용 DB에 저장, 맥락 유지 대화 가능

#### 4. 웹 인터페이스 (`feature/website`)
- HTML + JavaScript로 구성된 간단한 채팅 UI
- Flask 서버와 fetch API 연동
- 감정 분석 및 추천 결과 실시간 출력
- 로그인 / 회원가입 기능 구현
- 개인별 감정 이력 7일치 바 차트 시각화

#### 5. 데이터베이스 (`feature/DB`)
- SQLite3 기반 로컬 DB
- 테이블 구성:
  - `users`: 사용자 정보
  - `messages`: 사용자별 대화 이력
  - `emotions`: 날짜별 감정 결과
- 감정 예측 결과는 날짜별로 누적 저장 → 시각화에 활용

---

### 🧪 로컬 실행 방법

#### 1. 프로젝트 클론 및 가상환경 설정
```bash
git clone https://github.com/cosmosweet/emotion_music_chatbot.git
python -m venv env
source env/bin/activate   # Windows는 .\env\Scripts\activate
pip install --upgrade pip
pip install pyngrok
pip install -r requirements.txt

#### 2. .env 환경 변수 설정

.env 파일을 프로젝트 루트 디렉토리에 생성하고 다음 항목을 입력하세요:
OPENAI_API_KEY: OpenAI GPT-4o API Key (직접 발급 받아야합니다)

#### 3. ngrok 연결
ngrok 설치 후,
ngrok config add-authtoken [본인의 토큰]
를 통해 계졍을 연동해주세요

#### 4. Flask 서버 실행
python main.py
127.0.0.1:5001 접속 (끝)