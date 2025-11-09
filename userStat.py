from collections import Counter, defaultdict
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
    get_all_user_tracks,
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
    favorite_tracks = get_tracks_from_playlist(user_id=user_id, are_favourite=True)

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
                print(f"{bcolors.OKCYAN}ЖАНРОВЫЙ АНАЛИЗ ЛЮБИМЫХ ПЕСЕН:{bcolors.ENDC}")
                print(f"├─ Всего уникальных жанров: {len(set(genres))}")
                print(
                    f"├─ Топ-3 жанра: {', '.join([f'{genre}({count})' for genre, count in most_common_genres[:3]])}"
                )
                print(
                    f"└─ Редкие жанры: {', '.join([genre for genre, count in most_common_genres[-5:] if count == 1])}\n"
                )

        # =============== ДОПОЛНИТЕЛЬНЫЕ МЕТРИКИ ===============

        # 3. Аналитика вообще всех песен                                пока фигня 
        print(f"{bcolors.OKCYAN}ОБЩИЙ АНАЛИЗ ВСЕХ ПЕСЕН{bcolors.ENDC}")
        tracks = get_all_user_tracks(user_id=user_id)
        tracks_for_set = [f'{track["title"]} - {track["artists"]}' for track in tracks]
        print(f"Всего треков во всех плейлистах: {len(set(tracks_for_set))}. Из них повторяются: {len(tracks_for_set) - len(set(tracks_for_set))}")
        print("=" * 50)
        
        # 1. Метрика: Самые популярные треки (по количеству повторений в плейлистах)
        track_counts = Counter()
        track_info = {}  # Для хранения информации о треке
        
        for track in tracks:
            track_key = (track['title'], track['artists'])
            track_counts[track_key] += 1
            track_info[track_key] = track
        
        print("ТОП-10 самых частовстречающихся треков в ваших плейлистах:")
        for i, (track_key, count) in enumerate(track_counts.most_common(10), 1):
            title, artists_m = track_key
            print(f"{i:2d}. {title} - {artists_m} ({count} раз)")
        
        # 2. Метрика: Анализ по жанрам
        # genre_counts = Counter(track['genre'] for track in tracks)
        # print("\nРаспределение по жанрам:")
        # for genre, count in genre_counts.most_common(10):
        #     percentage = (count / len(tracks)) * 100
        #     print(f"   {genre}: {count} треков ({percentage:.1f}%)")
        
        # 3. Метрика: Анализ по артистам
        artist_tracks = defaultdict(list)
        for track in tracks:
            # Разбираем строку артистов "Артист1 - ID1, Артист2 - ID2"
            artists_data = track['artists'].split(', ')
            for artist_data in artists_data:
                artist_name = artist_data.split(' - ')[0]  # Берем только имя артиста
                artist_tracks[artist_name].append(track)
        
        print(f"\nТОП-10 самых прослушиваемых артистов по всем плейлистам:")
        artist_counts = {artist: len(tracks_list) for artist, tracks_list in artist_tracks.items()}
        for i, (artist, count) in enumerate(sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:10], 1):
            print(f"{i:2d}. {artist}: {count} треков")
        
        # 4. Метрика: Статистика по годам
        year_counts = Counter(track['year'] for track in tracks if track['year'])
        print(f"\nРаспределение по годам (ТОП-10):")
        for year, count in year_counts.most_common(10):
            print(f"   {year}: {count} треков")
        
        # 5. Дополнительные статистики
        durations = [track['duration'] for track in tracks if track['duration']]
        total_duration_ms = sum(durations)
        avg_duration_ms = statistics.mean(durations)
        
        # Переводим в часы/минуты/секунды
        total_hours = total_duration_ms // (1000 * 60 * 60)
        total_minutes = (total_duration_ms % (1000 * 60 * 60)) // (1000 * 60)
        avg_minutes = avg_duration_ms // (1000 * 60)
        avg_seconds = (avg_duration_ms % (1000 * 60)) // 1000
        print(f"   Общая длительность: {total_hours}ч {total_minutes}мин")
        print(f"   Средняя длительность трека: {avg_minutes:.0f}мин {avg_seconds:.0f}сек")
        print(f"   Количество артистов: {len(artist_tracks)}")

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
        if tracks:
            year_analysis = analyze_track_years(tracks)
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
                    a['artist_name'][:30] + "..."
                    if len(a['artist_name']) > 30
                    else a['artist_name'],
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
        print(f"{bcolors.FAIL} Ошибка при получении статистики: {e}{bcolors.ENDC}")


# Дополнительная функция для быстрого обзора
def get_quick_stats_summary(user_id=None):
    """Краткая сводка основных метрик пользователя."""
    if not user_id or user_id == -1:
        user_id = get_user_id_from_token()["id"]

    albums = get_user_like_albums(user_id=user_id)
    liked_playlists = get_user_like_playlists(user_id=user_id)
    own_playlists = get_user_playlists(user_id=user_id)
    artists = get_users_likes_artists(user_id=user_id)
    favorite_tracks = get_tracks_from_playlist(user_id=user_id, are_favourite=True)

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
