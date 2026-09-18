#!/usr/bin/env python3
#coding: utf8
"""recipes.py — module with classes and methods used in the main script."""

import math
import os
import random
import re
import unicodedata

import joblib
import numpy as np
import pandas as pd

MESSAGES = {
    'bad': 'You might find it tasty, but in our opinion, it is a bad idea to\nhave a dish with that list of ingredients.',
    'so-so': 'It is hard to predict how good this dish will be, but you may\nstill enjoy it with that list of ingredients.',
    'great': 'This list of ingredients looks promising, you will definitely\nenjoy such a tasty and useful dish!',
}

NO_SIMILAR_MESSAGE = 'There are no similar recipes for this set of ingredients.'
MISSING_PREFIX = 'The following ingredients are missing in our database:'

SIM_BASE_URL = 'https://www.epicurious.com/recipes/food/views/'

NUTRIENT_LABELS = {
    'Protein': 'Protein',
    'Total lipid (fat)': 'Total Fat',
    'Carbohydrate, by difference': 'Total Carbohydrate',
    'Calcium, Ca': 'Calcium',
    'Sodium, Na': 'Sodium',
    'Total Sugars': 'Total Sugars',
    'Cholesterol': 'Cholesterol',
    'Fiber, total dietary': 'Dietary Fiber',
    'Fatty acids, total saturated': 'Saturated Fat',
    'Vitamin C, total ascorbic acid': 'Vitamin C',
    'Vitamin A, RAE': 'Vitamin A',
    'Vitamin D (D2 + D3)': 'Vitamin D',
    'Vitamin E (alpha-tocopherol)': 'Vitamin E',
    'Vitamin K (phylloquinone)': 'Vitamin K',
    'Iron, Fe': 'Iron',
    'Magnesium, Mg': 'Magnesium',
    'Phosphorus, P': 'Phosphorus',
    'Potassium, K': 'Potassium',
    'Zinc, Zn': 'Zinc',
    'Copper, Cu': 'Copper',
    'Manganese, Mn': 'Manganese',
    'Thiamin': 'Thiamin',
    'Riboflavin': 'Riboflavin',
    'Niacin': 'Niacin',
    'Vitamin B-6': 'Vitamin B-6',
    'Vitamin B-12': 'Vitamin B-12',
    'Folate, total': 'Folate',
    'Pantothenic acid': 'Pantothenic acid',
    'Choline, total': 'Choline',
    'Selenium, Se': 'Selenium',
    'Iodine, I': 'Iodine',
    'Biotin': 'Biotin',
    'Molybdenum, Mo': 'Molybdenum',
}

META_COLUMNS = ['title', 'rating', 'calories', 'protein', 'fat', 'sodium']

NON_INGREDIENTS = [
    'alaska', 'alcoholic', 'breakfast', 'buffalo', 'burrito', 'cake',
    'canada', 'cocktail', 'cookie', 'dessert', 'dip', 'fat free',
    'flat bread', 'fry', 'game', 'grill', 'ice cream', 'lasagna',
    'lunch', 'macaroni and cheese', 'meatball', 'meatloaf', 'organic',
    'pancake', 'pasta maker', 'pastry', 'picnic', 'pie', 'pizza',
    'pot pie', 'potato salad', 'poultry sausage', 'roast', 'salad',
    'salad dressing', 'sandwich', 'sauce', 'smoothie', 'steak',
    'stew', 'taco', 'tart', 'waffle', 'vegetarian', 'fruit juice',
    'sugar conscious', 'snack', 'meat', 'fruit', 'spice', 'seed', 'poultry',
]


def to_category(rating):
    """Convert a rounded rating into a rating category."""
    if rating in (0, 1):
        return 'bad'
    if rating in (2, 3):
        return 'so-so'
    return 'great'


def normalize(name):
    """Return a lowercase stripped name."""
    return str(name).strip().lower()


def slugify(title):
    """Turn a recipe title into a URL slug."""
    slug = ''.join(c if c.isalnum() else ' ' for c in normalize(title))
    return '-'.join(slug.split())


def is_ingredient_column(column):
    """Check whether a dataset column is a real food ingredient."""
    return column not in META_COLUMNS and column not in NON_INGREDIENTS


class Recipe:
    """A single recipe with its title, rating, ingredients and URL."""

    def __init__(self, title, rating, ingredients=None, url=None,
                 categories=None):
        self.title = title
        self.rating = rating
        self.ingredients = ingredients or []
        self.url = url
        self.categories = categories or []

    @property
    def name(self):
        return self.title

    def __str__(self):
        return (f"{self.title}, rating: {self.rating}, URL:\n"
                f"{self.url}")


