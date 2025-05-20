import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import random

# 실제 배포용
# load_dotenv()

# CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
# CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
# REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# 프로젝트 발표용 API
CLIENT_ID = os.getenv("e0b9304753a04c0c90c887066cd702ce")
CLIENT_SECRET = os.getenv("79e2ff5799794bc0bd672ae97388aaaa")
REDIRECT_URI = os.getenv("http://127.0.0.1:8080/callback")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id = CLIENT_ID,
    client_secret = CLIENT_SECRET,
    redirect_uri = REDIRECT_URI,
    scope = 'user-read-private'
))

# 감정별 검색어 리스트
emotion_to_queries = {
    '기쁨': ['기분 좋아지는 노래', '신나는 노래', '행복해지는 플레이리스트', '즐거운 음악', '긍정적인 바이브'],
    '슬픔': ['슬픈 노래 모음', '우울할 때 듣는 노래', '이별 노래', '감성적인 음악', '눈물나는 플레이리스트'],
    '분노': ['화날 때 듣는 노래', '스트레스 날려버리는 음악', '분노 해소용 노래', '강한 에너지의 노래', '록 플레이리스트']
}

def recommend_music_by_emotion(emotion: str):
    """
    감정 키워드에 따라 Spotify에서 음악을 추천하는 함수

    Parameters:
        emotion (str): 사용자의 감정 ('기쁨', '슬픔', '분노')

    Returns:
        dict | None: 추천된 플레이리스트 및 곡 정보를 담은 dict
                     (플레이리스트 이름, 링크, 곡 리스트), 추천 실패 시 None
    """
    query_list = emotion_to_queries.get(emotion, [emotion])
    query = random.choice(query_list)
    
    results = sp.search(q=query, type='playlist', limit=20)
    playlists = results['playlists']['items']

    filtered = [
        p for p in playlists
        if p is not None and '찬양' not in (p.get('name', '') + p.get('description', ''))
    ]

    if not filtered:
        return None

    playlist = random.choice(filtered)
    playlist_id = playlist['id']
    playlist_name = playlist['name']
    playlist_url = playlist['external_urls']['spotify']

    # 최대 50곡 불러오고 그중 랜덤 3곡 추출
    tracks_data = sp.playlist_tracks(playlist_id, limit=50, market="KR")
    all_tracks = tracks_data['items']
    selected_tracks = random.sample(all_tracks, k=min(3, len(all_tracks)))

    songs = []
    for t in selected_tracks:
        track = t['track']
        name = track['name']
        artist = track['artists'][0]['name']
        url = track['external_urls']['spotify']
        songs.append({
            'name': name,
            'artist': artist,
            'url': url
        })

    return {
        'emotion': emotion,
        'playlist_name': playlist_name,
        'playlist_url': playlist_url,
        'songs': songs
    }

#############################################################################

# 이건 main.py에 붙여넣기 해야함.    
# from recommendation import recommend_music_by_emotion

# result = recommend_music_by_emotion('기쁨')

# if result:
#     print(f"🎧 감정: {result['emotion']}")
#     print(f"📚 추천 플레이리스트: {result['playlist_name']}")
#     print(f"🔗 링크: {result['playlist_url']}\n")

#     for song in result['songs']:
#         print(f"🎵 {song['name']} - {song['artist']}\n   🔗 {song['url']}\n")
# else:
#     print("❌ 감정에 맞는 플레이리스트를 찾지 못했습니다.")

#############################################################################

# 테스트: 파일을 직접 실행했을 때만 동작하게 함
# if __name__ == "__main__":
#     emotion = input("감정을 입력하세요 (기쁨 / 슬픔 / 분노): ").strip()

#     result = recommend_music_by_emotion(emotion)

#     if result:
#         print(f"\n🎧 감정: {result['emotion']}")
#         print(f"📚 추천 플레이리스트: {result['playlist_name']}")
#         print(f"🔗 링크: {result['playlist_url']}\n")

#         print("🎵 추천 곡 리스트:")
#         for song in result['songs']:
#             print(f"- {song['name']} - {song['artist']}")
#             print(f"  🔗 {song['url']}\n")
#     else:
#         print("❌ 감정에 맞는 플레이리스트를 찾지 못했습니다.")

#############################################################################