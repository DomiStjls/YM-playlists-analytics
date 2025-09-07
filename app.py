# console_app.py
import os
import argparse
import sys
from utils import (
    get_user_id_from_token,
    write_data_to_txt,
    write_data_to_csv,
    get_tracks_from_playlist,
    get_user_playlists,
    get_user_like_playlists,
    get_users_likes_artists,
    get_user_like_albums,
    add_known_ids,
    get_cache_info, 
    
)
from userStat import get_quick_stats_summary, get_stats_enhanced
from compare import compare_playlists_enhanced, print_comparison_report
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
# if not os.path.exists("logs"):
#     os.mkdir("logs")
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
# )
# logging.basicConfig(
#     filename="logs/app.log",
#     level=logging.DEBUG,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
# )


def get_stats(user_id=None, short=False):
    return get_stats_enhanced(user_id) if not short else get_quick_stats_summary(user_id)


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
        all_t1 = get_tracks_from_playlist(
            user_id=user1, kind=i1, are_favorite=i1 == "0"
        )
        print("\nПлейлисты пользователя 2:")
        for p in pl2:
            kinds2.append(str(p["kind"]))
            print(f"{p['kind']}: {p['playlist_title']}")
        while True:
            i2 = input("Выберите номер плейлиста для пользователя 2: ")
            if i2 in kinds2:
                break
        
        all_t2 = get_tracks_from_playlist(
            user_id=user2, kind=i2, are_favorite=i2 == "0"
        )
        
        print_comparison_report(compare_playlists_enhanced(all_t1, all_t2, playlist1_name="Плейлист пользователя 1", playlist2_name="Плейлист пользователя 2"))
        # t1 = set([el["id"] for el in all_t1])
        # t2 = set([el["id"] for el in all_t2])
        # common = t1 & t2
        # print(f"\nОбщих треков: {len(common)} - {len(common) / len(t1 | t2) * 100:.2f}% от общего количества треков")


def find_owner(user_id=None):
    playlists = get_user_like_playlists(user_id=user_id)
    d = {}
    for i, p in enumerate(playlists):
        d[i] = (p['owner_uid'], p['owner_name'])
        print(f"{i + 1}: {p['playlist_uid']} - {p['playlist_title']} - {p['owner_name']}")
    i = int(input("Владельца какого плейлиста ищем: ")) -1 
    
    print(f"\nid Владельца этого плейлиста: {d[i][0]}. Добавить в известные пользователи? (y/n)")
    if input() == "y":
        add_known_ids([(d[i][0], d[i][1])])
    


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
    parser.add_argument("--find", action="store_true", help=help_text["find"])
    parser.add_argument("--en", action="store_true", help="switch help to English")
    
    parser.add_argument('--cache', action='store_true', help='get cache info')

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
    elif args.find:
        find_owner()
        
    elif args.cache:
        print(get_cache_info())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
