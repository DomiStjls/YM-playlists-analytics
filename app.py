# console_app.py
import os
import argparse
import logging
import sys
from tabulate import tabulate
from collections import Counter
from utils import (
    get_favorite_tracks,
    get_user_id_from_token,
    get_token_from_env,
    get_user_playlists,
    write_tracks_to_file,
    get_user_like_playlists,
    get_users_likes_artists,
    get_user_like_albums,
)
from colorama import just_fix_windows_console
just_fix_windows_console()

class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


# Логирование
if not os.path.exists("logs"):
    os.mkdir("logs")
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
# )
# logging.basicConfig(
#     filename="logs/app.log",
#     level=logging.DEBUG,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
# )


def get_stats(user_id=None):
    albums = get_user_like_albums(user_id=user_id)
    liked_playlists = get_user_like_playlists(user_id=user_id)
    own_playlists = get_user_playlists(user_id=user_id)
    artists = get_users_likes_artists(user_id=user_id)
    if not user_id:
        user_id = get_user_id_from_token()["id"]
    try:
        print(f"\n{bcolors.OKCYAN}id пользователя:{bcolors.ENDC} {user_id}\n")

        print(f"{bcolors.OKCYAN}Понравившиеся альбомы:{bcolors.ENDC} {len(albums)}")
        if albums:
            album_table = [[a["album_id"], a["album_title"]] for a in albums]
            print(
                tabulate(
                    album_table,
                    headers=["id альбома", "Название альбома"],
                    tablefmt="rst",
                )
            )
        print()

        print(f"{bcolors.OKCYAN}Понравившиеся плейлисты:{bcolors.ENDC} {len(liked_playlists)}")
        if liked_playlists:
            liked_table = [
                [
                    p["playlist_uid"],
                    p["playlist_title"],
                    p["owner_uid"],
                    p["owner_name"],
                ]
                for p in liked_playlists
            ]
            print(
                tabulate(
                    liked_table,
                    headers=[
                        "id плейлиста",
                        "Название",
                        "id владельца",
                        "Имя владельца",
                    ],
                    tablefmt="rst",
                )
            )
        print()

        print(f"{bcolors.OKCYAN}Собственные плейлисты:{bcolors.ENDC} {len(own_playlists)}")
        if own_playlists:
            own_table = [
                [p["kind"], p["playlist_title"], p["track_count"]]
                for p in own_playlists
            ]
            print(
                tabulate(
                    own_table,
                    headers=["Номер", "Название", "Количество треков"],
                    tablefmt="rst",
                )
            )
        print()

        print(f"{bcolors.OKCYAN}Понравившиеся исполнители:{bcolors.ENDC} {len(artists)}")
        if artists:
            artist_table = [
                [a["artist_id"], a["artist_name"], ", ".join(a["artist_genres"])]
                for a in artists
            ]
            print(
                tabulate(
                    artist_table,
                    headers=["id исполнителя", "Имя", "Жанры"],
                    tablefmt="rst",
                )
            )
        print()

        artists_genres = []
        for artist in artists:
            [artists_genres.append(genre) for genre in artist["artist_genres"]]
        most_common_genres = Counter(artists_genres).most_common(3)
        print(
            f"{bcolors.OKCYAN}Самые часто встречающиеся жанры среди любимых авторов:{bcolors.ENDC} {', '.join([genre[0] for genre in most_common_genres])}"
        )
    except UnicodeEncodeError:
        print(
            bcolors.WARNING +"UnicodeEncodeError. В названии плейлиста или чего-нибудь еще есть некорректные символы, которые не отображаются в данной консоли. Смените кодировку или консоль." + bcolors.ENDC)


def get_fav_tracks(user_id=None):
    tracks = get_favorite_tracks(user_id=user_id)
    for track in tracks[:10]:
        print(
            f"{track['title']} - {', '.join(artist['name'] for artist in track['artists'])} - {track['duration'] / 60000:.2f}min"
        )


def get_playlist(user_id=None):
    pass


def compare_playlists(user1, user2):
    pl1 = get_user_playlists(user_id=user1)
    pl2 = get_user_playlists(user_id=user2)
    print("\nПлейлисты пользователя 1:")
    for i, p in enumerate(pl1):
        print(f"{i}: {p.title}")
    i1 = int(input("Выберите номер плейлиста для пользователя 1: "))

    print("\nПлейлисты пользователя 2:")
    for i, p in enumerate(pl2):
        print(f"{i}: {p.title}")
    i2 = int(input("Выберите номер плейлиста для пользователя 2: "))

    t1 = set(t.id for t in pl1[i1].fetch_tracks())
    t2 = set(t.id for t in pl2[i2].fetch_tracks())
    common = t1 & t2
    print(f"\n🔁 Общих треков: {len(common)}")


def find_owner(user_id=None):
    playlists = get_user_playlists(user_id=user_id)
    for i, p in enumerate(playlists):
        print(f"{i}: {p.title} — от {p.owner.uid}")
    i = int(input("Владельца какого плейлиста ищем: "))
    owner_id = playlists[i].owner.uid
    print(f"\n👤 Владелец этого плейлиста: {owner_id}")


def main():
    # Сначала проверим, есть ли --en
    is_english = "--en" in sys.argv

    help_text = {
        "desc": "Yandex Music CLI Analytics"
        if is_english
        else "Консольная аналитика Яндекс Музыки",
        "my": "Show my liked tracks" if is_english else "Показать мои любимые треки",
        "other": "Show another user's playlist"
        if is_english
        else "Показать треки другого пользователя",
        "compare": "Compare two users' playlists"
        if is_english
        else "Сравнить плейлисты двух пользователей",
        "find": "Find the owner of a liked playlist"
        if is_english
        else "Найти владельца плейлиста из лайков",
    }

    parser = argparse.ArgumentParser(description=help_text["desc"])
    parser.add_argument("--my", action="store_true", help=help_text["my"])
    parser.add_argument("--other", metavar="USER_ID", help=help_text["other"])
    parser.add_argument(
        "--compare", nargs=2, metavar=("USER1", "USER2"), help=help_text["compare"]
    )
    parser.add_argument("--find-owner", action="store_true", help=help_text["find"])
    parser.add_argument(
        "--en", action="store_true", help="switch help to English"
    )  # скрытый переключатель

    args = parser.parse_args()

    if args.my:
        get_stats()
    elif args.other:
        get_stats(args.other)
    elif args.compare:
        compare_playlists(args.compare[0], args.compare[1])
    elif args.find_owner:
        find_owner()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
