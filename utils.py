# getting the user's favorite tracks
from yandex_music import Client
import os
from dotenv import load_dotenv
import pandas as pd

# logging.basicConfig(
#     level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )


# to get the token: https://yandex-music.readthedocs.io/en/main/token.html
def get_token_from_env():
    load_dotenv()
    token = os.getenv("TOKEN", None)
    return token

def is_available(owner):
    unavailable_owners = ['yamusic', 'yandex', 'yandexmusic', 'яндекс']
    return all([el not in str(owner) for el in unavailable_owners])
    

def get_user_id_from_token(token=None):
    if not token:
        token = get_token_from_env()
    if not token:
        return None
    info = Client(token=token).init().me
    return {"id": info.account.uid, "full_name": info.account.full_name}


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


def get_tracks_from_playlist(token=None, user_id=None, are_favorite=False, kind=None):
    if not token:
        token = get_token_from_env()
    if not token:
        return None
    client = Client(token=token).init()
    if are_favorite:
        playlist = client.users_likes_tracks(user_id=user_id).fetch_tracks()
    else:
        playlist = client.users_playlists(kind=kind, user_id=user_id).fetch_tracks()
    tracks = []
    for track in playlist:
        tracks.append(
            {
                "title": track.title,
                "id": track.id,
                "duration": track.duration_ms,
                "artists": ", ".join(
                    [f"{artist.name} - {artist.id}" for artist in track.artists]
                ),
                "albums": ", ".join(
                    [f"{album.title} - {album.id}" for album in track.albums]
                ),
            }
        )
    return tracks


def get_user_playlists(token=None, user_id=None):
    if not token:
        token = get_token_from_env()
    if not token:
        return None
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
    return playlists_list


def get_user_like_playlists(token=None, user_id=None):
    if not token:
        token = get_token_from_env()
    if not token:
        return None
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
    return playlists_list


def get_user_like_albums(token=None, user_id=None):
    if not token:
        token = get_token_from_env()
    if not token:
        return None
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
    return albums_list


def get_users_likes_artists(token=None, user_id=None):
    if not token:
        token = get_token_from_env()
    if not token:
        return None
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
                "artist_genres": ', '.join(artist.artist.genres),
                "track_count": artist.artist.counts.tracks,
            }
        )
    return artists_list
