import json
from collections import Counter
import functools
from datetime import datetime, time
import re
from urllib import response
import requests
import pytest

class Ratings:
    def __init__(self, file_path, movies_file_path):
        self.file_path = file_path
        self.movies_file_path = movies_file_path
        self.data = self.read_file()

    def read_file(self):
        pattern = r',(?=(?:[^"]*"[^"]*")*[^"]*$)'
        movies = {}
        with open(self.movies_file_path, 'r', encoding='utf-8') as f:
            next(f)
            for line in f:
                fields = [field.strip('"') for field in re.split(pattern, line.strip())]
                movies[fields[0]] = (fields[1], fields[2])
        data = []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            next(f)
            for i, line in enumerate(f):
                if i >= 1000:
                    break
                row = line.strip().split(',')
                row.append(movies.get(row[1], (None, None))[0])
                row.append(movies.get(row[1], (None, None))[1])
                data.append(row)
        return data
    
    class Movies:
        def __init__(self, data):
            self.data = data

        def dist_by_year(self):
            try:
                d = {}
                for timestamp in self.data:
                    year = datetime.fromtimestamp(int(timestamp[3])).year
                    d[year] = d.get(year, 0) + 1

                ratings_by_year = dict(sorted(d.items(), key=lambda v: v[0]))
                return ratings_by_year
            except Exception:
                return None
        
        #НОВЫй МЕТОД!!!! 
        def top_by_genre(self, genre, n):
            try:
                d = {}
                for movie in self.data:
                    if movie[5] and genre in movie[5]:
                        d[movie[4]] = self.average_counter(movie[1], 'movie')
                return dict(sorted(d.items(), key=lambda v: v[1], reverse=True)[:n])
            except Exception:
                return None

        def dist_by_rating(self):
            try:
                d = {}
                for rating in self.data:
                    rat = float(rating[2])
                    d[rat] = d.get(rat, 0) + 1
                ratings_distribution = dict(sorted(d.items(), key=lambda v: v[0]))
                return ratings_distribution
            except Exception:
                return None

        def top_by_num_of_ratings(self, n):
            try:
                if int(n) <= 0:
                    return None
                d = {}
                for movie in self.data:
                    title = self.get_movie_title(movie[1])
                    d[title] = d.get(title, 0) + 1
                top_movies = dict(sorted(d.items(), key=lambda v: v[1], reverse=True)[:n])
                return top_movies
            except Exception:
                return None

        def get_movie_title(self, movie_id):
            for row in self.data:
                if row[1] == movie_id:
                    return row[4]
            return None

        def top_by_ratings(self, n, metric='average'):
            try:
                n = int(n)
                if n <= 0:
                    return None
                if metric not in ['average', 'median']:
                    return None

                method = self.average_counter if metric == 'average' else self.median_counter
                d = {self.get_movie_title(movie[1]) : method(movie[1], 'movie') for movie in self.data if self.get_movie_title(movie[1])}
                top_movies = dict(sorted(d.items(), key=lambda v: v[1], reverse=True)[:n])

                return top_movies
            except Exception:
                return None

        def average_counter(self, id, metric):
            try:
                if metric not in ['movie', 'user']:
                        return None

                index = 1 if metric == 'movie' else 0
                ratings = [float(movie[2]) for movie in self.data if movie[index] == id]
                return round(sum(ratings) / len(ratings), 2) if len(ratings) > 0 else 0
            except Exception:
                return None

        def median_counter(self, id, metric):
            try:
                if metric not in ['movie', 'user']:
                    return None

                index = 1 if metric == 'movie' else 0
                ratings = [float(movie[2]) for movie in self.data if movie[index] == id]
                if not ratings:
                    return None

                ratings.sort()
                mid = len(ratings) // 2
                if len(ratings) % 2 == 1:
                    return round(ratings[mid], 2)
                else:
                    return round((ratings[mid - 1] + ratings[mid]) / 2, 2)
            except Exception:
                return None

        def top_controversial(self, n):
            try:
                n = int(n)
                if n <= 0:
                    return None

                d = {self.get_movie_title(movie[1]) : self.variance_counter(movie[1], 'movie') for movie in self.data if self.get_movie_title(movie[1])}
                top_movies = dict(sorted(d.items(), key=lambda v: v[1], reverse=True)[:n])
                return top_movies
            except Exception:
                return None

        def variance_counter(self, id, metric):
            try:
                if metric not in ['movie', 'user']:
                    return None

                index = 1 if metric == 'movie' else 0
                ratings = [float(movie[2]) for movie in self.data if movie[index] == id]

                if not ratings:
                    return None

                mean = sum(ratings) / len(ratings)
                variance = sum((x - mean) ** 2 for x in ratings) / len(ratings)
                return round(variance, 2)
            except Exception:
                return None

    class Users(Movies):
        """
        In this class, three methods should work.
        The 1st returns the distribution of users by the number of ratings made by them.
        The 2nd returns the distribution of users by average or median ratings made by them.
        The 3rd returns top-n users with the biggest variance of their ratings.
     Inherit from the class Movies. Several methods are similar to the methods from it.
        """
        def dist_by_num_of_ratings(self):
            try:
                d = {}
                for users in self.data:
                    d[users[0]] = d.get(users[0], 0) + 1
                return dict(sorted(d.items(), key=lambda v: v[1], reverse=True))
            except Exception:
                return None

        def dist_by_rating(self, metric):
            try:
                if metric not in ['average', 'median']:
                    return None
                d = {}
                user_ids = set(user[0] for user in self.data)
                method = self.average_counter if metric == 'average' else self.median_counter
                for user_id in user_ids:
                    d[user_id] = method(user_id, 'user')
                return dict(sorted(d.items(), key=lambda v: v[1], reverse=True ))
            except Exception:
                return None

        def top_users_with_biggest_variance(self, n):
            try:
                n = int(n)
                if n <= 0:
                    return None
                user_ids = set(user[0] for user in self.data)
                d = {user_id: self.variance_counter(user_id, 'user') for user_id in user_ids}
                top_users = dict(sorted(d.items(), key=lambda v: v[1], reverse=True)[:n])
                return top_users
            except Exception:
                return None

