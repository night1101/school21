#!/usr/bin/env python3
#coding: utf8
import os
import sys
import warnings

import pandas as pd

from recipes import MenuGenerator, Nutritionist, RecipeParser

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def show_menu():
    parser = RecipeParser(os.path.join(BASE_DIR, 'full_format_recipes.json'))
    recipes = parser.parse()
    facts = pd.read_csv(
        os.path.join(BASE_DIR, 'nutrition_facts.csv'), index_col=0)
    generator = MenuGenerator(recipes, facts)
    generator.show()


def main():
    if '--menu' in sys.argv or '-m' in sys.argv:
        show_menu()
        return
    if len(sys.argv) < 2:
        sys.exit(1)
    ingredient = [i.strip() for i in ' '.join(sys.argv[1:]).split(',')]
    ingredient = [i for i in ingredient if i]
    nutritionist = Nutritionist(BASE_DIR)
    nutritionist.ingredients = ingredient
    nutritionist.show()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
