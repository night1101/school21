# MovieLens Analysis

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Tests](https://img.shields.io/badge/tests-35%20passed-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Учебный, но production-подобный проект: показывает, как анализировать данные на чистом Python
без `pandas` и `numpy`, работать с внешними API, кэшировать ответы и писать тесты.
Сделан как pet-project для портфолио.

Разбирает датасет [MovieLens](https://grouplens.org/datasets/movielens/) — оценки, фильмы,
теги и внешние метаданные (OMDb / TMDB) — и отвечает на вопросы вида
«какой фильм самый спорный», «кто снял больше всего фильмов»,
«какой фильм самый дорогой в минуту».

---

## Что демонстрирует проект

- **ООП:** наследование (`Users` ← `Movies`), инкапсуляция, разделение ответственности между 4 классами.
- **Работа с REST API:** OMDb и TMDB, объединение ответов двух источников, обработка ошибок, кэширование в JSON.
- **Парсинг CSV с экранированием кавычек** через regex-сплит (без сторонних библиотек).
- **Статистика без numpy/pandas:** среднее, медиана, дисперсия — реализованы вручную.
- **Тестирование:** `pytest`, 35+ кейсов на корректность типов, сортировок и граничных случаев.
- **Аналитический отчёт:** Jupyter-ноутбук с ASCII-визуализацией и выводами.

---

## Структура проекта

```
.
├── movielens_analysis.py     # основной модуль: Ratings, Tags, Movies, Links
├── movielens_report.ipynb    # аналитический отчёт с выводами
├── ratings.csv               # оценки пользователей (MovieLens)
├── movies.csv                # фильмы и жанры
├── tags.csv                  # теги пользователей
├── links.csv                 # соответствие movieId ↔ imdbId ↔ tmdbId
└── cache.json                # кэш ответов внешних API (создаётся автоматически)
```

---

## Требования

- Python 3.10+
- `requests`
- `pytest` (для тестов)
- `jupyter` (для ноутбука)

```bash
pip install requests pytest jupyter
```

---

## Быстрый старт

```python
from movielens_analysis import Ratings, Movies, Tags, Links

# Инициализация
ratings = Ratings("ratings.csv", "movies.csv")
movies  = Movies("movies.csv")
tags    = Tags("tags.csv")
links   = Links("links.csv", "movies.csv")

# Обёртки для подмножеств
ratings_movies = ratings.Movies(ratings.data)
ratings_users  = ratings.Users(ratings.data)

# Примеры
print(ratings_movies.top_by_genre("Drama", 10))
print(ratings_users.top_users_with_biggest_variance(10))
print(tags.most_popular(10))
print(links.top_directors(10))
```

---

## Описание классов

### `Ratings(file_path, movies_file_path)`

Читает оценки и подтягивает название и жанры фильма.

Вложенные классы:

- **`Movies`** — анализ по фильмам:
  - `dist_by_year()` — распределение оценок по годам.
  - `dist_by_rating()` — распределение по значению оценки.
  - `top_by_num_of_ratings(n)` — топ по количеству оценок.
  - `top_by_ratings(n, metric='average'|'median')` — топ по средней/медиане.
  - `top_by_genre(genre, n)` — топ фильмов в жанре.
  - `top_controversial(n)` — топ по дисперсии оценок.
- **`Users`** (наследует `Movies`):
  - `dist_by_num_of_ratings()` — активность пользователей.
  - `dist_by_rating(metric)` — распределение по средней/медиане.
  - `top_users_with_biggest_variance(n)` — пользователи с самым широким вкусом.

### `Movies(file_path)`

- `dist_by_release()` — фильмы по годам выпуска.
- `dist_by_genres()` — распределение по жанрам.
- `most_genres(n)` — фильмы с наибольшим числом жанров.

### `Tags(file_path, movies_file_path='movies.csv')`

- `most_popular(n)` — самые частые теги.
- `most_words(n)` — теги с максимумом слов.
- `longest(n)` — самые длинные теги.
- `most_words_and_longest(n)` — пересечение двух предыдущих.
- `tags_with(word)` — теги, содержащие подстроку.
- `most_tagged_movies(n)` — фильмы с наибольшим числом тегов.

### `Links(file_path, movies_file_path)`

- `get_imdb(list_of_movies, list_of_fields)` — данные с OMDb для списка фильмов.
- `tmdb_id(imdb_id)` — получить TMDB id по IMDb id.
- `top_directors(n)` — топ режиссёров по количеству фильмов.
- `most_expensive(n)` — топ по бюджету.
- `most_profitable(n)` — топ по (сборы − бюджет).
- `longest(n)` — топ по хронометражу.
- `top_cost_per_minute(n)` — топ по бюджету на минуту.
- `refresh_cache()` — принудительно обновить кэш API.

---

## Кэширование

Ответы OMDb и TMDB сохраняются в `cache.json`, чтобы не превышать лимиты запросов.
Удалите файл или вызовите `refresh_cache()`, чтобы получить свежие данные.

> ⚠️ **Безопасность.** API-ключи в текущей версии захардкожены. Перед публикацией
> вынесите их в переменные окружения (`.env`) и добавьте `cache.json` в `.gitignore`.

---

## Тесты

```bash
pytest movielens_analysis.py -v
```

Покрыты:

- корректность типов и сортировок для каждого метода;
- длина считанных данных (1000 записей);
- граничные случаи (`n <= 0`, неизвестные метрики).

---

## Пример вывода

```
ТОП-10 САМЫХ СПОРНЫХ ФИЛЬМОВ
 1. My Fair Lady (1964)                → дисперсия = 5.06
 2. Schindler's List (1993)            → дисперсия = 3.42
 3. Courage Under Fire (1996)          → дисперсия = 3.06
 ...

ТОП-10 САМЫХ ПРИБЫЛЬНЫХ ФИЛЬМОВ
 1. Jurassic Park (1993)               → $857,100,000
 2. E.T. the Extra-Terrestrial (1982)  → $786,807,407
 ...

ТОП-10 ФИЛЬМОВ ПО СТОИМОСТИ МИНУТЫ
 1. Waterworld (1995)                  → $1,296,296.30 в минуту
 2. Hunchback of Notre Dame, The (1996)→ $1,098,901.10 в минуту
```

---

## Roadmap

- [ ] Вынести `limit` в параметр конструктора вместо хардкода `if i >= 1000: break`
- [ ] Заменить линейный `get_movie_title` на предварительно построенный `dict` (убрать O(n²))
- [ ] Добавить `timeout` и retry-политику для `requests`
- [ ] Перенести API-ключи в переменные окружения (`.env` + `python-dotenv`)
- [ ] Заменить `except Exception` на конкретные типы исключений
- [ ] Покрыть `Links` моками HTTP-ответов (`responses` / `pytest-mock`)
- [ ] Добавить CI (GitHub Actions) с прогоном `pytest` на push

---

## Лицензия

MIT