class Tags:
    def __init__(self, file_path, movies_file_path='movies.csv'):
        self.file_path = file_path
        self.movies_file_path = movies_file_path
        self.data = self.read_file()
        

    def read_file(self):
        pattern = r',(?=(?:[^"]*"[^"]*")*[^"]*$)'
        movies = {}
        with open(self.movies_file_path, 'r', encoding='utf-8') as f:
            next(f)
            for line in f:
                fields = [field.strip('"') for field in re.split(pattern, line.strip())]
                movies[fields[0]] = fields[1]
        data = []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            next(f)
            for i, line in enumerate(f):
                if i >= 1000:
                    break
                row = line.strip().split(',')
                row.append(movies.get(row[1]))
                data.append(row)
        return data
    
    #новый метод 
    def most_tagged_movies(self, n):
        try:
            d = {}
            for tag in self.data:
                d[tag[4]] = d.get(tag[4], 0) + 1
            top_movies = dict(sorted(d.items(), key=lambda v: v[1], reverse=True)[:n])
            return top_movies
        except Exception:
            return None

    def most_words(self, n):
        try:
            tags = {tag[2] : len(tag[2].split()) for tag in self.data}
            ls = sorted(tags.items(), key=lambda item: item[1], reverse=True)
            big_tags = dict(ls[:n])
            return big_tags
        except Exception:
            return None

    def longest(self, n):
        try:
            tags = {tag[2] : len(tag[2]) for tag in self.data}
            big_tags = sorted(tags.items(), key=lambda item: item[1], reverse=True)
            return [t[0] for t in big_tags[:n]]
        except Exception:
            return None

    def most_words_and_longest(self, n):
        try:
            most_words = self.most_words(n)
            longest = self.longest(n)
            big_tags = list(set(most_words.keys()) & set(longest))
            return big_tags
        except Exception:
            return None

    def most_popular(self, n):
        d = Counter(tag[2] for tag in self.data)
        popular_tags = dict(d.most_common(n))
        return popular_tags

    def tags_with(self, word):
        return sorted(set([tag[2] for tag in self.data if word in tag[2]]))

