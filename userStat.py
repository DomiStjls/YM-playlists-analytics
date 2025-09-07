from collections import Counter
import statistics
from datetime import datetime, timedelta
from utils import (
    get_user_id_from_token,
    get_tracks_from_playlist,
    get_user_playlists,
    get_user_like_playlists,
    get_users_likes_artists,
    get_user_like_albums,
    add_known_ids,
    is_available,
)
from tabulate import tabulate


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


def analyze_track_years(tracks):
    """Анализирует годы релизов треков для определения музыкальных эпох."""
    years = []
    # current_year = datetime.now().year

    for track in tracks:
        year = track["year"]
        if year:
            years.append(int(year))

    if not years:
        return None

    return {
        "avg_year": round(statistics.mean(years)),
        "oldest_year": min(years),
        "newest_year": max(years),
        "year_range": max(years) - min(years),
        "decades": Counter([year // 10 * 10 for year in years]),
    }


def calculate_music_personality(genres, artists_data, duration_stats):
    """Определяет музыкальную личность на основе предпочтений."""
    personality_traits = []

    # Анализ по жанрам
    if any(genre in ["rock", "metal", "punk"] for genre in genres):
        personality_traits.append("Рокер")
    if any(genre in ["pop", "mainstream"] for genre in genres):
        personality_traits.append(" Поп-меломан")
    if any(genre in ["jazz", "blues", "classical"] for genre in genres):
        personality_traits.append("Ценитель классики")
    if any(genre in ["electronic", "techno", "house"] for genre in genres):
        personality_traits.append("Электронщик")
    if any(genre in ["indie", "alternative"] for genre in genres):
        personality_traits.append(" Инди-исследователь")

    # Анализ по длительности треков
    if duration_stats and duration_stats["avg"] > 300000:  # > 5 минут
        personality_traits.append("Любитель эпических композиций")
    elif duration_stats and duration_stats["avg"] < 180000:  # < 3 минут
        personality_traits.append("Любитель коротких хитов")

    # Анализ разнообразия
    if len(set(genres)) > 10:
        personality_traits.append("Музыкальный всеядный")
    elif len(set(genres)) < 3:
        personality_traits.append("Музыкальный минималист")

    return personality_traits if personality_traits else ["Уникальный меломан"]


def get_stats_enhanced(user_id=None):
    """Расширенная функция статистики пользователя с детальной аналитикой."""
    if not user_id or user_id == -1:
        user_id = get_user_id_from_token()["id"]

    # Получаем основные данные
    albums = get_user_like_albums(user_id=user_id)
    liked_playlists = get_user_like_playlists(user_id=user_id)
    own_playlists = get_user_playlists(user_id=user_id)
    artists = get_users_likes_artists(user_id=user_id)
    favorite_tracks = get_tracks_from_playlist(user_id=user_id, are_favorite=True)

    # Обрабатываем known_ids
    known_ids = [
        (pl["owner_uid"], pl["owner_name"])
        for pl in liked_playlists
        if is_available(pl["owner_name"].lower())
    ]
    add_known_ids(known_ids)

    try:
        print(f"\n{bcolors.HEADER}{'=' * 80}")
        print(f"МУЗЫКАЛЬНАЯ СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ {user_id}")
        print(f"{'=' * 80}{bcolors.ENDC}\n")

        # =============== БАЗОВАЯ СТАТИСТИКА ===============
        print(f"{bcolors.OKCYAN} БАЗОВАЯ СТАТИСТИКА:{bcolors.ENDC}")
        print(f"├─ Понравившиеся альбомы: {len(albums)}")
        print(f"├─ Понравившиеся плейлисты: {len(liked_playlists)}")
        print(f"├─ Собственные плейлисты: {len(own_playlists)}")
        print(f"├─ Понравившиеся исполнители: {len(artists)}")
        print(f"└─ Любимые треки: {len(favorite_tracks) if favorite_tracks else 0}\n")

        # =============== АНАЛИЗ ЛЮБИМЫХ ТРЕКОВ ===============
        if favorite_tracks:
            print(f"{bcolors.OKCYAN}АНАЛИЗ ЛЮБИМЫХ ТРЕКОВ:{bcolors.ENDC}")

            # 1. Средняя длина трека
            durations = [
                track.get("duration", 0)
                for track in favorite_tracks
                if track.get("duration")
            ]
            if durations:
                avg_duration = sum(durations) / len(durations)
                total_duration = sum(durations)
                print(
                    f"├─ Средняя длина трека: {int(avg_duration // 60000)}:{int((avg_duration % 60000) // 1000):02d}"
                )
                print(
                    f"├─ Общая длительность треков: {str(timedelta(milliseconds=total_duration)).split(".")[0]}"
                )
                print(
                    f"├─ Самый короткий трек: {int(min(durations) // 60000)}:{int((min(durations) % 60000) // 1000):02d}"
                )
                print(
                    f"└─ Самый длинный трек: {int(max(durations) // 60000)}:{int((max(durations) % 60000) // 1000):02d}\n"
                )

            # 2. Топ-5 артистов по количеству треков в любимых 
            all_track_artists = []
            for track in favorite_tracks:
                artists_str = track.get("artists", "")
                if artists_str:
                    track_artists = []
                    for artist_part in artists_str.split(", "):
                        if " - " in artist_part:
                            artist_name = artist_part.rsplit(" - ", 1)[0].strip()
                            track_artists.append(artist_name)
                    all_track_artists.extend(track_artists)

            if all_track_artists:
                top_track_artists = Counter(all_track_artists).most_common(5)
                print(
                    f"{bcolors.OKCYAN}ТОП-5 АРТИСТОВ В ЛЮБИМЫХ ТРЕКАХ:{bcolors.ENDC}"
                )
                for i, (artist, count) in enumerate(top_track_artists, 1):
                    print(f"  {i}. {artist}: {count} треков")
                print()

        # =============== ЖАНРОВЫЙ АНАЛИЗ ===============                               пока фигня 
        if favorite_tracks:
            genres = [el["genre"] for el in favorite_tracks if el["genre"]]
            for artist in artists:
                genres = (
                    artist["artist_genres"].split(", ")
                    if artist["artist_genres"]
                    else []
                )
                genres.extend([genre.strip() for genre in genres if genre.strip()])

            if genres:
                most_common_genres = Counter(genres).most_common(10)
                print(f"{bcolors.OKCYAN}ЖАНРОВЫЙ АНАЛИЗ:{bcolors.ENDC}")
                print(f"├─ Всего уникальных жанров: {len(set(genres))}")
                print(
                    f"├─ Топ-3 жанра: {', '.join([f'{genre}({count})' for genre, count in most_common_genres[:3]])}"
                )
                print(
                    f"└─ Редкие жанры: {', '.join([genre for genre, count in most_common_genres[-5:] if count == 1])}\n"
                )

        # =============== ДОПОЛНИТЕЛЬНЫЕ МЕТРИКИ ===============

        # 3. Коэффициент разнообразия исполнителей                                  пока фигня 
        # if artists:
        #     total_artist_tracks = sum(
        #         artist.get("track_count", 0) for artist in artists
        #     )
        #     avg_tracks_per_artist = total_artist_tracks / len(artists) if artists else 0
        #     print(f"{bcolors.OKCYAN}КОЭФФИЦИЕНТ РАЗНООБРАЗИЯ:{bcolors.ENDC}")
        #     print(
        #         f"├─ Среднее количество треков на артиста: {avg_tracks_per_artist:.0f}"
        #     )

        #     # Находим артистов с наибольшим количеством треков
        #     top_artists_by_tracks = sorted(
        #         artists, key=lambda x: x.get("track_count", 0), reverse=True
        #     )[:5]
        #     print("├─ Топ-артисты по количеству треков:")
        #     for i, artist in enumerate(top_artists_by_tracks, 1):
        #         print(
        #             f"│   {i}. {artist['artist_name']}: {artist.get('track_count', 0)} треков"
        #         )
        #     print()

        # 4. Анализ коллабораций
        if favorite_tracks:
            collab_tracks = 0
            for track in favorite_tracks:
                artists_str = track.get("artists", "")
                if artists_str and len(artists_str.split(", ")) > 1:
                    collab_tracks += 1

            collab_ratio = (
                collab_tracks / len(favorite_tracks) if favorite_tracks else 0
            )
            print(f"{bcolors.OKCYAN}АНАЛИЗ КОЛЛАБОРАЦИЙ:{bcolors.ENDC}")
            print(
                f"├─ Треки с коллаборациями: {collab_tracks} из {len(favorite_tracks)}"
            )
            print(f"└─ Процент коллабораций: {collab_ratio:.1%}\n")

        # 5. Анализ музыкальных эпох (по названиям треков)
        if favorite_tracks:
            year_analysis = analyze_track_years(favorite_tracks)
            if year_analysis:
                print(f"{bcolors.OKCYAN} АНАЛИЗ МУЗЫКАЛЬНЫХ ЭПОХ:{bcolors.ENDC}")
                print(f"├─ Средний год музыки: {year_analysis['avg_year']}")
                print(
                    f"├─ Диапазон лет: {year_analysis['oldest_year']} - {year_analysis['newest_year']}"
                )
                print(f"├─ Временной размах: {year_analysis['year_range']} лет")
                top_decades = year_analysis["decades"].most_common(3)
                print(
                    f"└─ Любимые десятилетия: {', '.join([f'{decade}е({count})' for decade, count in top_decades])}\n"
                )

        # 6. Социальная активность (анализ лайкнутых плейлистов)
        if liked_playlists:
            owners = [
                pl["owner_name"]
                for pl in liked_playlists
                if is_available(pl["owner_name"].lower())
            ]
            unique_owners = len(set(owners))
            avg_tracks_per_liked_playlist = (
                statistics.mean([pl.get("track_count", 0) for pl in liked_playlists])
                if liked_playlists
                else 0
            )

            print(f"{bcolors.OKCYAN} СОЦИАЛЬНАЯ АКТИВНОСТЬ:{bcolors.ENDC}")
            print(f"├─ Уникальных создателей плейлистов: {unique_owners}")
            print(
                f"├─ Среднее количество треков в лайкнутом плейлисте: {int(avg_tracks_per_liked_playlist)}"
            )
            if owners:
                most_liked_creators = Counter(owners).most_common(3)
                print(
                    f"└─ Топ-создатели: {', '.join([f'{creator}({count})' for creator, count in most_liked_creators])}\n"
                )

        # 7. Продуктивность создания контента
        if own_playlists:
            total_own_tracks = sum(pl.get("track_count", 0) for pl in own_playlists)
            avg_tracks_per_own_playlist = (
                total_own_tracks / len(own_playlists) if own_playlists else 0
            )

            print(f"{bcolors.OKCYAN} ПРОДУКТИВНОСТЬ СОЗДАНИЯ:{bcolors.ENDC}")
            print(f"├─ Всего треков в собственных плейлистах: {total_own_tracks}")
            print(
                f"├─ Среднее количество треков на плейлист: {int(avg_tracks_per_own_playlist)}"
            )

            # Самые большие плейлисты
            biggest_playlists = sorted(
                own_playlists, key=lambda x: x.get("track_count", 0), reverse=True
            )[:3]
            print("└─ Самые большие плейлисты:")
            for i, pl in enumerate(biggest_playlists, 1):
                print(
                    f"    {i}. '{pl['playlist_title']}': {pl.get('track_count', 0)} треков"
                )
            print()

        # 8. Музыкальная личность
        if artists and genres:
            duration_stats = {"avg": statistics.mean(durations)} if durations else None
            personality = calculate_music_personality(genres, artists, duration_stats)
            print(f"{bcolors.OKCYAN}МУЗЫКАЛЬНАЯ ЛИЧНОСТЬ:{bcolors.ENDC}")
            print(f"└─ {' | '.join(personality)}\n")

        # =============== ДЕТАЛЬНЫЕ ТАБЛИЦЫ (сокращенные) ===============
        print(f"{bcolors.OKCYAN} ДЕТАЛЬНЫЕ ДАННЫЕ:{bcolors.ENDC}")

        # Альбомы
        if albums:
            print("\nПонравившиеся альбомы:")
            album_table = [
                [
                    a["album_id"],
                    a["album_title"][:50] + "..."
                    if len(a["album_title"]) > 50
                    else a["album_title"],
                ]
                for a in albums[:10]
            ]
            print(
                tabulate(
                    album_table, headers=["ID", "Название альбома"], tablefmt="grid"
                )
            )
            if len(albums) > 10:
                print(f"   ...и еще {len(albums) - 10} альбомов")

        # Понравившиеся плейлисты
        if liked_playlists:
            print("\nПонравившиеся плейлисты:")
            liked_table = [
                [
                    p["playlist_uid"],
                    p["playlist_title"][:40] + "..."
                    if len(p["playlist_title"]) > 40
                    else p["playlist_title"],
                    p["track_count"],
                    p["owner_name"][:20] + "..."
                    if len(p["owner_name"]) > 20
                    else p["owner_name"],
                ]
                for p in liked_playlists[:10]
            ]
            print(
                tabulate(
                    liked_table,
                    headers=["ID", "Название", "Треков", "Владелец"],
                    tablefmt="grid",
                )
            )
            if len(liked_playlists) > 10:
                print(f"   ...и еще {len(liked_playlists) - 10} плейлистов")

        # Собственные плейлисты
        if own_playlists:
            print("\nСобственные плейлисты:")
            own_table = [
                [
                    p["kind"],
                    p["playlist_title"][:50] + "..."
                    if len(p["playlist_title"]) > 50
                    else p["playlist_title"],
                    p["track_count"],
                ]
                for p in own_playlists[:10]
            ]
            print(
                tabulate(
                    own_table, headers=["ID", "Название", "Треков"], tablefmt="grid"
                )
            )
            if len(own_playlists) > 10:
                print(f"   ...и еще {len(own_playlists) - 10} плейлистов")

        # Исполнители
        if artists:
            print("\nПонравившиеся исполнители:")
            artist_table = [
                [
                    a["artist_name"][:30] + "..."
                    if len(a["artist_name"]) > 30
                    else a["artist_name"],
                    a["track_count"],
                    a["artist_genres"][:40] + "..."
                    if len(a["artist_genres"]) > 40
                    else a["artist_genres"],
                ]
                for a in artists[:10]
            ]
            print(
                tabulate(
                    artist_table,
                    headers=["Исполнитель", "Треков", "Жанры"],
                    tablefmt="grid",
                )
            )
            if len(artists) > 10:
                print(f"   ...и еще {len(artists) - 10} исполнителей")

        print(
            f"\n{bcolors.OKGREEN} Анализ завершен! Для получения полных данных используйте функции экспорта.{bcolors.ENDC}"
        )
        print(
            f"{bcolors.WARNING} Данные ограничены первыми 10-20 элементами для читаемости.{bcolors.ENDC}\n"
        )

    except UnicodeEncodeError:
        print(
            f"{bcolors.WARNING}  UnicodeEncodeError: Обнаружены некорректные символы. Смените кодировку консоли.{bcolors.ENDC}"
        )
    except Exception as e:
        print(f"{bcolors.FAIL} Ошибка при получении статистики: {str(e)}{bcolors.ENDC}")


# Дополнительная функция для быстрого обзора
def get_quick_stats_summary(user_id=None):
    """Краткая сводка основных метрик пользователя."""
    if not user_id or user_id == -1:
        user_id = get_user_id_from_token()["id"]

    albums = get_user_like_albums(user_id=user_id)
    liked_playlists = get_user_like_playlists(user_id=user_id)
    own_playlists = get_user_playlists(user_id=user_id)
    artists = get_users_likes_artists(user_id=user_id)
    favorite_tracks = get_tracks_from_playlist(user_id=user_id, are_favorite=True)

    # Базовые метрики
    total_content = (
        len(albums) + len(liked_playlists) + len(own_playlists) + len(artists)
    )

    # Жанровое разнообразие
    all_genres = []
    for artist in artists:
        genres = (
            artist.get("artist_genres", "").split(", ")
            if artist.get("artist_genres")
            else []
        )
        all_genres.extend([g.strip() for g in genres if g.strip()])

    genre_diversity = len(set(all_genres))

    # Музыкальная активность
    total_own_tracks = sum(pl.get("track_count", 0) for pl in own_playlists)

    return {
        "user_id": user_id,
        "total_liked_content": total_content,
        "albums_count": len(albums),
        "liked_playlists_count": len(liked_playlists),
        "own_playlists_count": len(own_playlists),
        "artists_count": len(artists),
        "favorite_tracks_count": len(favorite_tracks) if favorite_tracks else 0,
        "genre_diversity": genre_diversity,
        "total_own_tracks": total_own_tracks,
        "top_genres": Counter(all_genres).most_common(5) if all_genres else [],
    }
