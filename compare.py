import re
from collections import Counter
from datetime import timedelta


def parse_artists_from_string(artists_str):
    """Извлекает имена артистов из строки формата 'Artist1 - ID1, Artist2 - ID2'."""
    if not artists_str:
        return []
    artists = []
    for artist_part in artists_str.split(", "):
        if " - " in artist_part:
            artist_name = artist_part.rsplit(" - ", 1)[0]
            artists.append(artist_name.strip())
    return artists


def parse_albums_from_string(albums_str):
    """Извлекает названия альбомов из строки формата 'Album1 - ID1, Album2 - ID2'."""
    if not albums_str:
        return []
    albums = []
    for album_part in albums_str.split(", "):
        if " - " in album_part:
            album_name = album_part.rsplit(" - ", 1)[0]
            albums.append(album_name.strip())
    return albums


def extract_release_year_from_title(title):
    """Пытается извлечь год из названия трека (примерный алгоритм)."""
    # Ищем 4-значные числа, которые могут быть годами (1900-2099)
    years = re.findall(r"\b(19\d{2}|20\d{2})\b", title)
    return int(years[0]) if years else None


def calculate_duration_stats(tracks):
    """Вычисляет статистику по длительности треков."""
    if not tracks:
        return {"avg": 0, "median": 0, "min": 0, "max": 0}

    durations = [track.get("duration", 0) for track in tracks if track.get("duration")]
    if not durations:
        return {"avg": 0, "median": 0, "min": 0, "max": 0}

    durations.sort()
    n = len(durations)
    median = (
        durations[n // 2]
        if n % 2 == 1
        else (durations[n // 2 - 1] + durations[n // 2]) // 2
    )

    return {
        "avg": sum(durations) // len(durations),
        "median": median,
        "min": min(durations),
        "max": max(durations),
    }


def analyze_title_patterns(tracks):
    """Анализирует паттерны в названиях треков."""
    if not tracks:
        return {}

    titles = [track.get("title", "").lower() for track in tracks]

    # Анализ языков (упрощенный)
    cyrillic_count = sum(
        1
        for title in titles
        if any(ord(c) >= 0x0400 and ord(c) <= 0x04FF for c in title)
    )
    latin_count = len(titles) - cyrillic_count

    # Анализ специальных символов и скобок
    with_brackets = sum(1 for title in titles if "(" in title or "[" in title)
    with_feat = sum(1 for title in titles if "feat" in title or "ft." in title)

    # Анализ длины названий
    avg_title_length = (
        sum(len(title) for title in titles) / len(titles) if titles else 0
    )

    return {
        "cyrillic_ratio": cyrillic_count / len(titles) if titles else 0,
        "latin_ratio": latin_count / len(titles) if titles else 0,
        "brackets_ratio": with_brackets / len(titles) if titles else 0,
        "featuring_ratio": with_feat / len(titles) if titles else 0,
        "avg_title_length": round(avg_title_length, 1),
    }


def calculate_diversity_index(items_list):
    """Вычисляет индекс разнообразия (Simpson's Diversity Index)."""
    if not items_list:
        return 0

    counter = Counter(items_list)
    total = len(items_list)

    # Simpson's Diversity Index: 1 - Σ(ni/N)²
    simpson_index = 1 - sum((count / total) ** 2 for count in counter.values())
    return round(simpson_index, 3)


def compare_playlists_enhanced(
    playlist1_tracks,
    playlist2_tracks,
    playlist1_name="Плейлист 1",
    playlist2_name="Плейлист 2",
):
    """
    Расширенное сравнение двух плейлистов с детальной аналитикой.

    Parameters
    ----------
    playlist1_tracks : list
        Список треков первого плейлиста (результат get_tracks_from_playlist)
    playlist2_tracks : list
        Список треков второго плейлиста
    playlist1_name : str
        Название первого плейлиста
    playlist2_name : str
        Название второго плейлиста

    Returns
    -------
    dict
        Детальная аналитика сравнения плейлистов
    """
    # print(len(playlist1_tracks), len(playlist2_tracks))
    if not playlist1_tracks or not playlist2_tracks:
        return {"error": "Один или оба плейлиста пусты"}

    # Базовые данные
    p1_tracks = set(
        (track.get("title", ""), track.get("id", "")) for track in playlist1_tracks
    )
    p2_tracks = set(
        (track.get("title", ""), track.get("id", "")) for track in playlist2_tracks
    )

    # Общие треки
    common_tracks = p1_tracks & p2_tracks

    # Извлекаем артистов
    p1_artists = []
    p2_artists = []
    for track in playlist1_tracks:
        p1_artists.extend(parse_artists_from_string(track.get("artists", "")))
    for track in playlist2_tracks:
        p2_artists.extend(parse_artists_from_string(track.get("artists", "")))

    p1_unique_artists = set(p1_artists)
    p2_unique_artists = set(p2_artists)
    common_artists = p1_unique_artists & p2_unique_artists

    # Извлекаем альбомы
    p1_albums = []
    p2_albums = []
    for track in playlist1_tracks:
        p1_albums.extend(parse_albums_from_string(track.get("albums", "")))
    for track in playlist2_tracks:
        p2_albums.extend(parse_albums_from_string(track.get("albums", "")))

    p1_unique_albums = set(p1_albums)
    p2_unique_albums = set(p2_albums)
    common_albums = p1_unique_albums & p2_unique_albums

    # 1. Коэффициент схожести Жаккара
    jaccard_tracks = (
        len(common_tracks) / len(p1_tracks | p2_tracks)
        if (p1_tracks | p2_tracks)
        else 0
    )
    jaccard_artists = (
        len(common_artists) / len(p1_unique_artists | p2_unique_artists)
        if (p1_unique_artists | p2_unique_artists)
        else 0
    )

    # 2. Статистика по длительности треков
    p1_duration_stats = calculate_duration_stats(playlist1_tracks)
    p2_duration_stats = calculate_duration_stats(playlist2_tracks)

    total_duration_p1 = sum(track.get("duration", 0) for track in playlist1_tracks)
    total_duration_p2 = sum(track.get("duration", 0) for track in playlist2_tracks)

    # 3. Анализ разнообразия артистов
    p1_artist_diversity = calculate_diversity_index(p1_artists)
    p2_artist_diversity = calculate_diversity_index(p2_artists)

    # 4. Анализ паттернов названий
    p1_title_patterns = analyze_title_patterns(playlist1_tracks)
    p2_title_patterns = analyze_title_patterns(playlist2_tracks)

    # 5. Топ артисты в каждом плейлисте
    p1_artist_counts = Counter(p1_artists)
    p2_artist_counts = Counter(p2_artists)

    # 6. Коэффициент "коллаборативности" (треки с несколькими артистами)
    p1_collab_ratio = sum(
        1
        for track in playlist1_tracks
        if len(parse_artists_from_string(track.get("artists", ""))) > 1
    ) / len(playlist1_tracks)
    p2_collab_ratio = sum(
        1
        for track in playlist2_tracks
        if len(parse_artists_from_string(track.get("artists", ""))) > 1
    ) / len(playlist2_tracks)

    # 7. Анализ "раритетности" (уникальность артистов между плейлистами)
    p1_exclusive_artists = p1_unique_artists - p2_unique_artists
    p2_exclusive_artists = p2_unique_artists - p1_unique_artists

    # Формируем результат
    result = {
        "playlist_names": {"playlist1": playlist1_name, "playlist2": playlist2_name},
        "basic_stats": {
            "playlist1_track_count": len(playlist1_tracks),
            "playlist2_track_count": len(playlist2_tracks),
            "common_tracks_count": len(common_tracks),
            "common_artists_count": len(common_artists),
            "common_albums_count": len(common_albums),
        },
        "similarity_scores": {
            "track_jaccard_similarity": round(jaccard_tracks, 3),
            "artist_jaccard_similarity": round(jaccard_artists, 3),
            "overall_similarity_score": round(
                (jaccard_tracks + jaccard_artists) / 2, 3
            ),
        },
        "duration_analysis": {
            "playlist1": {
                "total_duration_ms": total_duration_p1,
                "total_duration_formatted": str(
                    timedelta(milliseconds=total_duration_p1)
                ).split(".")[0],
                "avg_track_duration_ms": p1_duration_stats["avg"],
                "median_duration_ms": p1_duration_stats["median"],
                "shortest_track_ms": p1_duration_stats["min"],
                "longest_track_ms": p1_duration_stats["max"],
            },
            "playlist2": {
                "total_duration_ms": total_duration_p2,
                "total_duration_formatted": str(
                    timedelta(milliseconds=total_duration_p2)
                ).split(".")[0],
                "avg_track_duration_ms": p2_duration_stats["avg"],
                "median_duration_ms": p2_duration_stats["median"],
                "shortest_track_ms": p2_duration_stats["min"],
                "longest_track_ms": p2_duration_stats["max"],
            },
            "duration_similarity": 1
            - abs(p1_duration_stats["avg"] - p2_duration_stats["avg"])
            / max(p1_duration_stats["avg"], p2_duration_stats["avg"])
            if max(p1_duration_stats["avg"], p2_duration_stats["avg"]) > 0
            else 1,
        },
        "diversity_analysis": {
            "playlist1_artist_diversity": p1_artist_diversity,
            "playlist2_artist_diversity": p2_artist_diversity,
            "diversity_difference": abs(p1_artist_diversity - p2_artist_diversity),
            "more_diverse_playlist": playlist1_name
            if p1_artist_diversity > p2_artist_diversity
            else playlist2_name,
        },
        "collaboration_analysis": {
            "playlist1_collab_ratio": round(p1_collab_ratio, 3),
            "playlist2_collab_ratio": round(p2_collab_ratio, 3),
            "collab_preference_similarity": 1 - abs(p1_collab_ratio - p2_collab_ratio),
        },
        "language_and_style": {
            "playlist1_patterns": p1_title_patterns,
            "playlist2_patterns": p2_title_patterns,
            "language_similarity": 1
            - abs(
                p1_title_patterns.get("cyrillic_ratio", 0)
                - p2_title_patterns.get("cyrillic_ratio", 0)
            ),
        },
        "top_artists": {
            "playlist1_top5": [
                {"artist": artist, "count": count}
                for artist, count in p1_artist_counts.most_common(5)
            ],
            "playlist2_top5": [
                {"artist": artist, "count": count}
                for artist, count in p2_artist_counts.most_common(5)
            ],
        },
        "uniqueness_analysis": {
            "playlist1_exclusive_artists_count": len(p1_exclusive_artists),
            "playlist2_exclusive_artists_count": len(p2_exclusive_artists),
            "playlist1_exclusivity_ratio": len(p1_exclusive_artists)
            / len(p1_unique_artists)
            if p1_unique_artists
            else 0,
            "playlist2_exclusivity_ratio": len(p2_exclusive_artists)
            / len(p2_unique_artists)
            if p2_unique_artists
            else 0,
            "most_unique_playlist": playlist1_name
            if len(p1_exclusive_artists) > len(p2_exclusive_artists)
            else playlist2_name,
        },
        "recommendations": [],
    }

    # Генерируем рекомендации на основе анализа
    recommendations = []

    if jaccard_tracks > 0.03:
        recommendations.append(
            "Высокая схожесть треков! Возможно, у вас похожие музыкальные вкусы."
        )
    elif jaccard_tracks < 0.01:
        recommendations.append(
            "Плейлисты очень разные - отличная возможность открыть новую музыку!"
        )

    if jaccard_artists > 0.3:
        recommendations.append(
            "Много общих артистов - попробуйте обменяться другими плейлистами!"
        )

    if abs(p1_artist_diversity - p2_artist_diversity) > 0.3:
        more_diverse = (
            playlist1_name
            if p1_artist_diversity > p2_artist_diversity
            else playlist2_name
        )
        recommendations.append(f"{more_diverse} более разнообразен по артистам.")

    if abs(p1_collab_ratio - p2_collab_ratio) > 0.3:
        collab_lover = (
            playlist1_name if p1_collab_ratio > p2_collab_ratio else playlist2_name
        )
        recommendations.append(
            f"{collab_lover} содержит больше коллабораций между артистами."
        )

    duration_diff = abs(total_duration_p1 - total_duration_p2) / 1000 / 60  # в минутах
    if duration_diff > 60:
        longer = (
            playlist1_name if total_duration_p1 > total_duration_p2 else playlist2_name
        )
        recommendations.append(
            f"{longer} значительно длиннее - подходит для долгого прослушивания."
        )

    result["recommendations"] = recommendations

    return result


def print_comparison_report(comparison_result):
    """Выводит красиво отформатированный отчет сравнения."""
    if "error" in comparison_result:
        print(f" Ошибка: {comparison_result['error']}")
        return

    r = comparison_result
    p1_name = r["playlist_names"]["playlist1"]
    p2_name = r["playlist_names"]["playlist2"]

    print("=" * 80)
    print(f"СРАВНЕНИЕ ПЛЕЙЛИСТОВ: {p1_name} vs {p2_name}")
    print("=" * 80)

    # Основные показатели
    print("\nОСНОВНАЯ СТАТИСТИКА:")
    print(f"├─ {p1_name}: {r['basic_stats']['playlist1_track_count']} треков")
    print(f"├─ {p2_name}: {r['basic_stats']['playlist2_track_count']} треков")
    print(f"├─ Общие треки: {r['basic_stats']['common_tracks_count']}")
    print(f"└─ Общие артисты: {r['basic_stats']['common_artists_count']}")

    # Схожесть
    print(f"\n КОЭФФИЦИЕНТЫ СХОЖЕСТИ:")
    print(
        f"├─ Схожесть по трекам: {r['similarity_scores']['track_jaccard_similarity']:.1%}"
    )
    print(
        f"├─ Схожесть по артистам: {r['similarity_scores']['artist_jaccard_similarity']:.1%}"
    )
    print(
        f"└─ Общая схожесть: {r['similarity_scores']['overall_similarity_score']:.1%}"
    )

    # Длительность
    print(f"\nАНАЛИЗ ДЛИТЕЛЬНОСТИ:")
    p1_dur = r["duration_analysis"]["playlist1"]
    p2_dur = r["duration_analysis"]["playlist2"]
    print(
        f"├─ {p1_name}: {p1_dur['total_duration_formatted']} (сред. {p1_dur['avg_track_duration_ms'] // 1000 // 60}:{(p1_dur['avg_track_duration_ms'] // 1000) % 60:02d})"
    )
    print(
        f"└─ {p2_name}: {p2_dur['total_duration_formatted']} (сред. {p2_dur['avg_track_duration_ms'] // 1000 // 60}:{(p2_dur['avg_track_duration_ms'] // 1000) % 60:02d})"
    )

    # Разнообразие
    print(f"\nРАЗНООБРАЗИЕ АРТИСТОВ:")
    div = r["diversity_analysis"]
    print(f"├─ {p1_name}: {div['playlist1_artist_diversity']:.3f}")
    print(f"├─ {p2_name}: {div['playlist2_artist_diversity']:.3f}")
    print(f"└─ Более разнообразный: {div['more_diverse_playlist']}")

    # Топ артисты
    print(f"\n ТОП-5 АРТИСТОВ:")
    print(f"  {p1_name}:")
    for i, artist in enumerate(r["top_artists"]["playlist1_top5"], 1):
        print(f"    {i}. {artist['artist']} ({artist['count']} треков)")
    print(f"  {p2_name}:")
    for i, artist in enumerate(r["top_artists"]["playlist2_top5"], 1):
        print(f"    {i}. {artist['artist']} ({artist['count']} треков)")

    # Рекомендации
    if r["recommendations"]:
        print(f"\nРЕКОМЕНДАЦИИ:")
        for rec in r["recommendations"]:
            print(f"  {rec}")

    print("=" * 80)
