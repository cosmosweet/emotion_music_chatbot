import random
from sentence_transformers import SentenceTransformer, util
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Spotify 인증
SPOTIPY_CLIENT_ID = 'e0b9304753a04c0c90c887066cd702ce'
SPOTIPY_CLIENT_SECRET = '79e2ff5799794bc0bd672ae97388aaaa'

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
))

# 감정별 대표 단어 사전
emotion_to_situation = {
    '기쁨': ['행복', '설레는', '썸', '연애', '달달한', '산책', '에너지'],
    '슬픔': ['슬픔', '밤', '고통', '눈물', '이별', '외로움', '우울', '고독', '절망', '답답', '막막', '감성'],
    '분노': ['분노', '짜증', '폭발', '스트레스', '싸움', '격렬', '부셔', '빡칠때']
}

# Sentence-BERT 모델 로드 (최초 1회)
model = SentenceTransformer('jhgan/ko-sroberta-multitask')

def get_best_matching_emotion_word(user_input, emotion):
    candidates = emotion_to_situation.get(emotion, [])
    sentences = [user_input] + candidates

    embeddings = model.encode(sentences, convert_to_tensor=True)
    user_embedding = embeddings[0]
    candidate_embeddings = embeddings[1:]

    cosine_scores = util.cos_sim(user_embedding, candidate_embeddings)[0]
    best_idx = cosine_scores.argmax().item()

    return candidates[best_idx]

def recommend_music(user_input, emotion):
    query_for_search = get_best_matching_emotion_word(user_input, emotion)
    print(f"[감정 기반 검색 쿼리] {query_for_search}")

    try:
        results = sp.search(q=query_for_search, type='playlist', limit=50, market='KR')
        playlists = results.get('playlists', {}).get('items', [])
    except Exception as e:
        print(f"❗ Spotify 검색 오류: {e}")
        return None

    if not playlists:
        print("❗ 검색된 플레이리스트가 없습니다.")
        return None

    playlist = random.choice(playlists)
    playlist_id = playlist.get('id')
    playlist_name = playlist.get('name')
    playlist_url = playlist.get('external_urls', {}).get('spotify')

    try:
        tracks_data = sp.playlist_tracks(playlist_id, limit=50, market="KR")
        all_tracks = tracks_data.get('items', [])
        selected_tracks = random.sample(all_tracks, k=min(3, len(all_tracks)))
    except Exception as e:
        print(f"❗ 트랙 정보 수집 실패: {e}")
        selected_tracks = []

    songs = []
    for t in selected_tracks:
        track = t.get('track')
        if track:
            songs.append({
                'name': track.get('name'),
                'artist': track.get('artists', [{}])[0].get('name', 'Unknown'),
                'url': track.get('external_urls', {}).get('spotify')
            })

    return {
        'emotion': emotion,
        'query': query_for_search,
        'playlist': playlist_name,
        'playlist_url': playlist_url,
        'songs': songs
    }