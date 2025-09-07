# getting the user's favorite tracks
from yandex_music import Client
import os
from dotenv import load_dotenv
import pandas as pd
import json
import hashlib
from datetime import datetime, timedelta
import pickle

# logging.basicConfig(
#     level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )

# Настройки кэша
CACHE_DIR = "cache"
DEFAULT_CACHE_DURATION = 3600  # 1 час в секундах


def ensure_cache_dir():
    """Создает директорию для кэша если она не существует."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def get_cache_key(func_name, **kwargs):
    """Генерирует уникальный ключ для кэша на основе имени функции и параметров."""
    # Исключаем токен из ключа по соображениям безопасности
    cache_params = {k: v for k, v in kwargs.items() if k != "token"}
    params_str = json.dumps(cache_params, sort_keys=True, default=str)
    return hashlib.md5(f"{func_name}:{params_str}".encode()).hexdigest()


def get_from_cache(cache_key, cache_duration=DEFAULT_CACHE_DURATION):
    """Получает данные из кэша если они не устарели."""
    ensure_cache_dir()
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.pkl")

    if not os.path.exists(cache_file):
        return None

    try:
        with open(cache_file, "rb") as f:
            cached_data = pickle.load(f)

        # Проверяем время создания кэша
        if datetime.now() - cached_data["timestamp"] > timedelta(
            seconds=cache_duration
        ):
            os.remove(cache_file)  # Удаляем устаревший кэш
            return None

        return cached_data["data"]
    except (pickle.PickleError, KeyError, OSError):
        # Если файл поврежден, удаляем его
        try:
            os.remove(cache_file)
        except OSError:
            pass
        return None


def save_to_cache(cache_key, data):
    """Сохраняет данные в кэш."""
    ensure_cache_dir()
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.pkl")

    try:
        with open(cache_file, "wb") as f:
            pickle.dump({"timestamp": datetime.now(), "data": data}, f)
    except (pickle.PickleError, OSError) as e:
        print(f"Предупреждение: Не удалось сохранить кэш: {e}")


def clear_cache():
    """Очищает весь кэш."""
    if os.path.exists(CACHE_DIR):
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith(".pkl"):
                try:
                    os.remove(os.path.join(CACHE_DIR, filename))
                except OSError:
                    pass


# to get the token: https://yandex-music.readthedocs.io/en/main/token.html
def get_token_from_env():
    load_dotenv()
    token = os.getenv("TOKEN", None)
    return token


def is_available(owner):
    unavailable_owners = ["yamusic", "yandex", "yandexmusic", "яндекс"]
    return all([el not in str(owner) for el in unavailable_owners])


def get_user_id_from_token(token=None, use_cache=True):
    """Получает ID пользователя и полное имя по токену с кэшированием."""
    if not token:
        token = get_token_from_env()
    if not token:
        return None

    if use_cache:
        cache_key = get_cache_key(
            "get_user_id_from_token", token_hash=hashlib.md5(token.encode()).hexdigest()
        )
        cached_result = get_from_cache(cache_key, cache_duration=86400)  # Кэш на сутки
        if cached_result is not None:
            return cached_result

    try:
        info = Client(token=token).init().me
        result = {"id": info.account.uid, "full_name": info.account.full_name}

        if use_cache:
            save_to_cache(cache_key, result)

        return result
    except Exception as e:
        print(f"Ошибка получения информации о пользователе: {e}")
        return None


def write_data_to_txt(data, name_file="playlist.txt"):
    text = ""
    keys = list(data[0].keys())
    text += f"{'; '.join(keys)}\n"
    for el in data:
        text += f"{'; '.join([str(el[key]) for key in keys])}\n"
    if not os.path.isdir("data"):
        os.mkdir("data")
    path = os.path.join("data", name_file)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def write_data_to_csv(data, name_file="playlist.csv"):
    df = pd.DataFrame(data)
    if not os.path.isdir("data"):
        os.mkdir("data")
    path = os.path.join("data", name_file)
    df.to_csv(path, index=False, sep=";")


def add_known_ids(known_ids):
    if os.path.exists("data/ids.txt"):
        ids = open("data/ids.txt", encoding="utf-8").read()
    else:
        ids = f"{get_user_id_from_token()['id']} - {get_user_id_from_token()['full_name']}"
        with open("data/ids.txt", "w", encoding="utf-8") as f:
            f.write(ids + "\n")
    with open("data/ids.txt", "a", encoding="utf-8") as f:
        known_ids = [
            f"{uid} - {name}"
            for uid, name in list(set(known_ids))
            if str(uid) not in ids
        ]
        f.write("\n".join(known_ids) + "\n")


def get_tracks_from_playlist(
    token=None, user_id=None, are_favorite=False, kind=None, use_cache=True
):
    """Получает треки из плейлиста с кэшированием."""
    if not token:
        token = get_token_from_env()
    if not token:
        return None

    if use_cache:
        cache_key = get_cache_key(
            "get_tracks_from_playlist",
            user_id=user_id,
            are_favorite=are_favorite,
            kind=kind,
            token_hash=hashlib.md5(token.encode()).hexdigest(),
        )
        cached_result = get_from_cache(
            cache_key, cache_duration=1800
        )  # Кэш на 30 минут
        if cached_result is not None:
            return cached_result

    try:
        client = Client(token=token).init()
        if are_favorite:
            playlist = client.users_likes_tracks(user_id=user_id).fetch_tracks()
        else:
            playlist = [
                el.track
                for el in client.users_playlists(
                    kind=kind, user_id=user_id
                ).fetch_tracks()
            ]

        tracks = []
        for track in playlist:
            tracks.append(
                {
                    "title": track.title,
                    "id": track.id,
                    "duration": track.duration_ms,
                    "year": track.albums[0].year if len(track.albums) > 0 else None,
                    "genre": track.albums[0].genre if len(track.albums) > 0 else None,
                    "artists": ", ".join(
                        [f"{artist.name} - {artist.id}" for artist in track.artists]
                    ),
                    "albums": ", ".join(
                        [f"{album.title} - {album.id}" for album in track.albums]
                    ),
                }
            )

        if use_cache:
            save_to_cache(cache_key, tracks)
        print(f"Получено треков: {len(tracks)}")
        return tracks
    except Exception as e:
        print(f"Ошибка получения треков: {e}")
        return None


def get_user_playlists(token=None, user_id=None, use_cache=True):
    """Получает плейлисты пользователя с кэшированием."""
    if not token:
        token = get_token_from_env()
    if not token:
        return None

    if use_cache:
        cache_key = get_cache_key(
            "get_user_playlists",
            user_id=user_id,
            token_hash=hashlib.md5(token.encode()).hexdigest(),
        )
        cached_result = get_from_cache(
            cache_key, cache_duration=1800
        )  # Кэш на 30 минут
        if cached_result is not None:
            return cached_result

    try:
        client = Client(token=token).init()
        playlists = client.users_playlists_list(user_id=user_id)

        playlists_list = []
        for playlist in playlists:
            playlists_list.append(
                {
                    "playlist_uid": playlist.uid,
                    "kind": playlist.kind,
                    "track_count": playlist.track_count,
                    "playlist_title": playlist.title,
                    "playlist_duration": playlist.duration_ms,
                }
            )

        if use_cache:
            save_to_cache(cache_key, playlists_list)

        return playlists_list
    except Exception as e:
        print(f"Ошибка получения плейлистов: {e}")
        return None


def get_user_like_playlists(token=None, user_id=None, use_cache=True):
    """
    Get list of playlists liked by user with caching.

    Parameters
    ----------
    token : str
        Yandex Music API token.
    user_id : int
        User id.
    use_cache : bool
        Whether to use caching.

    Returns
    -------
    list
        List of dictionaries with owner's id, owner's name, playlist's id, track count, playlist's title, and playlist's duration.
    """
    if not token:
        token = get_token_from_env()
    if not token:
        return None

    if use_cache:
        cache_key = get_cache_key(
            "get_user_like_playlists",
            user_id=user_id,
            token_hash=hashlib.md5(token.encode()).hexdigest(),
        )
        cached_result = get_from_cache(cache_key, cache_duration=3600)  # Кэш на 1 час
        if cached_result is not None:
            return cached_result

    try:
        client = Client(token=token).init()
        playlists = client.users_likes_playlists(user_id=user_id)
        playlists_list = []
        for playlist in playlists:
            playlists_list.append(
                {
                    "owner_uid": playlist.playlist.owner.uid,
                    "owner_name": playlist.playlist.owner.name,
                    "playlist_uid": playlist.playlist.uid,
                    "track_count": playlist.playlist.track_count,
                    "playlist_title": playlist.playlist.title,
                    "playlist_duration": playlist.playlist.duration_ms,
                }
            )

        if use_cache:
            save_to_cache(cache_key, playlists_list)

        return playlists_list
    except Exception as e:
        print(f"Ошибка получения понравившихся плейлистов: {e}")
        return None


def get_user_like_albums(token=None, user_id=None, use_cache=True):
    """
    Get list of albums liked by user with caching.

    Parameters
    ----------
    token : str
        Yandex Music API token.
    user_id : int
        User id.
    use_cache : bool
        Whether to use caching.

    Returns
    -------
    list
        List of dictionaries with album's id, track count and title.
    """
    if not token:
        token = get_token_from_env()
    if not token:
        return None

    if use_cache:
        cache_key = get_cache_key(
            "get_user_like_albums",
            user_id=user_id,
            token_hash=hashlib.md5(token.encode()).hexdigest(),
        )
        cached_result = get_from_cache(cache_key, cache_duration=7200)  # Кэш на 2 часа
        if cached_result is not None:
            return cached_result

    try:
        client = Client(token=token).init()
        if not user_id:
            albums = client.users_likes_albums()
        else:
            albums = client.users_likes_albums(user_id=user_id)

        albums_list = []
        for album in albums:
            albums_list.append(
                {
                    "album_id": album.album.id,
                    "track_count": album.album.track_count,
                    "album_title": album.album.title,
                }
            )

        if use_cache:
            save_to_cache(cache_key, albums_list)

        return albums_list
    except Exception as e:
        print(f"Ошибка получения понравившихся альбомов: {e}")
        return None


def get_users_likes_artists(token=None, user_id=None, use_cache=True):
    """
    Get list of artists liked by user with caching.

    Parameters
    ----------
    token : str
        Yandex Music API token.
    user_id : int
        User id.
    use_cache : bool
        Whether to use caching.

    Returns
    -------
    list
        List of dictionaries with artist id, name, genres and track count.
    """
    if not token:
        token = get_token_from_env()
    if not token:
        return None

    if use_cache:
        cache_key = get_cache_key(
            "get_users_likes_artists",
            user_id=user_id,
            token_hash=hashlib.md5(token.encode()).hexdigest(),
        )
        cached_result = get_from_cache(cache_key, cache_duration=7200)  # Кэш на 2 часа
        if cached_result is not None:
            return cached_result

    try:
        client = Client(token=token).init()
        if not user_id:
            artists = client.users_likes_artists()
        else:
            artists = client.users_likes_artists(user_id=user_id)

        artists_list = []
        for artist in artists:
            artists_list.append(
                {
                    "artist_id": artist.artist.id,
                    "artist_name": artist.artist.name,
                    "artist_genres": ", ".join(artist.artist.genres),
                    "track_count": artist.artist.counts.tracks,
                }
            )

        if use_cache:
            save_to_cache(cache_key, artists_list)

        return artists_list
    except Exception as e:
        print(f"Ошибка получения понравившихся артистов: {e}")
        return None


def get_cache_info():
    """Возвращает информацию о состоянии кэша."""
    if not os.path.exists(CACHE_DIR):
        return {"cache_files": 0, "total_size": 0}

    cache_files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".pkl")]
    total_size = sum(os.path.getsize(os.path.join(CACHE_DIR, f)) for f in cache_files)

    return {
        "cache_files": len(cache_files),
        "total_size": total_size,
        "total_size_mb": round(total_size / 1024 / 1024, 2),
    }


def cleanup_expired_cache():
    """Удаляет устаревшие файлы кэша."""
    if not os.path.exists(CACHE_DIR):
        return 0

    removed_count = 0
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith(".pkl"):
            cache_file = os.path.join(CACHE_DIR, filename)
            try:
                with open(cache_file, "rb") as f:
                    cached_data = pickle.load(f)

                # Проверяем время создания кэша
                if datetime.now() - cached_data["timestamp"] > timedelta(
                    seconds=DEFAULT_CACHE_DURATION
                ):
                    os.remove(cache_file)
                    removed_count += 1
            except (pickle.PickleError, KeyError, OSError):
                # Удаляем поврежденные файлы
                try:
                    os.remove(cache_file)
                    removed_count += 1
                except OSError:
                    pass

    return removed_count