class RecipeParser:
    """Parse recipes from the Epicurious full-format JSON dataset."""

    def __init__(self, path):
        self.path = path

    def parse(self):
        """Return a list of Recipe objects built from the JSON file."""
        import json
        with open(self.path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        recipes = []
        for item in data:
            recipes.append(Recipe(
                title=item.get('title', ''),
                rating=item.get('rating', 0),
                ingredients=item.get('ingredients', []),
                categories=item.get('categories', []),
            ))
        return recipes

    @staticmethod
    def similar_recipes(recipes, ingredients, top_n=3):
        """Return the most similar recipes to the given ingredient list."""
        scored = []
        wanted = [normalize(i) for i in ingredients]
        for recipe in recipes:
            text = ' '.join(normalize(x) for x in recipe.ingredients)
            matches = sum(1 for w in wanted if w in text)
            if matches == 0:
                continue
            overlap = matches / max(len(wanted), 1)
            scored.append((overlap, recipe.rating, recipe))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [s[2] for s in scored[:top_n]]


class Nutritionist:
    """Main engine: predicts the rating class, nutrition facts and
    similar recipes for a list of ingredients."""

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.ingredients = []
        self.data = pd.read_csv(
            os.path.join(base_dir, 'epi_r_filtered.csv'), low_memory=False)
        self.features = [c for c in self.data.columns if c != 'rating']
        self.matrix = self.data[self.features].apply(
            pd.to_numeric, errors='coerce').fillna(0).values
        self.model = joblib.load(os.path.join(base_dir, 'bestmodel.pkl'))
        similar = pd.read_csv(
            os.path.join(base_dir, 'similar_recipes.csv'), low_memory=False)
        self.similar = similar.reset_index(drop=True)
        self.facts = pd.read_csv(
            os.path.join(base_dir, 'nutrition_facts.csv'), index_col=0)
        self.facts.index = [str(i).strip().lower() for i in self.facts.index]

    @staticmethod
    def _matches(norm_ingredient, column):
        col = normalize(column)
        return (col == norm_ingredient
                or col.startswith(norm_ingredient + '/')
                or col.startswith(norm_ingredient + ' or ')
                or col.startswith(norm_ingredient + ' and ')
                or col.startswith(norm_ingredient + ','))

    def _matched_columns(self):
        matched = set()
        for ing in self.ingredients:
            norm = normalize(ing)
            for i, col in enumerate(self.features):
                if self._matches(norm, col):
                    matched.add(i)
        return matched

    def missing_ingredients(self):
        known = set()
        for ing in self.ingredients:
            norm = normalize(ing)
            for col in self.features:
                if self._matches(norm, col):
                    known.add(norm)
        return [i for i in self.ingredients
                if normalize(i) not in known]

    def _user_vector(self):
        vec = np.zeros(len(self.features))
        for i in self._matched_columns():
            vec[i] = 1.0
        return pd.DataFrame([vec], columns=self.features)

    def forecast(self):
        predicted = self.model.predict(self._user_vector())[0]
        return MESSAGES[predicted]

    def nutrition_facts(self):
        facts = {}
        for ing in self.ingredients:
            norm = normalize(ing)
            if norm not in self.facts.index:
                continue
            row = self.facts.loc[norm]
            facts[ing] = {key: row[key] for key in self.facts.columns}
        return facts

    def similar_recipes(self):
        user = self._matched_columns()
        vec = np.zeros(len(self.features))
        vec[list(user)] = 1.0
        denom = np.linalg.norm(vec) * np.linalg.norm(self.matrix, axis=1)
        denom[denom == 0] = 1.0
        cosine = (self.matrix @ vec) / denom
        overlap = (self.matrix[:, list(user)].sum(axis=1)
                   if user else np.zeros(self.matrix.shape[0]))
        threshold = math.ceil(len(self.ingredients) / 2)
        keep = (cosine > 0) & (overlap >= threshold)
        similar = self.similar[keep].copy()
        similar['cosine'] = cosine[keep]
        similar = similar.sort_values(
            ['cosine', 'rating'], ascending=[False, False])
        return similar.head(3)

    def show(self):
        missing = self.missing_ingredients()
        if missing:
            print(MISSING_PREFIX + ' ' + ', '.join(missing))
            return
        print('I. OUR FORECAST')
        print(self.forecast())
        print()
        print('II. NUTRITION FACTS')
        for ing, nutr in self.nutrition_facts().items():
            print(ing.title())
            for key, label in NUTRIENT_LABELS.items():
                if key not in nutr:
                    continue
                value = nutr[key]
                if pd.isna(value) or value == 0:
                    continue
                print(f"{label} - {round(value)}% of Daily Value")
        print()
        print('III. TOP-3 SIMILAR RECIPES:')
        similar = self.similar_recipes()
        if similar.empty:
            print(NO_SIMILAR_MESSAGE)
            return
        for _, row in similar.iterrows():
            title = str(row['title']).strip()
            url = SIM_BASE_URL + slugify(title)
            print(f"- {title}, rating: {row['rating']}, URL:")
            print(url)


class MenuGenerator:
    """Build a daily menu of three recipes (breakfast, lunch, dinner)
    that cover the daily nutrient needs without exceeding them and
    have the highest total rating."""

    MEALS = ('breakfast', 'lunch', 'dinner')
    DAILY_CAP = 100.0
    COVERAGE_THRESHOLD = 70.0
    SAMPLES = 2000
    CORE_NUTRIENTS = (
        'Protein',
        'Total lipid (fat)',
        'Carbohydrate, by difference',
        'Sodium, Na',
        'Fiber, total dietary',
        'Cholesterol',
        'Fatty acids, total saturated',
        'Total Sugars',
    )

    def __init__(self, recipes, facts):
        self.recipes = recipes
        self.facts = facts
        self._nutrient_cache = {}

    def _matches_meal(self, recipe, meal):
        cats = [str(c).lower() for c in recipe.categories]
        if meal == 'breakfast':
            return any(c in cats for c in ('breakfast', 'brunch'))
        return meal in cats

    def _pool(self, meal):
        return [r for r in self.recipes if self._matches_meal(r, meal)]

    def _matched_facts_rows(self, ingredient):
        norm = normalize(ingredient)
        for idx in self.facts.index:
            pattern = r'\b' + re.escape(str(idx)) + r'\b'
            if re.search(pattern, norm):
                yield idx

    def _recipe_nutrients(self, recipe):
        if id(recipe) in self._nutrient_cache:
            return self._nutrient_cache[id(recipe)]
        totals = {}
        for ing in recipe.ingredients:
            for idx in self._matched_facts_rows(ing):
                row = self.facts.loc[idx]
                for col in self.facts.columns:
                    value = row[col]
                    if pd.isna(value):
                        value = 0.0
                    totals[col] = totals.get(col, 0.0) + float(value)
        self._nutrient_cache[id(recipe)] = totals
        return totals

    @staticmethod
    def _daily_totals(combo):
        daily = {}
        for nutrients in combo:
            for key, value in nutrients.items():
                daily[key] = daily.get(key, 0.0) + value
        return daily

    def _fits(self, daily):
        return not any(daily.get(key, 0.0) > self.DAILY_CAP
                       for key in self.CORE_NUTRIENTS)

    def _coverage(self, daily):
        return sum(1 for v in daily.values()
                   if v >= self.COVERAGE_THRESHOLD)

    def generate(self):
        """Randomly pick one recipe per meal so that together they cover
        the daily needs without exceeding them, maximizing total rating."""
        pools = [self._pool(meal) for meal in self.MEALS]
        pools = [p for p in pools if p]
        rng = random.Random()
        best = None
        best_score = (-1.0, -1)
        for _ in range(self.SAMPLES):
            combo = [rng.choice(pool) for pool in pools]
            daily = self._daily_totals(
                [self._recipe_nutrients(r) for r in combo])
            if not self._fits(daily):
                continue
            total_rating = sum(r.rating for r in combo)
            coverage = self._coverage(daily)
            score = (total_rating, coverage)
            if score > best_score:
                best_score = score
                best = (combo, daily)
        if best is None:
            combo = [max(pool, key=lambda r: r.rating) for pool in pools]
            daily = self._daily_totals(
                [self._recipe_nutrients(r) for r in combo])
            best = (combo, daily)
        return best

    def show(self):
        combo, daily = self.generate()
        for meal, recipe in zip(self.MEALS, combo):
            title = recipe.title.strip()
            print(meal.upper())
            print('---------------------')
            print(f"{title} (rating: {recipe.rating})")
            print('Ingredients:')
            for ing in recipe.ingredients:
                print(f"- {ing}")
            print('Nutrients:')
            nutrients = self._recipe_nutrients(recipe)
            for col in self.facts.columns:
                label = NUTRIENT_LABELS.get(col, col).lower()
                value = nutrients.get(col, 0.0)
                if value > 0:
                    print(f"- {label}: {round(value)}%")
            print(f"URL: {SIM_BASE_URL}{slugify(title)}")
            print()
