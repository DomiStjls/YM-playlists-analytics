# console_app.py
import os
import argparse
import logging
import sys
from tabulate import tabulate
from collections import Counter
from utils import (
    get_user_id_from_token,
    is_available,
    get_token_from_env,
    write_data_to_txt,
    write_data_to_csv,
    get_tracks_from_playlist,
    get_user_playlists,
    get_user_like_playlists,
    get_users_likes_artists,
    get_user_like_albums,
)
from colorama import just_fix_windows_console

just_fix_windows_console()
if not os.path.exists("data"):
    os.mkdir("data")


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
    if not user_id or user_id == -1:
        user_id = get_user_id_from_token()["id"]
    albums = get_user_like_albums(user_id=user_id)
    liked_playlists = get_user_like_playlists(user_id=user_id)
    known_ids = [
        (pl["owner_uid"], pl["owner_name"])
        for pl in liked_playlists
        if is_available(pl["owner_name"].lower())
    ]
    if os.path.exists("data/ids.txt"):
        ids = open("data/ids.txt", encoding="utf-8").read()
    else:
        ids = [f"{user_id} - {get_user_id_from_token()['full_name']}"]
        with open("data/ids.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(ids) + "\n")

    with open("data/ids.txt", "a", encoding="utf-8") as f:
        known_ids = [
            f"{uid} - {name}"
            for uid, name in list(set(known_ids))
            if str(uid) not in ids
        ]
        f.write("\n".join(known_ids) + "\n")
    own_playlists = get_user_playlists(user_id=user_id)
    artists = get_users_likes_artists(user_id=user_id)

    try:
        print(f"\n{bcolors.OKCYAN}id пользователя:{bcolors.ENDC} {user_id}\n")

        print(f"{bcolors.OKCYAN}Понравившиеся альбомы:{bcolors.ENDC} {len(albums)}")
        if albums:
            album_table = [[a["album_id"], a["album_title"]] for a in albums[:20]]
            print(
                tabulate(
                    album_table,
                    headers=["id альбома", "Название альбома"],
                    tablefmt="rst",
                )
            )
        print("...Сокращено\n" if len(albums) > 20 else "\n")

        print(
            f"{bcolors.OKCYAN}Понравившиеся плейлисты:{bcolors.ENDC} {len(liked_playlists)}"
        )
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
        print("...Сокращено\n" if len(liked_playlists) > 20 else "\n")

        print(
            f"{bcolors.OKCYAN}Собственные плейлисты:{bcolors.ENDC} {len(own_playlists)}"
        )
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
        print("...Сокращено\n" if len(own_playlists) > 20 else "\n")

        print(
            f"{bcolors.OKCYAN}Понравившиеся исполнители:{bcolors.ENDC} {len(artists)}"
        )
        if artists:
            artist_table = [
                [a["artist_id"], a["artist_name"], a["artist_genres"]] for a in artists
            ]
            print(
                tabulate(
                    artist_table,
                    headers=["id исполнителя", "Имя", "Жанры"],
                    tablefmt="rst",
                )
            )
        print("...Сокращено\n" if len(artists) > 20 else "\n")

        artists_genres = []
        for artist in artists:
            [
                artists_genres.append(genre)
                for genre in artist["artist_genres"].split(", ")
            ]
        most_common_genres = Counter(artists_genres).most_common(3)
        print(
            f"{bcolors.OKCYAN}Самые часто встречающиеся жанры среди любимых авторов:{bcolors.ENDC} {', '.join([genre[0] for genre in most_common_genres])}"
        )
        print(
            "Все выводы сокращены до 20 элементов. Для получения полного списка скачайте необходинные данные.\n"
        )
    except UnicodeEncodeError:
        print()
        print(
            bcolors.WARNING
            + "UnicodeEncodeError. В названии плейлиста или чего-нибудь еще есть некорректные символы, которые не отображаются в данной консоли. Смените кодировку или консоль."
            + bcolors.ENDC
        )


def download(file_name, type, user_id=get_user_id_from_token()["id"]):
    # FavoriteTracks, LikedArtists, LikedAlbums, LikedPlaylists, OwnedPlaylists
    try:
        if type == "FavoriteTracks":
            data = get_tracks_from_playlist(user_id=user_id, are_favourite=True)
        elif type == "LikedArtists":
            data = get_users_likes_artists(user_id=user_id)
        elif type == "LikedAlbums":
            data = get_user_like_albums(user_id=user_id)
        elif type == "LikedPlaylists":
            data = get_user_like_playlists(user_id=user_id)
        elif type == "OwnedPlaylists":
            data = get_user_playlists(user_id=user_id)

        if file_name.split(".")[1] == "csv":
            write_data_to_csv(data=data, name_file=file_name)
            print(f"Данные сохранены в файл {file_name} в папке data")
        elif file_name.split(".")[1] == "txt":
            write_data_to_txt(data=data, name_file=file_name)
            print(f"Данные сохранены в файл {file_name} в папке data")
        else:
            print("Неверное расширение файла, доступны только txt и csv.")
    except Exception as e:
        print(e)


def get_fav_tracks(user_id=None):
    # tracks = get_favorite_tracks(user_id=user_id)
    # for track in tracks[:10]:
    #     print(
    #         f"{track['title']} - {', '.join(artist['name'] for artist in track['artists'])} - {track['duration'] / 60000:.2f}min"
    #     )
    pass


def compare_playlists(user1, user2=get_user_id_from_token()["id"]):
    # if len(args) == 2:
    #     user1, user2 = args
    # elif len(args) == 1:
    #     user1 = args[0]
    #     user2 = get_user_id_from_token()["id"]
    kinds1 = []
    kinds2 = []
    pl1 = get_user_playlists(user_id=user1)
    pl2 = get_user_playlists(user_id=user2)

    pl1.append({"kind": "0", "playlist_title": "Мне нравится"})
    pl2.append({"kind": "0", "playlist_title": "Мне нравится"})
    if len(pl1) == 0 or len(pl2) == 0:
        print("Нет плейлистов у одного из пользователей.")
    else:
        print("\nПлейлисты пользователя 1:")
        for p in pl1:
            kinds1.append(str(p["kind"]))
            print(f"{p['kind']}: {p['playlist_title']}")
        while True:
            i1 = input("Выберите номер плейлиста для пользователя 1: ")
            if i1 in kinds1:
                break
        print("\nПлейлисты пользователя 2:")
        for p in pl2:
            kinds2.append(str(p["kind"]))
            print(f"{p['kind']}: {p['playlist_title']}")
        while True:
            i2 = input("Выберите номер плейлиста для пользователя 2: ")
            if i2 in kinds2:
                break
        all_t1 = get_tracks_from_playlist(
            user_id=user1, kind=i1, are_favorite=i1 == "0"
        )
        all_t2 = get_tracks_from_playlist(
            user_id=user2, kind=i2, are_favorite=i2 == "0"
        )
        t1 = set([el["id"] for el in all_t1])
        t2 = set([el["id"] for el in all_t2])
        common = t1 & t2
        print(f"\nОбщих треков: {len(common)}")


def find_owner(user_id=None):
    playlists = get_user_playlists(user_id=user_id)
    for i, p in enumerate(playlists):
        print(f"{i}: {p.title} — от {p.owner.uid}")
    i = int(input("Владельца какого плейлиста ищем: "))
    owner_id = playlists[i].owner.uid
    print(f"\nВладелец этого плейлиста: {owner_id}")


def main():
    # Сначала проверим, есть ли --en
    is_english = "--en" in sys.argv

    help_text = {
        "desc": "YM-Anal",
        "stats": "Show statistics"
        if is_english
        else "Показать статистику пользователя",
        "compare": "Compare two users' playlists"
        if is_english
        else "Сравнить плейлисты двух пользователей",
        "download": "Save to a file `FileName` (.csv and .txt) information of type `Type` (type from the list: FavoriteTracks, LikedArtists, LikedAlbums, LikedPlaylists, OwnedPlaylists) for user `UserId`"
        if is_english
        else "Сохранить в файл `FileName` (.csv и .txt) информацию типа `Type`(тип из списка: FavoriteTracks, LikedArtists, LikedAlbums, LikedPlaylists, OwnedPlaylists) пользователя `UserId`",
        "find": "Find the owner of a liked playlist"
        if is_english
        else "Найти владельца плейлиста из лайков",
    }

    parser = argparse.ArgumentParser(description=help_text["desc"])
    parser.add_argument(
        "--stats",
        nargs="?",
        const=-1,
        metavar=("UserId (optional)"),
        help=help_text["stats"],
    )
    parser.add_argument(
        "--compare",
        nargs="*",
        metavar="UserId1, UserId2 (optional)",
        help=help_text["compare"],
    )
    parser.add_argument(
        "--download",
        nargs="*",
        metavar="FileName, Type, UserId (optional)",
        help=help_text["download"],
    )
    parser.add_argument("--find-owner", action="store_true", help=help_text["find"])
    parser.add_argument("--en", action="store_true", help="switch help to English")

    args = parser.parse_args()

    if args.stats:
        get_stats(args.stats)
    elif args.compare:
        compare_playlists(*args.compare)
    elif args.download:
        a = args.download
        if len(a) < 2:
            print("Недостаточно аргументов, обязательными являются FileName и Type.")
            sys.exit(1)
        elif a[0].split(".")[1] not in ["csv", "txt"]:
            print("Аргумент FileName должен иметь расширение csv или txt.")
            sys.exit(1)
        elif a[1] not in [
            "FavoriteTracks",
            "LikedArtists",
            "LikedAlbums",
            "LikedPlaylists",
            "OwnedPlaylists",
        ]:
            print(
                "Аргумент Type должен быть одним из: FavoriteTracks, LikedArtists, LikedAlbums, LikedPlaylists, OwnedPlaylists."
            )
            sys.exit(1)
        else:
            download(*a)
    elif args.find_owner:
        find_owner()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
