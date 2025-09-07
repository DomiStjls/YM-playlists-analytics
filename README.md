# YM-analytics

# Описание работы файла utils.py


## Утилитарные функции

### `get_token_from_env()`
Загружает токен Yandex Music из переменной окружения TOKEN.

### `is_available(owner)`
Проверяет, доступен ли контент (исключает официальные аккаунты Яндекса).

### `get_user_id_from_token(token=None)`
Получает ID пользователя и полное имя по токену.
**Возвращает:** `{"id": int, "full_name": str}`

### `write_data_to_txt(data, name_file="playlist.txt")`
Записывает список словарей в текстовый файл с разделителем ";".

### `write_data_to_csv(data, name_file="playlist.csv")`
Записывает список словарей в CSV файл с разделителем ";".

### `add_known_ids(known_ids)`
Добавляет известные ID пользователей в файл ids.txt для отслеживания.

## Функции получения данных

### `get_tracks_from_playlist(token=None, user_id=None, are_favorite=False, kind=None)`
Получает треки из плейлиста или избранного пользователя.
**Возвращает список словарей:**
```python
[{
    "title": str,           # Название трека
    "id": int,              # ID трека
    "duration": int,        # Длительность в миллисекундах
    "year": int,            # Год альбома, в который входить трек
    "genre": str,           # Жанр альбома, в который входить трек
    "artists": str,         # "Артист1 - ID1, Артист2 - ID2"
    "albums": str           # "Альбом1 - ID1, Альбом2 - ID2"
}]
```

### `get_user_playlists(token=None, user_id=None)`
Получает список плейлистов пользователя.
**Возвращает список словарей:**
```python
[{
    "playlist_uid": str,    # UID плейлиста
    "kind": int,            # ID плейлиста
    "track_count": int,     # Количество треков
    "playlist_title": str,  # Название плейлиста
    "playlist_duration": int # Длительность в миллисекундах
}]
```

### `get_user_like_playlists(token=None, user_id=None)`
Получает список плейлистов, которые лайкнул пользователь.
**Возвращает список словарей:**
```python
[{
    "owner_uid": int,       # ID владельца плейлиста
    "owner_name": str,      # Имя владельца плейлиста
    "playlist_uid": str,    # UID плейлиста
    "track_count": int,     # Количество треков
    "playlist_title": str,  # Название плейлиста
    "playlist_duration": int # Длительность в миллисекундах
}]
```

### `get_user_like_albums(token=None, user_id=None)`
Получает список альбомов, которые лайкнул пользователь.
**Возвращает список словарей:**
```python
[{
    "album_id": int,        # ID альбома
    "track_count": int,     # Количество треков в альбоме
    "album_title": str      # Название альбома
}]
```

### `get_users_likes_artists(token=None, user_id=None)`
Получает список артистов, которых лайкнул пользователь.
**Возвращает список словарей:**
```python
[{
    "artist_id": int,       # ID артиста
    "artist_name": str,     # Имя артиста
    "artist_genres": str,   # "Жанр1, Жанр2, Жанр3"
    "track_count": int      # Количество треков артиста
}]
```

## Примечания
- Все функции `get_*` возвращают `None` при отсутствии токена
- Токен можно получить по инструкции: https://yandex-music.readthedocs.io/en/main/token.html (самый простой и быстрый: https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781)
- Параметр `user_id` опционален для большинства функций (по умолчанию используется текущий пользователь)