class Movies:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self.read_file()

    def read_file(self):
        pattern = r',(?=(?:[^"]*"[^"]*")*[^"]*$)'
        data = []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            next(f)
            for i, line in enumerate(f):
                if i >= 1000:
                    break
                line = line.strip()
                fields = [field.strip('"') for field in re.split(pattern, line)]
                fields[2] = fields[2].split('|')
                data.append(fields)
        return data

    def dist_by_release(self):
        try:
            d = {}
            for movie in self.data:
                title = re.search(r'\((\d{4})\)', movie[1])
                year = title.group(1)
                d[year] = d.get(year, 0) + 1
            release_years = dict(sorted(d.items(), key=lambda v: v[1], reverse=True))
            return release_years
        except Exception:
            return None

    def dist_by_genres(self):
        try:
            d = {}
            for genre in self.data:
                for g in genre[2]:
                    d[g] = d.get(g, 0) + 1
            genres = dict(sorted(d.items(), key=lambda v: v[1], reverse=True))
            return genres
        except Exception:
            return None

    def most_genres(self, n):
        try:
            d = {movie[1] : len(movie[2]) for movie in self.data}
            movies = dict(sorted(d.items(), key=lambda v: v[1], reverse=True)[:n])
            return movies
        except Exception:
            return None

class Links:
    def __init__(self, file_path, movies_file_path):
        self.file_path = file_path
        self.movies_file_path = movies_file_path
        self.data = self.read_file()
        self.data_cache = self.load_cache()

    def read_file(self):
        pattern = r',(?=(?:[^"]*"[^"]*")*[^"]*$)'
        movies = {}
        with open(self.movies_file_path, 'r', encoding='utf-8') as f:
            next(f)
            for line in f:
                fields = [field.strip('"') for field in re.split(pattern, line.strip())]
                movies[fields[0]] = fields[1]
        data = []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            next(f)
            for i, line in enumerate(f):
                if i >= 1000:
                    break
                row = line.strip().split(',')
                row.append(movies.get(row[0]))
                data.append(row)
        return data

    def load_cache(self):
        try:
            with open('cache.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return self.fetch_cache()

    def fetch_cache(self):
        dict_cache = {}
        try:
            for movie in self.data:
                response = requests.get(f'http://www.omdbapi.com/?i=tt{movie[1]}&apikey=6d4e4e3d')
                dataimdb = json.loads(response.text)
                response = requests.get(f'https://api.themoviedb.org/3/movie/{movie[2]}?api_key=a1f1838d4050cad6edef1ae8e6c2beb0')
                datatmdb = json.loads(response.text)
                dict_cache[movie[1]] = {**dataimdb, **datatmdb}
                with open('cache.json', 'w', encoding='utf-8') as f:
                    json.dump(dict_cache, f)
            return dict_cache   
        except Exception:
            return None

    def _save_cache(self):
        with open('cache.json', 'w', encoding='utf-8') as f:
            json.dump(self.data_cache, f)

    def refresh_cache(self):
        self.data_cache = self.fetch_cache()
        self._save_cache()

    def get_imdb(self, list_of_movies, list_of_fields): # не готов
        """
        The method returns a list of lists [movieId, field1, field2, field3, ...] for the list of movies given as the argument (movieId).
        For example, [movieId, Director, Budget, Cumulative Worldwide Gross, Runtime].
        The values should be parsed from the IMDB webpages of the movies.
        Sort it by movieId descendingly.
        """
        try:
            ls = []
            for idmovie in list_of_movies:
                if idmovie in self.data_cache:
                    ls.append([idmovie] + [self.data_cache[idmovie].get(field, 'N/A') for field in list_of_fields])
                else:
                    response = requests.get(f'http://www.omdbapi.com/?i=tt{idmovie}&apikey=6d4e4e3d')
                    dataimdb = json.loads(response.text)
                    listinlist = [idmovie]
                    for field in list_of_fields:
                        datafield = dataimdb.get(field, 'N/A')
                        if datafield == 'N/A':
                            tmdb_id = self.tmdb_id(idmovie)
                            if tmdb_id:
                                response = requests.get(f'https://api.themoviedb.org/3/movie/{tmdb_id}?api_key=a1f1838d4050cad6edef1ae8e6c2beb0')
                                datatmdb = json.loads(response.text)
                                self.data_cache[idmovie] = {**dataimdb, **datatmdb}
                                self._save_cache()
                                datafield = datatmdb.get(field.lower(), 'N/A')
                        listinlist.append(datafield)
                    ls.append(listinlist)
            sorted_ls = sorted(ls, key=lambda x: int(x[0]), reverse=True)
            return sorted_ls
        except Exception:
            return None

    def tmdb_id(self, imdb_id):
        with open('links.csv', 'r', encoding='utf-8') as f:
            next(f)
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 3 and parts[1] == imdb_id:
                    return parts[2]
            return None

    def top_directors(self, n):
        """
        The method returns a dict with top-n directors where the keys are directors and
        the values are numbers of movies created by them. Sort it by numbers descendingly.
        """
        directors = {}
        for movie in self.data:
            if movie[1] in self.data_cache:
                director = self.data_cache[movie[1]].get('Director', 'N/A')
                if director != 'N/A':
                    directors[director] = directors.get(director, 0) + 1
            else:
                response = requests.get(f'http://www.omdbapi.com/?i=tt{movie[1]}&apikey=6d4e4e3d')
                dataimdb = json.loads(response.text)
                response = requests.get(f'https://api.themoviedb.org/3/movie/{movie[2]}?api_key=a1f1838d4050cad6edef1ae8e6c2beb0')
                datatmdb = json.loads(response.text)
                self.data_cache[movie[1]] = {**dataimdb, **datatmdb}
                self._save_cache()
                director = dataimdb.get('Director', 'N/A')
                if director != 'N/A':
                    directors[director] = directors.get(director, 0) + 1
        d = dict(sorted(directors.items(), key = lambda v: v[1], reverse=True)[:n])
        return d

    def most_expensive(self, n):
        """
        The method returns a dict with top-n movies where the keys are movie titles and
        the values are their budgets. Sort it by budgets descendingly.
        """
        budgets = {}
        for movie in self.data:
            title = movie[3]
            if title is None:
                continue
            if movie[1] in self.data_cache:
                budget = self.data_cache[movie[1]].get('budget', 0)
            else:
                response = requests.get(f'http://www.omdbapi.com/?i=tt{movie[1]}&apikey=6d4e4e3d')
                dataimdb = json.loads(response.text)
                response = requests.get(f'https://api.themoviedb.org/3/movie/{movie[2]}?api_key=a1f1838d4050cad6edef1ae8e6c2beb0')
                datatmdb = json.loads(response.text)
                self.data_cache[movie[1]] = {**dataimdb, **datatmdb}
                self._save_cache()
                budget = datatmdb.get('budget', 0)
            if budget:
                budgets[title] = budget
        budgets = dict(sorted(budgets.items(), key=lambda v: v[1], reverse=True)[:n])
        return budgets

    def most_profitable(self, n):
        """
        The method returns a dict with top-n movies where the keys are movie titles and
        the values are the difference between cumulative worldwide gross and budget.
     Sort it by the difference descendingly.
        """
        profits = {}
        for movie in self.data:
            title = movie[3]
            if title is None:
                continue
            if movie[1] in self.data_cache:
                budget = self.data_cache[movie[1]].get('budget', 0)
                revenue = self.data_cache[movie[1]].get('revenue', 0)
            else:
                response = requests.get(f'http://www.omdbapi.com/?i=tt{movie[1]}&apikey=6d4e4e3d')
                dataimdb = json.loads(response.text)
                response = requests.get(f'https://api.themoviedb.org/3/movie/{movie[2]}?api_key=a1f1838d4050cad6edef1ae8e6c2beb0')
                datatmdb = json.loads(response.text)
                self.data_cache[movie[1]] = {**dataimdb, **datatmdb}
                self._save_cache()
                budget = datatmdb.get('budget', 0)
                revenue = datatmdb.get('revenue', 0)
            if budget and revenue:
                profits[title] = revenue - budget
        profits = dict(sorted(profits.items(), key=lambda v: v[1], reverse=True)[:n])
        return profits

    def longest(self, n):
        """
        The method returns a dict with top-n movies where the keys are movie titles and
        the values are their runtime. If there are more than one version – choose any.
     Sort it by runtime descendingly.
        """
        runtimes = {}
        for movie in self.data:
            title = movie[3]
            if title is None:
                continue
            if movie[1] in self.data_cache:
                runtime_str = self.data_cache[movie[1]].get('Runtime', 'N/A')
            else:
                response = requests.get(f'http://www.omdbapi.com/?i=tt{movie[1]}&apikey=6d4e4e3d')
                dataimdb = json.loads(response.text)
                response = requests.get(f'https://api.themoviedb.org/3/movie/{movie[2]}?api_key=a1f1838d4050cad6edef1ae8e6c2beb0')
                datatmdb = json.loads(response.text)
                self.data_cache[movie[1]] = {**dataimdb, **datatmdb}
                self._save_cache()
                runtime_str = dataimdb.get('Runtime', 'N/A')
            if runtime_str != 'N/A':
                match = re.search(r'\d+', str(runtime_str))
                if match:
                    runtimes[title] = int(match.group())
        d = dict(sorted(runtimes.items(), key=lambda v: v[1], reverse=True)[:n])
        return d

    def top_cost_per_minute(self, n):
        """
        The method returns a dict with top-n movies where the keys are movie titles and
the values are the budgets divided by their runtime. The budgets can be in different currencies – do not pay attention to it.
     The values should be rounded to 2 decimals. Sort it by the division descendingly.
        """
        costs = {}
        for movie in self.data:
            title = movie[3]
            if title is None:
                continue
            if movie[1] in self.data_cache:
                budget = self.data_cache[movie[1]].get('budget', None)
                runtime_str = self.data_cache[movie[1]].get('Runtime', None)
            else:
                response = requests.get(f'http://www.omdbapi.com/?i=tt{movie[1]}&apikey=6d4e4e3d')
                dataimdb = json.loads(response.text)
                response = requests.get(f'https://api.themoviedb.org/3/movie/{movie[2]}?api_key=a1f1838d4050cad6edef1ae8e6c2beb0')
                datatmdb = json.loads(response.text)
                self.data_cache[movie[1]] = {**dataimdb, **datatmdb}
                self._save_cache()
                budget = datatmdb.get('budget', None)
                runtime_str = dataimdb.get('Runtime', None)
            if budget and runtime_str:
                match = re.search(r'\d+', str(runtime_str))
                if match:
                    runtime = int(match.group())
                    if runtime > 0:
                        costs[title] = round(budget / runtime, 2)
        return dict(sorted(costs.items(), key=lambda v: v[1], reverse=True)[:n])

class Test:
    #ratings
    def test_ratings_init(self):
        ans = Ratings("ratings.csv", "movies.csv")
        assert isinstance(ans.data, list)
        assert len(ans.data) == 1000

    def test_ratings_movies_dist_by_year(self):
        ratings = Ratings("ratings.csv", "movies.csv")
        ratings_movies = ratings.Movies(ratings.data)
        ans = ratings_movies.dist_by_year()
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, int)
            assert isinstance(value, int)
        keys = list(ans.keys())
        assert keys == sorted(keys)

    #bonus test
    def test_ratings_movies_top_by_genre(self):
        ratings = Ratings("ratings.csv", "movies.csv")
        ratings_movies = ratings.Movies(ratings.data)
        ans = ratings_movies.top_by_genre('Comedy', 5)
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, float)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

    def test_ratings_movies_dist_by_rating(self):
        ratings = Ratings("ratings.csv", "movies.csv")
        ratings_movies = ratings.Movies(ratings.data)
        ans = ratings_movies.dist_by_rating()
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, float)
            assert isinstance(value, int)
        keys = list(ans.keys())
        assert keys == sorted(keys)

    def test_ratings_movies_top_by_num_of_ratings(self):
        ratings = Ratings("ratings.csv", "movies.csv")
        ratings_movies = ratings.Movies(ratings.data)
        ans = ratings_movies.top_by_num_of_ratings(5)
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

    def test_ratings_movies_get_movie_title(self):
        ratings = Ratings("ratings.csv", "movies.csv")
        ratings_movies = ratings.Movies(ratings.data)
        ans = ratings_movies.get_movie_title('2')
        assert isinstance(ans, str)

    def test_ratings_movies_top_by_ratings(self):
        ratings = Ratings("ratings.csv", "movies.csv")
        ratings_movies = ratings.Movies(ratings.data)
        ans = ratings_movies.top_by_ratings(5)
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, float)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

    def test_ratings_movies_average_counter(self):
        ratings = Ratings("ratings.csv", "movies.csv")
        ratings_movies = ratings.Movies(ratings.data)
        ans = ratings_movies.average_counter('2', 'movie')
        assert isinstance(ans, float)

    def test_ratings_movies_median_counter(self):
        ratings = Ratings("ratings.csv", "movies.csv")
        ratings_movies = ratings.Movies(ratings.data)
        ans = ratings_movies.median_counter('2', 'movie')
        assert isinstance(ans, float)

    def test_ratings_movies_top_controversial(self):
        ratings = Ratings("ratings.csv", "movies.csv")
        ratings_movies = ratings.Movies(ratings.data)
        ans = ratings_movies.top_controversial(5)
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, float)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

    def test_ratings_movies_variance_counter(self):
        ratings = Ratings("ratings.csv", "movies.csv")
        ratings_movies = ratings.Movies(ratings.data)
        ans = ratings_movies.variance_counter('2', 'movie')
        assert isinstance(ans, float)

    def test_ratings_users_dist_by_num_of_ratings(self):
        ratings = Ratings("ratings.csv", "movies.csv")
        ratings_users = Ratings.Users(ratings.data)
        ans = ratings_users.dist_by_num_of_ratings()
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

    def test_ratings_users_dist_by_rating(self):
        ratings = Ratings("ratings.csv", "movies.csv")
        ratings_users = Ratings.Users(ratings.data)
        ans = ratings_users.dist_by_rating('average')
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, float)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)        

    def test_ratings_users_top_users_with_biggest_variance(self):
        ratings = Ratings("ratings.csv", "movies.csv")
        ratings_users = Ratings.Users(ratings.data)
        ans = ratings_users.top_users_with_biggest_variance(5)
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, float)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

    #movies

    def test_movies_init(self):
        ans = Movies("movies.csv")
        assert isinstance(ans.data, list)
        assert len(ans.data) == 1000
       
    def test_movies_dist_by_release(self):
        movies = Movies("movies.csv")
        ans = movies.dist_by_release()
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

    def test_movies_dist_by_genres(self):
        movies = Movies("movies.csv")
        ans = movies.dist_by_genres()
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

    def test_movies_most_genres(self):
        movies = Movies("movies.csv")
        ans = movies.most_genres(5)
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

    # tags

    def test_tags_init(self):
        ans = Tags("tags.csv")
        assert isinstance(ans.data, list)
        assert len(ans.data) == 1000

    def test_tags_most_words(self):
        tags = Tags("tags.csv")
        ans = tags.most_words(5)
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)
    
    #bonus test
    def test_tags_most_tagged_movies(self):
        tags = Tags("tags.csv")
        ans = tags.most_tagged_movies(5)
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

    def test_tags_longest(self):
        tags = Tags("tags.csv")
        ans = tags.longest(5)
        assert isinstance(ans, list)
        for item in ans:
            assert isinstance(item, str)
        a = [len(i) for i in ans ]
        assert a == sorted(a, reverse=True)

    def test_tags_most_words_and_longest(self):
        tags = Tags("tags.csv")
        ans = tags.most_words_and_longest(5)
        for item in ans:
            assert isinstance(item, str)
        assert isinstance(ans,list)

    def test_tags_most_popular(self):
        tags = Tags("tags.csv")
        ans = tags.most_popular(5)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
        assert isinstance(ans, dict)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)        

    def test_tags_tags_with(self):
        tags = Tags("tags.csv")
        ans = tags.tags_with("Best")
        for item in ans:
            assert isinstance(item, str)
        assert isinstance(ans, list)
        assert ans == sorted(ans)

    #Links

    def test_links_init(self):
        ans = Links("links.csv", "movies.csv")
        assert isinstance(ans.data, list)
        assert len(ans.data) == 1000

    def test_links_get_imdb(self):
        links = Links("links.csv", "movies.csv")
        lists = links.get_imdb(['0113497','0114709'], ['Director', 'budget', 'revenue', 'Runtime'])
        assert isinstance(lists, list)
        ans = [a[0] for a in lists]
        assert ans == sorted(ans, reverse=True)

    def test_links_tmdb_id(self):
        links = Links("links.csv", "movies.csv")
        ans = links.tmdb_id("0114709")
        assert isinstance(ans, str)
        assert ans == '862'

    def test_links_top_directors(self):
        links = Links("links.csv", "movies.csv")
        ans = links.top_directors(5)
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

    def test_links_most_expensive(self):
        links = Links("links.csv", "movies.csv")
        ans = links.most_expensive(5)
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

    def test_links_most_profitable(self):
        links = Links("links.csv", "movies.csv")
        ans = links.most_profitable(5)
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

    def test_links_longest(self): 
        links = Links("links.csv", "movies.csv")
        ans = links.longest(5)
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

    def test_links_top_cost_per_minute(self):
        links = Links("links.csv", "movies.csv")
        ans = links.top_cost_per_minute(5)
        assert isinstance(ans, dict)
        for key, value in ans.items():
            assert isinstance(key, str)
            assert isinstance(value, float)
        values = list(ans.values())
        assert values == sorted(values, reverse=True)

if __name__ == "__main__":
    link = Links('links.csv', 'movies.csv')
    topdir = link.top_directors(10)
    print(topdir)
    print('\n========================================================\n')
    mostex = link.most_expensive(10)
    print(mostex)
    print('\n========================================================\n')
    mostprof = link.most_profitable(10)
    print(mostprof)
    print('\n========================================================\n')
    longest = link.longest(10)
    print(longest)
    print('\n========================================================\n')
    topcostperminute = link.top_cost_per_minute(10)
    print(topcostperminute)
    print('\n========================================================\n')

    ratings = Ratings("ratings.csv", "movies.csv")
    ratings_movies = ratings.Movies(ratings.data)
    ans = ratings_movies.top_by_genre('Comedy', 10)
    print(ans)

    print('\n========================================================\n')



    tags = Tags("tags.csv")
    t = tags.most_tagged_movies(5)
    print(t)