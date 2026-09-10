#!/usr/bin/env python3
"""
generate_and_seed_30_problems.py
Generates 30 algorithmic problems (15 Basics + 15 Tableaux) with:
- Detailed Markdown descriptions (Contexte, Format d'entrée, Format de sortie, Exemple)
- Algo template code
- Exactly 12 test cases per problem (2 public + 10 hidden) verified with Python reference implementations
- Saves JSON files in src/web/data/problems/
- Updates manifest.json
- Inserts them directly into PostgreSQL
"""

import json
import math
import os
import sys
from pathlib import Path

# Add src to python path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from web.app import app, db
from web.models import Problem, TestCase

PROBLEMS_DIR = Path(__file__).resolve().parent / 'problems'
PROBLEMS_DIR.mkdir(parents=True, exist_ok=True)

def generate_problems():
    problems = []

    # =========================================================================
    # CHAPITRE 1 : BASICS (15 PROBLEMES)
    # =========================================================================

    # 1. Factorielle d'un Entier (Basics, Easy)
    def solve_fact(n):
        return math.factorial(n)

    p1_tests = []
    p1_inputs = [5, 0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12]
    for idx, n in enumerate(p1_inputs):
        p1_tests.append({
            "input": f"{n}\n",
            "expected_output": f"{solve_fact(n)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Factorielle d'un Entier",
        "topic": "Basics",
        "difficulty": "Easy",
        "description": (
            "### Calcul de la Factorielle d'un Entier\n\n"
            "Écrivez un algorithme qui lit un entier positif ou nul `N` et calcule sa factorielle `N!`.\n\n"
            "#### Contexte & Objectif\n"
            "La factorielle d'un entier naturel `N` est le produit des nombres entiers strictement positifs inférieurs ou égaux à `N`. Par convention, `0! = 1`.\n\n"
            "#### Format d'entrée\n"
            "- Une seule ligne contenant l'entier `N` (avec `0 <= N <= 12`).\n\n"
            "#### Format de sortie attendu\n"
            "- Un seul entier représentant la valeur de `N!`.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "5\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "120\n"
            "```"
        ),
        "template_code": (
            "Algorithme Factorielle;\n"
            "Var\n"
            "    N, F, I : Entier;\n"
            "Debut\n"
            "    Lire(N);\n\n"
            "    // TODO: Initialiser le résultat et calculer la factorielle à l'aide d'une boucle\n"
            "    F <- 1;\n\n"
            "    Ecrire(F);\n"
            "Fin."
        ),
        "test_cases": p1_tests
    })

    # 2. Nombre et Somme des Chiffres (Basics, Easy)
    def solve_digits(n):
        s_n = str(n)
        count = len(s_n)
        s = sum(int(c) for c in s_n)
        return f"{count} {s}"

    p2_tests = []
    p2_inputs = [4821, 0, 7, 10, 999, 1000, 50505, 123456, 90807, 100000, 88, 314159]
    for idx, n in enumerate(p2_inputs):
        p2_tests.append({
            "input": f"{n}\n",
            "expected_output": f"{solve_digits(n)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Nombre et Somme des Chiffres",
        "topic": "Basics",
        "difficulty": "Easy",
        "description": (
            "### Analyse des Chiffres d'un Nombre\n\n"
            "Écrivez un algorithme qui lit un entier positif ou nul `N`, puis détermine le nombre total de chiffres qui le composent ainsi que la somme de ses chiffres.\n\n"
            "#### Contexte & Objectif\n"
            "En utilisant des divisions entières successives par 10 (`div 10`) et des restes (`mod 10`), extrayez chaque chiffre pour les compter et les additionner.\n\n"
            "#### Format d'entrée\n"
            "- Une seule ligne contenant l'entier `N` (`0 <= N <= 1000000`).\n\n"
            "#### Format de sortie attendu\n"
            "- Deux entiers séparés par un espace : le nombre de chiffres suivi de la somme des chiffres.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "4821\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "4 15\n"
            "```"
        ),
        "template_code": (
            "Algorithme ChiffresNombre;\n"
            "Var\n"
            "    N, Temp, NbChiffres, Somme, Reste : Entier;\n"
            "Debut\n"
            "    Lire(N);\n\n"
            "    // TODO: Parcourir les chiffres de N avec div 10 et mod 10\n"
            "    NbChiffres <- 0;\n"
            "    Somme <- 0;\n\n"
            "    Ecrire(NbChiffres, \" \", Somme);\n"
            "Fin."
        ),
        "test_cases": p2_tests
    })

    # 3. Calcul de Puissance Entière (Basics, Easy)
    def solve_pow(x, y):
        return x ** y

    p3_tests = []
    p3_inputs = [(2, 6), (5, 0), (3, 1), (10, 3), (2, 10), (7, 2), (4, 4), (1, 20), (0, 5), (3, 5), (9, 3), (2, 15)]
    for idx, (x, y) in enumerate(p3_inputs):
        p3_tests.append({
            "input": f"{x}\n{y}\n",
            "expected_output": f"{solve_pow(x, y)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Calcul de Puissance Entière",
        "topic": "Basics",
        "difficulty": "Easy",
        "description": (
            "### Calcul de Puissance X^Y\n\n"
            "Écrivez un algorithme qui calcule `X` élevé à la puissance `Y` à l'aide d'une boucle d'accumulation.\n\n"
            "#### Contexte & Objectif\n"
            "Par définition, pour tout entier `X != 0`, `X^0 = 1`. Pour `Y > 0`, `X^Y = X * X * ... * X` (`Y` fois).\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : L'entier de base `X` (`0 <= X <= 20`).\n"
            "- Ligne 2 : L'exposant `Y` (`0 <= Y <= 15`).\n\n"
            "#### Format de sortie attendu\n"
            "- Un seul entier représentant `X^Y`.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "2\n"
            "6\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "64\n"
            "```"
        ),
        "template_code": (
            "Algorithme Puissance;\n"
            "Var\n"
            "    X, Y, Res, I : Entier;\n"
            "Debut\n"
            "    Lire(X);\n"
            "    Lire(Y);\n\n"
            "    // TODO: Calculer X^Y à l'aide d'une boucle\n"
            "    Res <- 1;\n\n"
            "    Ecrire(Res);\n"
            "Fin."
        ),
        "test_cases": p3_tests
    })

    # 4. Table de Multiplication Personnalisée (Basics, Easy)
    def solve_mult_table(n, k):
        lines = [f"{n} x {i} = {n * i}" for i in range(1, k + 1)]
        return "\n".join(lines) + "\n"

    p4_tests = []
    p4_inputs = [(7, 3), (5, 1), (12, 4), (1, 5), (9, 2), (6, 6), (8, 5), (10, 3), (3, 4), (11, 3), (4, 7), (2, 8)]
    for idx, (n, k) in enumerate(p4_inputs):
        p4_tests.append({
            "input": f"{n}\n{k}\n",
            "expected_output": solve_mult_table(n, k),
            "is_public": idx < 2
        })

    problems.append({
        "title": "Table de Multiplication Personnalisée",
        "topic": "Basics",
        "difficulty": "Easy",
        "description": (
            "### Table de Multiplication de N jusqu'à K\n\n"
            "Écrivez un algorithme qui lit deux entiers `N` et `K` et affiche les `K` premières lignes de la table de multiplication de `N`.\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : L'entier `N`.\n"
            "- Ligne 2 : Le nombre de lignes `K` (`K >= 1`).\n\n"
            "#### Format de sortie attendu\n"
            "- `K` lignes au format exact `N x i = Resultat`.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "7\n"
            "3\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "7 x 1 = 7\n"
            "7 x 2 = 14\n"
            "7 x 3 = 21\n"
            "```"
        ),
        "template_code": (
            "Algorithme TableMultiplication;\n"
            "Var\n"
            "    N, K, I : Entier;\n"
            "Debut\n"
            "    Lire(N);\n"
            "    Lire(K);\n\n"
            "    // TODO: Afficher chaque ligne sous la forme N x I = Prod\n"
            "    Pour I De 1 A K Faire\n"
            "        Ecrire(N, \" x \", I, \" = \", N * I);\n"
            "    FinPour;\n"
            "Fin."
        ),
        "test_cases": p4_tests
    })

    # 5. Test d'Année Bissextile (Basics, Easy)
    def solve_leap(year):
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return "1"
        return "0"

    p5_tests = []
    p5_inputs = [2024, 1900, 2000, 2023, 2020, 2100, 2400, 1996, 1982, 2004, 2018, 1600]
    for idx, yr in enumerate(p5_inputs):
        p5_tests.append({
            "input": f"{yr}\n",
            "expected_output": f"{solve_leap(yr)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Test d'Année Bissextile",
        "topic": "Basics",
        "difficulty": "Easy",
        "description": (
            "### Détection d'Année Bissextile\n\n"
            "Écrivez un algorithme qui détermine si une année donnée est bissextile.\n\n"
            "#### Règle du calendrier grégorien\n"
            "Une année est bissextile si :\n"
            "- Elle est divisible par 4 ET non divisible par 100,\n"
            "- OU si elle est divisible par 400.\n\n"
            "#### Format d'entrée\n"
            "- Un entier positif `Annee`.\n\n"
            "#### Format de sortie attendu\n"
            "- Affichez `1` si l'année est bissextile, ou `0` sinon.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "2024\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "1\n"
            "```"
        ),
        "template_code": (
            "Algorithme AnneeBissextile;\n"
            "Var\n"
            "    Annee, EstBissextile : Entier;\n"
            "Debut\n"
            "    Lire(Annee);\n\n"
            "    // TODO: Appliquer les conditions bissextiles\n"
            "    Si ((Annee Mod 4 = 0) Et (Annee Mod 100 <> 0)) Ou (Annee Mod 400 = 0) Alors\n"
            "        EstBissextile <- 1;\n"
            "    Sinon\n"
            "        EstBissextile <- 0;\n"
            "    FinSi;\n\n"
            "    Ecrire(EstBissextile);\n"
            "Fin."
        ),
        "test_cases": p5_tests
    })

    # 6. Conversion Binaire en Décimal (Basics, Medium)
    def solve_bin2dec(b_str):
        return int(str(b_str), 2)

    p6_tests = []
    p6_inputs = [1101, 10, 0, 1, 111, 1000, 1010, 1111, 10000, 10101, 111111, 1001001]
    for idx, b in enumerate(p6_inputs):
        p6_tests.append({
            "input": f"{b}\n",
            "expected_output": f"{solve_bin2dec(b)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Conversion Binaire en Décimal",
        "topic": "Basics",
        "difficulty": "Medium",
        "description": (
            "### Conversion de Binaire vers Décimal\n\n"
            "Écrivez un algorithme qui lit un nombre binaire (représenté comme un entier composé uniquement de 0 et 1) et calcule sa valeur équivalente en base 10.\n\n"
            "#### Principe\n"
            "En décomposant par modulo 10, chaque chiffre binaire extrait à la position $i$ contribue pour $bit \\times 2^i$ au total décimal.\n\n"
            "#### Format d'entrée\n"
            "- Un entier composé uniquement des chiffres 0 et 1 (ex: `1101`).\n\n"
            "#### Format de sortie attendu\n"
            "- Un seul entier représentant la valeur décimale.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "1101\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "13\n"
            "```"
        ),
        "template_code": (
            "Algorithme BinaireVersDecimal;\n"
            "Var\n"
            "    Binaire, Decimal, Poids, Bit : Entier;\n"
            "Debut\n"
            "    Lire(Binaire);\n\n"
            "    // TODO: Extraire les bits avec Mod 10 et accumuler avec les puissances de 2\n"
            "    Decimal <- 0;\n"
            "    Poids <- 1;\n\n"
            "    TantQue Binaire > 0 Faire\n"
            "        Bit <- Binaire Mod 10;\n"
            "        Decimal <- Decimal + Bit * Poids;\n"
            "        Poids <- Poids * 2;\n"
            "        Binaire <- Binaire Div 10;\n"
            "    FinTantQue;\n\n"
            "    Ecrire(Decimal);\n"
            "Fin."
        ),
        "test_cases": p6_tests
    })

    # 7. Longueur du Vol de Syracuse (Basics, Medium)
    def solve_collatz(n):
        steps = 0
        mx = n
        curr = n
        while curr > 1:
            if curr % 2 == 0:
                curr = curr // 2
            else:
                curr = 3 * curr + 1
            steps += 1
            if curr > mx:
                mx = curr
        return f"{steps} {mx}"

    p7_tests = []
    p7_inputs = [6, 1, 2, 3, 5, 7, 11, 15, 27, 12, 10, 20]
    for idx, n in enumerate(p7_inputs):
        p7_tests.append({
            "input": f"{n}\n",
            "expected_output": f"{solve_collatz(n)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Longueur du Vol de Syracuse",
        "topic": "Basics",
        "difficulty": "Medium",
        "description": (
            "### Suite de Collatz (Problème de Syracuse)\n\n"
            "Soit la suite définie pour un entier $N > 0$ par :\n"
            "- Si $N$ est pair : $N \\leftarrow N / 2$\n"
            "- Si $N$ est impair : $N \\leftarrow 3N + 1$\n"
            "La conjecture de Collatz affirme que toute valeur finit par atteindre 1.\n\n"
            "#### Objectif\n"
            "Calculer le nombre total d'étapes pour atteindre 1, ainsi que la valeur maximale atteinte au cours du vol.\n\n"
            "#### Format d'entrée\n"
            "- Un entier $N \\ge 1$.\n\n"
            "#### Format de sortie attendu\n"
            "- Deux entiers séparés par un espace : `Etapes Max`.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "6\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "8 16\n"
            "```"
        ),
        "template_code": (
            "Algorithme Syracuse;\n"
            "Var\n"
            "    N, Etapes, ValMax : Entier;\n"
            "Debut\n"
            "    Lire(N);\n\n"
            "    Etapes <- 0;\n"
            "    ValMax <- N;\n\n"
            "    // TODO: Appliquer les règles de Collatz jusqu'à atteindre 1\n"
            "    TantQue N > 1 Faire\n"
            "        Si N Mod 2 = 0 Alors\n"
            "            N <- N Div 2;\n"
            "        Sinon\n"
            "            N <- 3 * N + 1;\n"
            "        FinSi;\n"
            "        Etapes <- Etapes + 1;\n"
            "        Si N > ValMax Alors\n"
            "            ValMax <- N;\n"
            "        FinSi;\n"
            "    FinTantQue;\n\n"
            "    Ecrire(Etapes, \" \", ValMax);\n"
            "Fin."
        ),
        "test_cases": p7_tests
    })

    # 8. PGCD et PPCM par Euclide (Basics, Medium)
    def solve_gcd_lcm(a, b):
        g = math.gcd(a, b)
        l = (a * b) // g
        return f"{g} {l}"

    p8_tests = []
    p8_inputs = [(48, 18), (15, 25), (7, 13), (100, 10), (12, 18), (21, 14), (35, 49), (17, 19), (54, 24), (80, 60), (9, 9), (120, 45)]
    for idx, (a, b) in enumerate(p8_inputs):
        p8_tests.append({
            "input": f"{a}\n{b}\n",
            "expected_output": f"{solve_gcd_lcm(a, b)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "PGCD et PPCM par Euclide",
        "topic": "Basics",
        "difficulty": "Medium",
        "description": (
            "### Calcul du PGCD et du PPCM\n\n"
            "Écrivez un algorithme qui lit deux entiers strictement positifs `A` et `B`, calcule leur Plus Grand Commun Diviseur (PGCD) à l'aide de l'algorithme d'Euclide, puis leur Plus Petit Commun Multiple (PPCM).\n\n"
            "#### Formule\n"
            "$$\\text{PPCM}(A, B) = \\frac{A \\times B}{\\text{PGCD}(A, B)}$$\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : L'entier `A`.\n"
            "- Ligne 2 : L'entier `B`.\n\n"
            "#### Format de sortie attendu\n"
            "- Deux entiers séparés par un espace : `PGCD PPCM`.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "48\n"
            "18\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "6 144\n"
            "```"
        ),
        "template_code": (
            "Algorithme PgcdPpcm;\n"
            "Var\n"
            "    A, B, X, Y, Reste, Pgcd, Ppcm : Entier;\n"
            "Debut\n"
            "    Lire(A);\n"
            "    Lire(B);\n\n"
            "    X <- A;\n"
            "    Y <- B;\n"
            "    TantQue Y <> 0 Faire\n"
            "        Reste <- X Mod Y;\n"
            "        X <- Y;\n"
            "        Y <- Reste;\n"
            "    FinTantQue;\n"
            "    Pgcd <- X;\n"
            "    Ppcm <- (A * B) Div Pgcd;\n\n"
            "    Ecrire(Pgcd, \" \", Ppcm);\n"
            "Fin."
        ),
        "test_cases": p8_tests
    })

    # 9. Prochain Nombre Premier (Basics, Medium)
    def is_prime(k):
        if k < 2: return False
        if k == 2: return True
        if k % 2 == 0: return False
        for d in range(3, int(math.isqrt(k)) + 1, 2):
            if k % d == 0:
                return False
        return True

    def solve_next_prime(n):
        cand = n + 1
        while not is_prime(cand):
            cand += 1
        return cand

    p9_tests = []
    p9_inputs = [14, 2, 1, 19, 20, 31, 50, 97, 113, 199, 250, 500]
    for idx, n in enumerate(p9_inputs):
        p9_tests.append({
            "input": f"{n}\n",
            "expected_output": f"{solve_next_prime(n)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Prochain Nombre Premier",
        "topic": "Basics",
        "difficulty": "Medium",
        "description": (
            "### Trouver le Plus Petit Premier Strictement Supérieur à N\n\n"
            "Écrivez un algorithme qui lit un entier `N` et trouve le premier nombre premier strictement supérieur à `N`.\n\n"
            "#### Format d'entrée\n"
            "- Un entier positif `N` (`1 <= N <= 2000`).\n\n"
            "#### Format de sortie attendu\n"
            "- Un seul entier : le prochain nombre premier.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "14\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "17\n"
            "```"
        ),
        "template_code": (
            "Algorithme ProchainPremier;\n"
            "Var\n"
            "    N, Cand, D, EstPremier : Entier;\n"
            "Debut\n"
            "    Lire(N);\n\n"
            "    Cand <- N + 1;\n"
            "    // TODO: Tester chaque candidat jusqu'à trouver un nombre premier\n"
            "    TantQue 1 = 1 Faire\n"
            "        EstPremier <- 1;\n"
            "        Si Cand < 2 Alors EstPremier <- 0; FinSi;\n"
            "        Pour D De 2 A Cand - 1 Faire\n"
            "            Si Cand Mod D = 0 Alors EstPremier <- 0; FinSi;\n"
            "        FinPour;\n"
            "        Si EstPremier = 1 Alors\n"
            "            Ecrire(Cand);\n"
            "            // Sortir de la boucle\n"
            "            N <- 0;\n"
            "            Cand <- -1;\n"
            "        Sinon\n"
            "            Cand <- Cand + 1;\n"
            "        FinSi;\n"
            "        Si Cand = -1 Alors Cand <- 0; N <- 0; FinSi;\n"
            "    FinTantQue;\n"
            "Fin."
        ),
        "test_cases": p9_tests
    })

    # 10. Décomposition en Facteurs Premiers (Basics, Medium)
    def solve_prime_factors(n):
        factors = []
        d = 2
        curr = n
        while d * d <= curr:
            if curr % d == 0:
                p = 0
                while curr % d == 0:
                    p += 1
                    curr //= d
                factors.append(f"{d}^{p}")
            d += 1
        if curr > 1:
            factors.append(f"{curr}^1")
        return " * ".join(factors)

    p10_tests = []
    p10_inputs = [60, 13, 18, 100, 84, 32, 49, 210, 128, 315, 97, 720]
    for idx, n in enumerate(p10_inputs):
        p10_tests.append({
            "input": f"{n}\n",
            "expected_output": f"{solve_prime_factors(n)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Décomposition en Facteurs Premiers",
        "topic": "Basics",
        "difficulty": "Medium",
        "description": (
            "### Décomposition d'un Nombre en Facteurs Premiers\n\n"
            "Écrivez un algorithme qui décompose un entier `N` en facteurs premiers sous la forme `p1^e1 * p2^e2 * ...`.\n\n"
            "#### Format d'entrée\n"
            "- Un entier `N` (`N >= 2`).\n\n"
            "#### Format de sortie attendu\n"
            "- Une ligne contenant la décomposition avec le format exact `facteur^puissance` séparés par ` * `.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "60\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "2^2 * 3^1 * 5^1\n"
            "```"
        ),
        "template_code": (
            "Algorithme FacteursPremiers;\n"
            "Var\n"
            "    N, D, P, PremierFacteur : Entier;\n"
            "Debut\n"
            "    Lire(N);\n\n"
            "    D <- 2;\n"
            "    PremierFacteur <- 1;\n"
            "    TantQue D * D <= N Faire\n"
            "        Si N Mod D = 0 Alors\n"
            "            P <- 0;\n"
            "            TantQue N Mod D = 0 Faire\n"
            "                P <- P + 1;\n"
            "                N <- N Div D;\n"
            "            FinTantQue;\n"
            "            Si PremierFacteur = 0 Alors Ecrire(\" * \"); FinSi;\n"
            "            Ecrire(D, \"^\", P);\n"
            "            PremierFacteur <- 0;\n"
            "        FinSi;\n"
            "        D <- D + 1;\n"
            "    FinTantQue;\n"
            "    Si N > 1 Alors\n"
            "        Si PremierFacteur = 0 Alors Ecrire(\" * \"); FinSi;\n"
            "        Ecrire(N, \"^1\");\n"
            "    FinSi;\n"
            "    Ecrire(\"\");\n"
            "Fin."
        ),
        "test_cases": p10_tests
    })

    # 11. Exponentiation Modulaire Rapide (Basics, Hard)
    def solve_mod_pow(a, b, m):
        return pow(a, b, m)

    p11_tests = []
    p11_inputs = [
        (3, 13, 7), (2, 10, 1000), (5, 3, 13), (2, 20, 17), (7, 100, 13),
        (3, 25, 11), (4, 15, 19), (6, 8, 23), (11, 13, 100), (2, 30, 105),
        (9, 9, 10), (13, 17, 31)
    ]
    for idx, (a, b, m) in enumerate(p11_inputs):
        p11_tests.append({
            "input": f"{a}\n{b}\n{m}\n",
            "expected_output": f"{solve_mod_pow(a, b, m)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Exponentiation Modulaire Rapide",
        "topic": "Basics",
        "difficulty": "Hard",
        "description": (
            "### Calcul de (A^B) mod M en Temps Logarithmique\n\n"
            "Écrivez un algorithme qui calcule `(A^B) mod M` efficacement en $O(\\log B)$ par élévation au carré modulaire, évitant tout débordement d'entier.\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `A` (base)\n"
            "- Ligne 2 : `B` (exposant)\n"
            "- Ligne 3 : `M` (modulo)\n\n"
            "#### Format de sortie attendu\n"
            "- Un entier représentant `(A^B) mod M`.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "3\n"
            "13\n"
            "7\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "3\n"
            "```"
        ),
        "template_code": (
            "Algorithme ExponentiationModulaire;\n"
            "Var\n"
            "    A, B, M, Res : Entier;\n"
            "Debut\n"
            "    Lire(A);\n"
            "    Lire(B);\n"
            "    Lire(M);\n\n"
            "    Res <- 1;\n"
            "    A <- A Mod M;\n"
            "    TantQue B > 0 Faire\n"
            "        Si B Mod 2 = 1 Alors\n"
            "            Res <- (Res * A) Mod M;\n"
            "        FinSi;\n"
            "        A <- (A * A) Mod M;\n"
            "        B <- B Div 2;\n"
            "    FinTantQue;\n\n"
            "    Ecrire(Res);\n"
            "Fin."
        ),
        "test_cases": p11_tests
    })

    # 12. Racine Carrée par la Méthode de Héron (Basics, Hard)
    def solve_heron(n):
        x = n / 2.0
        for _ in range(25):
            x = 0.5 * (x + n / x)
        return f"{x:.4f}"

    p12_tests = []
    p12_inputs = [2, 9, 10, 16, 25, 50, 100, 3, 7, 81, 144, 200]
    for idx, n in enumerate(p12_inputs):
        p12_tests.append({
            "input": f"{n}\n",
            "expected_output": f"{solve_heron(n)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Racine Carrée par la Méthode de Héron",
        "topic": "Basics",
        "difficulty": "Hard",
        "description": (
            "### Approximation Numérique de la Racine Carrée\n\n"
            "Calculez la racine carrée d'un nombre entier `N` par la méthode itérative de Héron d'Alexandrie :\n"
            "$$x_{k+1} = \\frac{1}{2} \\left( x_k + \\frac{N}{x_k} \\right)$$\n\n"
            "#### Format d'entrée\n"
            "- Un entier `N` (`N >= 1`).\n\n"
            "#### Format de sortie attendu\n"
            "- La valeur approchée arrondie à 4 chiffres après la virgule.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "2\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "1.4142\n"
            "```"
        ),
        "template_code": (
            "Algorithme RacineHeron;\n"
            "Var\n"
            "    N, I : Entier;\n"
            "    X : Reel;\n"
            "Debut\n"
            "    Lire(N);\n\n"
            "    X <- N / 2.0;\n"
            "    Pour I De 1 A 25 Faire\n"
            "        X <- 0.5 * (X + N / X);\n"
            "    FinPour;\n\n"
            "    Ecrire(X);\n"
            "Fin."
        ),
        "test_cases": p12_tests
    })

    # 13. Comptage des Zéros Terminaux de Factorielle (Basics, Hard)
    def solve_legendre_zeros(n):
        count = 0
        p = 5
        while p <= n:
            count += n // p
            p *= 5
        return count

    p13_tests = []
    p13_inputs = [100, 5, 10, 25, 50, 125, 200, 500, 1000, 10000, 4, 26]
    for idx, n in enumerate(p13_inputs):
        p13_tests.append({
            "input": f"{n}\n",
            "expected_output": f"{solve_legendre_zeros(n)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Comptage des Zéros Terminaux de Factorielle",
        "topic": "Basics",
        "difficulty": "Hard",
        "description": (
            "### Combien de Zéros terminent N! ?\n\n"
            "Déterminez par combien de zéros se termine l'écriture décimale de `N!` sans calculer explicitement la factorielle (formule de Legendre sur les facteurs 5).\n\n"
            "#### Formule de Legendre\n"
            "$$\\sum_{k=1}^{\\infty} \\lfloor \\frac{N}{5^k} \\rfloor$$\n\n"
            "#### Format d'entrée\n"
            "- Un entier `N` (`0 <= N <= 100000`).\n\n"
            "#### Format de sortie attendu\n"
            "- Un entier représentant le nombre de zéros terminaux.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "100\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "24\n"
            "```"
        ),
        "template_code": (
            "Algorithme ZerosFactorielle;\n"
            "Var\n"
            "    N, Zeros, Diviseur : Entier;\n"
            "Debut\n"
            "    Lire(N);\n\n"
            "    Zeros <- 0;\n"
            "    Diviseur <- 5;\n"
            "    TantQue Diviseur <= N Faire\n"
            "        Zeros <- Zeros + (N Div Diviseur);\n"
            "        Diviseur <- Diviseur * 5;\n"
            "    FinTantQue;\n\n"
            "    Ecrire(Zeros);\n"
            "Fin."
        ),
        "test_cases": p13_tests
    })

    # 14. Nombres Amicaux dans un Intervalle (Basics, Hard)
    def sum_proper_divisors(k):
        if k <= 1: return 0
        s = 1
        for d in range(2, int(math.isqrt(k)) + 1):
            if k % d == 0:
                s += d
                if d * d != k:
                    s += k // d
        return s

    def solve_amicable_count(limit):
        count = 0
        for a in range(2, limit + 1):
            b = sum_proper_divisors(a)
            if b > a and b <= limit:
                if sum_proper_divisors(b) == a:
                    count += 1
        return count

    p14_tests = []
    p14_inputs = [300, 200, 1200, 1500, 2000, 3000, 5000, 6000, 7000, 10000, 150, 500]
    for idx, lim in enumerate(p14_inputs):
        p14_tests.append({
            "input": f"{lim}\n",
            "expected_output": f"{solve_amicable_count(lim)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Nombres Amicaux dans un Intervalle",
        "topic": "Basics",
        "difficulty": "Hard",
        "description": (
            "### Détection de Paires de Nombres Amicaux\n\n"
            "Deux nombres distincts `A` et `B` sont dits **amicaux** si la somme des diviseurs stricts de `A` est égale à `B`, et réciproquement.\n"
            "Exemple : 220 et 284 sont amicaux.\n\n"
            "#### Objectif\n"
            "Compter le nombre total de paires amicales uniques `(A, B)` où `A < B <= Limite`.\n\n"
            "#### Format d'entrée\n"
            "- Un entier `Limite` (`Limite <= 10000`).\n\n"
            "#### Format de sortie attendu\n"
            "- Le nombre de paires amicales trouvées.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "300\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "1\n"
            "```"
        ),
        "template_code": (
            "Algorithme NombresAmicaux;\n"
            "Var\n"
            "    Limite, A, B, SommeA, SommeB, D, NbPaires : Entier;\n"
            "Debut\n"
            "    Lire(Limite);\n\n"
            "    NbPaires <- 0;\n"
            "    Pour A De 2 A Limite Faire\n"
            "        SommeA <- 1;\n"
            "        Pour D De 2 A A - 1 Faire\n"
            "            Si A Mod D = 0 Alors SommeA <- SommeA + D; FinSi;\n"
            "        FinPour;\n"
            "        B <- SommeA;\n"
            "        Si (B > A) Et (B <= Limite) Alors\n"
            "            SommeB <- 1;\n"
            "            Pour D De 2 A B - 1 Faire\n"
            "                Si B Mod D = 0 Alors SommeB <- SommeB + D; FinSi;\n"
            "            FinPour;\n"
            "            Si SommeB = A Alors\n"
            "                NbPaires <- NbPaires + 1;\n"
            "            FinSi;\n"
            "        FinSi;\n"
            "    FinPour;\n\n"
            "    Ecrire(NbPaires);\n"
            "Fin."
        ),
        "test_cases": p14_tests
    })

    # 15. Problème de Josephus Arithmétique (Basics, Hard)
    def solve_josephus(n, k):
        res = 0
        for i in range(1, n + 1):
            res = (res + k) % i
        return res + 1

    p15_tests = []
    p15_inputs = [(7, 3), (5, 2), (1, 2), (6, 5), (10, 2), (8, 3), (12, 4), (15, 3), (20, 2), (14, 2), (100, 2), (40, 7)]
    for idx, (n, k) in enumerate(p15_inputs):
        p15_tests.append({
            "input": f"{n}\n{k}\n",
            "expected_output": f"{solve_josephus(n, k)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Problème de Josephus Arithmétique",
        "topic": "Basics",
        "difficulty": "Hard",
        "description": (
            "### Le Problème de Josephus\n\n"
            "`N` personnes sont disposées en cercle et numérotées de 1 à `N`. En commençant par la personne 1, on élimine chaque `K`-ième personne vivante jusqu'à ce qu'il n'en reste qu'une seule.\n\n"
            "#### Objectif\n"
            "Déterminer la position finale du survivant en utilisant la formule itérative :\n"
            "$$J(1, K) = 0$$\n"
            "$$J(i, K) = (J(i-1, K) + K) \\pmod i$$\n"
            "avec conversion finale en indexation 1 ($J + 1$).\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N` (nombre de personnes, `N >= 1`).\n"
            "- Ligne 2 : `K` (pas d'élimination, `K >= 1`).\n\n"
            "#### Format de sortie attendu\n"
            "- Un seul entier représentant la position du survivant.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "7\n"
            "3\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "4\n"
            "```"
        ),
        "template_code": (
            "Algorithme Josephus;\n"
            "Var\n"
            "    N, K, Survivant, I : Entier;\n"
            "Debut\n"
            "    Lire(N);\n"
            "    Lire(K);\n\n"
            "    Survivant <- 0;\n"
            "    Pour I De 1 A N Faire\n"
            "        Survivant <- (Survivant + K) Mod I;\n"
            "    FinPour;\n\n"
            "    Ecrire(Survivant + 1);\n"
            "Fin."
        ),
        "test_cases": p15_tests
    })

    # =========================================================================
    # CHAPITRE 2 : TABLEAUX & MATRICES (15 PROBLEMES)
    # =========================================================================

    # 16. Somme et Moyenne d'un Tableau 1D (Tableaux, Easy)
    def solve_arr_sum_avg(arr):
        s = sum(arr)
        avg = s / len(arr)
        return f"{s} {avg:.2f}"

    p16_tests = []
    p16_inputs = [
        [10, 20, 30, 40],
        [5],
        [1, 2, 3, 4, 5],
        [0, 0, 0, 0],
        [-10, 10, -5, 5],
        [100, 200, 300],
        [7, 14, 21, 28, 35, 42],
        [12, 18, 24, 30],
        [-1, -2, -3, -4],
        [15, 25, 35, 45, 55],
        [2, 4, 8, 16, 32, 64],
        [9, 18, 27]
    ]
    for idx, arr in enumerate(p16_inputs):
        in_str = f"{len(arr)}\n" + "\n".join(str(x) for x in arr) + "\n"
        p16_tests.append({
            "input": in_str,
            "expected_output": f"{solve_arr_sum_avg(arr)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Somme et Moyenne d'un Tableau 1D",
        "topic": "Tableaux",
        "difficulty": "Easy",
        "description": (
            "### Calcul de la Somme et de la Moyenne d'un Tableau\n\n"
            "Écrivez un algorithme qui lit la taille `N` d'un tableau d'entiers, puis les `N` éléments, et calcule la somme arithmétique ainsi que la moyenne des éléments.\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : Entier `N` (`N >= 1`).\n"
            "- Les `N` lignes suivantes : Les entiers du tableau.\n\n"
            "#### Format de sortie attendu\n"
            "- Deux valeurs : `Somme Moyenne` (avec la moyenne arrondie à 2 décimales).\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "4\n"
            "10\n"
            "20\n"
            "30\n"
            "40\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "100 25.00\n"
            "```"
        ),
        "template_code": (
            "Algorithme SommeMoyenneTableau;\n"
            "Var\n"
            "    T : Tableau[1..100] de Entier;\n"
            "    N, I, Somme : Entier;\n"
            "    Moyenne : Reel;\n"
            "Debut\n"
            "    Lire(N);\n"
            "    Somme <- 0;\n"
            "    Pour I De 1 A N Faire\n"
            "        Lire(T[I]);\n"
            "        Somme <- Somme + T[I];\n"
            "    FinPour;\n\n"
            "    Moyenne <- Somme / N;\n"
            "    Ecrire(Somme, \" \", Moyenne);\n"
            "Fin."
        ),
        "test_cases": p16_tests
    })

    # 17. Recherche Séquentielle et Indice (Tableaux, Easy)
    def solve_linear_search(arr, target):
        for i, val in enumerate(arr, start=1):
            if val == target:
                return i
        return -1

    p17_tests = []
    p17_inputs = [
        ([4, 8, 15, 16, 23], 15),
        ([10, 20, 30], 99),
        ([5, 5, 5], 5),
        ([1, 3, 5, 7, 9], 1),
        ([1, 3, 5, 7, 9], 9),
        ([42], 42),
        ([42], 0),
        ([-5, -2, 0, 4, 8], 0),
        ([-10, -20, -30], -20),
        ([100, 200, 300, 400, 500], 350),
        ([7, 14, 21, 28, 35], 28),
        ([2, 4, 6, 8, 10, 12], 2)
    ]
    for idx, (arr, target) in enumerate(p17_inputs):
        in_str = f"{len(arr)}\n" + "\n".join(str(x) for x in arr) + f"\n{target}\n"
        p17_tests.append({
            "input": in_str,
            "expected_output": f"{solve_linear_search(arr, target)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Recherche Séquentielle et Indice",
        "topic": "Tableaux",
        "difficulty": "Easy",
        "description": (
            "### Recherche Linéaire dans un Tableau 1D\n\n"
            "Écrivez un algorithme qui recherche la première apparition d'une valeur `Cible` dans un tableau de taille `N`.\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N` (taille du tableau)\n"
            "- Lignes 2 à N+1 : Les `N` entiers du tableau\n"
            "- Ligne N+2 : L'entier `Cible`\n\n"
            "#### Format de sortie attendu\n"
            "- L'indice (base 1) de la première occurrence, ou `-1` si la valeur n'est pas présente.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "5\n"
            "4\n"
            "8\n"
            "15\n"
            "16\n"
            "23\n"
            "15\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "3\n"
            "```"
        ),
        "template_code": (
            "Algorithme RechercheLineaire;\n"
            "Var\n"
            "    T : Tableau[1..100] de Entier;\n"
            "    N, I, Cible, Pos : Entier;\n"
            "Debut\n"
            "    Lire(N);\n"
            "    Pour I De 1 A N Faire Lire(T[I]); FinPour;\n"
            "    Lire(Cible);\n\n"
            "    Pos <- -1;\n"
            "    Pour I De 1 A N Faire\n"
            "        Si (T[I] = Cible) Et (Pos = -1) Alors Pos <- I; FinSi;\n"
            "    FinPour;\n\n"
            "    Ecrire(Pos);\n"
            "Fin."
        ),
        "test_cases": p17_tests
    })

    # 18. Inversion d'un Tableau en Place (Tableaux, Easy)
    def solve_reverse_arr(arr):
        return " ".join(str(x) for x in reversed(arr))

    p18_tests = []
    p18_inputs = [
        [1, 2, 3, 4, 5],
        [10, 20],
        [7],
        [1, 1, 1, 1],
        [-3, 0, 3],
        [4, 8, 15, 16, 23, 42],
        [9, 7, 5, 3, 1],
        [100, -200, 300, -400],
        [0, 1, 0, 1, 0],
        [5, 4, 3, 2, 1, 0],
        [12, 34, 56, 78],
        [99, 88, 77, 66, 55, 44, 33]
    ]
    for idx, arr in enumerate(p18_inputs):
        in_str = f"{len(arr)}\n" + "\n".join(str(x) for x in arr) + "\n"
        p18_tests.append({
            "input": in_str,
            "expected_output": f"{solve_reverse_arr(arr)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Inversion d'un Tableau en Place",
        "topic": "Tableaux",
        "difficulty": "Easy",
        "description": (
            "### Inverser les Éléments d'un Tableau\n\n"
            "Écrivez un algorithme qui inverse l'ordre des éléments d'un tableau de taille `N` en échangeant les éléments symétriques par rapport au milieu.\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N`\n"
            "- Les `N` lignes suivantes : Les entiers du tableau\n\n"
            "#### Format de sortie attendu\n"
            "- Les éléments du tableau inversé affichés sur une seule ligne séparés par des espaces.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "5\n"
            "1\n"
            "2\n"
            "3\n"
            "4\n"
            "5\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "5 4 3 2 1\n"
            "```"
        ),
        "template_code": (
            "Algorithme InversionTableau;\n"
            "Var\n"
            "    T : Tableau[1..100] de Entier;\n"
            "    N, I, Temp : Entier;\n"
            "Debut\n"
            "    Lire(N);\n"
            "    Pour I De 1 A N Faire Lire(T[I]); FinPour;\n\n"
            "    Pour I De 1 A N Div 2 Faire\n"
            "        Temp <- T[I];\n"
            "        T[I] <- T[N - I + 1];\n"
            "        T[N - I + 1] <- Temp;\n"
            "    FinPour;\n\n"
            "    Pour I De 1 A N Faire\n"
            "        Si I > 1 Alors Ecrire(\" \"); FinSi;\n"
            "        Ecrire(T[I]);\n"
            "    FinPour;\n"
            "    Ecrire(\"\");\n"
            "Fin."
        ),
        "test_cases": p18_tests
    })

    # 19. Comptage des Positifs, Négatifs et Zéros (Tableaux, Easy)
    def solve_count_signs(arr):
        pos = sum(1 for x in arr if x > 0)
        neg = sum(1 for x in arr if x < 0)
        zeros = sum(1 for x in arr if x == 0)
        return f"{pos} {neg} {zeros}"

    p19_tests = []
    p19_inputs = [
        [-3, 0, 5, 12, -7, 0],
        [1, 2, 3],
        [-1, -2, -3],
        [0, 0, 0],
        [10, -10],
        [-5, 0, 5],
        [100, -200, 300, 0, -400, 0, 500],
        [-1, -1, 0, 1, 1],
        [42],
        [-42],
        [0],
        [7, -3, 0, 8, -4, 0, 9, -5]
    ]
    for idx, arr in enumerate(p19_inputs):
        in_str = f"{len(arr)}\n" + "\n".join(str(x) for x in arr) + "\n"
        p19_tests.append({
            "input": in_str,
            "expected_output": f"{solve_count_signs(arr)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Comptage des Positifs, Négatifs et Zéros",
        "topic": "Tableaux",
        "difficulty": "Easy",
        "description": (
            "### Dénombrement selon le Signe\n\n"
            "Écrivez un algorithme qui lit `N` entiers et compte simultanément le nombre d'éléments strictement positifs, strictement négatifs, et nuls.\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N`\n"
            "- Lignes 2 à N+1 : Les `N` entiers\n\n"
            "#### Format de sortie attendu\n"
            "- Trois entiers séparés par des espaces : `Positifs Negatifs Zeros`.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "6\n"
            "-3\n"
            "0\n"
            "5\n"
            "12\n"
            "-7\n"
            "0\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "2 2 2\n"
            "```"
        ),
        "template_code": (
            "Algorithme ComptageSignes;\n"
            "Var\n"
            "    N, I, Val, Pos, Neg, Zeros : Entier;\n"
            "Debut\n"
            "    Lire(N);\n"
            "    Pos <- 0;\n"
            "    Neg <- 0;\n"
            "    Zeros <- 0;\n\n"
            "    Pour I De 1 A N Faire\n"
            "        Lire(Val);\n"
            "        Si Val > 0 Alors\n"
            "            Pos <- Pos + 1;\n"
            "        Sinon\n"
            "            Si Val < 0 Alors\n"
            "                Neg <- Neg + 1;\n"
            "            Sinon\n"
            "                Zeros <- Zeros + 1;\n"
            "            FinSi;\n"
            "        FinSi;\n"
            "    FinPour;\n\n"
            "    Ecrire(Pos, \" \", Neg, \" \", Zeros);\n"
            "Fin."
        ),
        "test_cases": p19_tests
    })

    # 20. Trace d'une Matrice Carrée (Tableaux, Easy)
    def solve_matrix_trace(mat):
        return sum(mat[i][i] for i in range(len(mat)))

    p20_tests = []
    p20_inputs = [
        [[1, 2], [3, 4]],
        [[5]],
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        [[2, 1, 3], [4, 5, 6], [7, 8, 9]],
        [[-1, 2], [3, -4]],
        [[10, 20], [30, 40]],
        [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]],
        [[0, 1], [1, 0]],
        [[7, -5, 2], [1, -3, 4], [9, 0, 10]],
        [[-5]],
        [[100, 200], [300, 400]],
        [[4, 2, 1], [5, 6, 7], [8, 9, 3]]
    ]
    for idx, mat in enumerate(p20_inputs):
        n = len(mat)
        flat = []
        for row in mat:
            flat.extend(row)
        in_str = f"{n}\n" + "\n".join(str(x) for x in flat) + "\n"
        p20_tests.append({
            "input": in_str,
            "expected_output": f"{solve_matrix_trace(mat)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Trace d'une Matrice Carrée",
        "topic": "Tableaux",
        "difficulty": "Easy",
        "description": (
            "### Somme de la Diagonale Principale d'une Matrice Carrée\n\n"
            "Écrivez un algorithme qui lit la dimension `N` d'une matrice carrée `N x N`, puis ses éléments, et calcule sa trace (somme des éléments `M[i][i]`).\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N`\n"
            "- Les $N \\times N$ lignes suivantes : Les éléments de la matrice lus ligne par ligne\n\n"
            "#### Format de sortie attendu\n"
            "- Un seul entier représentant la trace de la matrice.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "2\n"
            "1\n"
            "2\n"
            "3\n"
            "4\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "5\n"
            "```"
        ),
        "template_code": (
            "Algorithme TraceMatrice;\n"
            "Var\n"
            "    M : Tableau[1..20, 1..20] de Entier;\n"
            "    N, I, J, Trace : Entier;\n"
            "Debut\n"
            "    Lire(N);\n"
            "    Pour I De 1 A N Faire\n"
            "        Pour J De 1 A N Faire Lire(M[I, J]); FinPour;\n"
            "    FinPour;\n\n"
            "    Trace <- 0;\n"
            "    Pour I De 1 A N Faire\n"
            "        Trace <- Trace + M[I, I];\n"
            "    FinPour;\n\n"
            "    Ecrire(Trace);\n"
            "Fin."
        ),
        "test_cases": p20_tests
    })

    # 21. Suppression des Doublons In-Place (Tableaux, Medium)
    def solve_remove_duplicates(arr):
        unique = sorted(list(set(arr)))
        return f"{len(unique)}\n" + " ".join(str(x) for x in unique)

    p21_tests = []
    p21_inputs = [
        [1, 1, 2, 3, 3, 4],
        [5, 5, 5, 5],
        [1, 2, 3, 4, 5],
        [10],
        [-5, -5, -2, 0, 0, 4],
        [1, 1, 1, 2, 2, 3],
        [0, 0, 1, 1, 1, 2, 2, 3, 3, 4],
        [-10, -10, -5, 0, 5, 5],
        [7, 7, 8, 9, 9],
        [2, 4, 4, 6, 8, 8, 10],
        [-1, 0, 0, 1],
        [100, 100, 200, 300, 300, 400]
    ]
    for idx, arr in enumerate(p21_inputs):
        in_str = f"{len(arr)}\n" + "\n".join(str(x) for x in arr) + "\n"
        p21_tests.append({
            "input": in_str,
            "expected_output": f"{solve_remove_duplicates(arr)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Suppression des Doublons In-Place",
        "topic": "Tableaux",
        "difficulty": "Medium",
        "description": (
            "### Compactage d'un Tableau Trié\n\n"
            "Étant donné un tableau trié dans l'ordre croissant contenant des doublons, compactez le tableau pour éliminer les occurrences répétées et conserver uniquement les éléments uniques.\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N`\n"
            "- Lignes 2 à N+1 : Les `N` entiers triés\n\n"
            "#### Format de sortie attendu\n"
            "- Ligne 1 : La nouvelle taille `K` du tableau\n"
            "- Ligne 2 : Les `K` éléments uniques séparés par des espaces\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "6\n"
            "1\n"
            "1\n"
            "2\n"
            "3\n"
            "3\n"
            "4\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "4\n"
            "1 2 3 4\n"
            "```"
        ),
        "template_code": (
            "Algorithme SupprimerDoublons;\n"
            "Var\n"
            "    T, Unique : Tableau[1..100] de Entier;\n"
            "    N, I, K : Entier;\n"
            "Debut\n"
            "    Lire(N);\n"
            "    Pour I De 1 A N Faire Lire(T[I]); FinPour;\n\n"
            "    K <- 1;\n"
            "    Unique[1] <- T[1];\n"
            "    Pour I De 2 A N Faire\n"
            "        Si T[I] <> T[I - 1] Alors\n"
            "            K <- K + 1;\n"
            "            Unique[K] <- T[I];\n"
            "        FinSi;\n"
            "    FinPour;\n\n"
            "    Ecrire(K);\n"
            "    Pour I De 1 A K Faire\n"
            "        Si I > 1 Alors Ecrire(\" \"); FinSi;\n"
            "        Ecrire(Unique[I]);\n"
            "    FinPour;\n"
            "    Ecrire(\"\");\n"
            "Fin."
        ),
        "test_cases": p21_tests
    })

    # 22. Produit de Deux Matrices (Tableaux, Medium)
    def solve_mat_mult(n, m, p, a, b):
        c = [[0] * p for _ in range(n)]
        for i in range(n):
            for j in range(p):
                c[i][j] = sum(a[i][k] * b[k][j] for k in range(m))
        lines = [" ".join(str(x) for x in row) for row in c]
        return "\n".join(lines)

    p22_tests = []
    p22_inputs = [
        (2, 3, 2, [[1, 2, 3], [4, 5, 6]], [[7, 8], [9, 1], [2, 3]]),
        (2, 2, 2, [[1, 0], [0, 1]], [[5, 6], [7, 8]]),
        (1, 2, 1, [[2, 3]], [[4], [5]]),
        (2, 2, 2, [[1, 2], [3, 4]], [[2, 0], [1, 2]]),
        (3, 2, 2, [[1, 2], [3, 4], [5, 6]], [[1, 1], [1, 1]]),
        (2, 2, 1, [[1, 2], [3, 4]], [[5], [6]]),
        (1, 1, 1, [[7]], [[8]]),
        (2, 2, 2, [[0, 1], [1, 0]], [[0, 1], [1, 0]]),
        (2, 3, 1, [[1, -1, 2], [0, 3, -2]], [[2], [4], [1]]),
        (2, 2, 2, [[-1, 2], [3, -4]], [[2, -1], [0, 3]]),
        (3, 1, 2, [[2], [3], [4]], [[5, 6]]),
        (2, 2, 2, [[10, 20], [30, 40]], [[1, 2], [3, 4]])
    ]
    for idx, (n, m, p, a, b) in enumerate(p22_inputs):
        in_parts = [f"{n}", f"{m}", f"{p}"]
        for row in a:
            in_parts.extend(str(x) for x in row)
        for row in b:
            in_parts.extend(str(x) for x in row)
        p22_tests.append({
            "input": "\n".join(in_parts) + "\n",
            "expected_output": f"{solve_mat_mult(n, m, p, a, b)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Produit de Deux Matrices",
        "topic": "Tableaux",
        "difficulty": "Medium",
        "description": (
            "### Multiplication Matricielle (N x M) par (M x P)\n\n"
            "Écrivez un algorithme qui multiplie une matrice `A` de dimension `N x M` par une matrice `B` de dimension `M x P` pour produire la matrice `C` de dimension `N x P`.\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N`\n"
            "- Ligne 2 : `M`\n"
            "- Ligne 3 : `P`\n"
            "- Les $N \\times M$ lignes suivantes : Éléments de la matrice `A`\n"
            "- Les $M \\times P$ lignes suivantes : Éléments de la matrice `B`\n\n"
            "#### Format de sortie attendu\n"
            "- Les `N` lignes de la matrice produit `C`, les colonnes étant séparées par des espaces.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "2\n"
            "2\n"
            "2\n"
            "1\n"
            "0\n"
            "0\n"
            "1\n"
            "5\n"
            "6\n"
            "7\n"
            "8\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "5 6\n"
            "7 8\n"
            "```"
        ),
        "template_code": (
            "Algorithme ProduitMatrices;\n"
            "Var\n"
            "    A : Tableau[1..15, 1..15] de Entier;\n"
            "    B : Tableau[1..15, 1..15] de Entier;\n"
            "    C : Tableau[1..15, 1..15] de Entier;\n"
            "    N, M, P, I, J, K, S : Entier;\n"
            "Debut\n"
            "    Lire(N); Lire(M); Lire(P);\n"
            "    Pour I De 1 A N Faire\n"
            "        Pour J De 1 A M Faire Lire(A[I, J]); FinPour;\n"
            "    FinPour;\n"
            "    Pour I De 1 A M Faire\n"
            "        Pour J De 1 A P Faire Lire(B[I, J]); FinPour;\n"
            "    FinPour;\n\n"
            "    Pour I De 1 A N Faire\n"
            "        Pour J De 1 A P Faire\n"
            "            S <- 0;\n"
            "            Pour K De 1 A M Faire\n"
            "                S <- S + A[I, K] * B[K, J];\n"
            "            FinPour;\n"
            "            C[I, J] <- S;\n"
            "        FinPour;\n"
            "    FinPour;\n\n"
            "    Pour I De 1 A N Faire\n"
            "        Pour J De 1 A P Faire\n"
            "            Si J > 1 Alors Ecrire(\" \"); FinSi;\n"
            "            Ecrire(C[I, J]);\n"
            "        FinPour;\n"
            "        Ecrire(\"\");\n"
            "    FinPour;\n"
            "Fin."
        ),
        "test_cases": p22_tests
    })

    # 23. Transposition de Matrice Carrée (Tableaux, Medium)
    def solve_mat_transpose(mat):
        n = len(mat)
        trans = [[mat[j][i] for j in range(n)] for i in range(n)]
        return "\n".join(" ".join(str(x) for x in row) for row in trans)

    p23_tests = []
    p23_inputs = [
        [[1, 2], [3, 4]],
        [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        [[5]],
        [[0, 1], [0, 0]],
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        [[10, 20], [30, 40]],
        [[1, 4, 7], [2, 5, 8], [3, 6, 9]],
        [[-1, -2], [-3, -4]],
        [[7, 8], [9, 10]],
        [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]],
        [[2, 0], [0, 3]],
        [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
    ]
    for idx, mat in enumerate(p23_inputs):
        n = len(mat)
        flat = []
        for row in mat:
            flat.extend(row)
        in_str = f"{n}\n" + "\n".join(str(x) for x in flat) + "\n"
        p23_tests.append({
            "input": in_str,
            "expected_output": f"{solve_mat_transpose(mat)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Transposition de Matrice Carrée",
        "topic": "Tableaux",
        "difficulty": "Medium",
        "description": (
            "### Transposition d'une Matrice N x N\n\n"
            "Écrivez un algorithme qui permute les lignes et colonnes d'une matrice carrée `N x N` ($M_{trans}[i][j] = M[j][i]$).\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N`\n"
            "- Les $N \\times N$ lignes suivantes : Éléments de la matrice ligne par ligne\n\n"
            "#### Format de sortie attendu\n"
            "- Les `N` lignes de la matrice transposée, les colonnes étant séparées par des espaces.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "2\n"
            "1\n"
            "2\n"
            "3\n"
            "4\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "1 3\n"
            "2 4\n"
            "```"
        ),
        "template_code": (
            "Algorithme TranspositionMatrice;\n"
            "Var\n"
            "    M : Tableau[1..20, 1..20] de Entier;\n"
            "    N, I, J, Temp : Entier;\n"
            "Debut\n"
            "    Lire(N);\n"
            "    Pour I De 1 A N Faire\n"
            "        Pour J De 1 A N Faire Lire(M[I, J]); FinPour;\n"
            "    FinPour;\n\n"
            "    Pour I De 1 A N Faire\n"
            "        Pour J De I + 1 A N Faire\n"
            "            Temp <- M[I, J];\n"
            "            M[I, J] <- M[J, I];\n"
            "            M[J, I] <- Temp;\n"
            "        FinPour;\n"
            "    FinPour;\n\n"
            "    Pour I De 1 A N Faire\n"
            "        Pour J De 1 A N Faire\n"
            "            Si J > 1 Alors Ecrire(\" \"); FinSi;\n"
            "            Ecrire(M[I, J]);\n"
            "        FinPour;\n"
            "        Ecrire(\"\");\n"
            "    FinPour;\n"
            "Fin."
        ),
        "test_cases": p23_tests
    })

    # 24. Élément Majoritaire de Boyer-Moore (Tableaux, Medium)
    def solve_majority(arr):
        cand = None
        count = 0
        for x in arr:
            if count == 0:
                cand = x
                count = 1
            elif x == cand:
                count += 1
            else:
                count -= 1
        return cand

    p24_tests = []
    p24_inputs = [
        [2, 2, 1, 1, 1, 2, 2],
        [3, 2, 3],
        [1],
        [7, 7, 7, 7, 1, 2, 7],
        [5, 5, 5, 2, 5, 3, 5],
        [10, 20, 10, 10, 10],
        [4, 4, 1, 4, 2, 4],
        [9, 9, 9, 8, 9, 7, 9],
        [-1, -1, 2, -1, 3, -1, -1],
        [6, 6, 6, 6, 6],
        [100, 200, 100, 100, 300, 100, 100],
        [8, 1, 8, 2, 8, 3, 8, 4, 8]
    ]
    for idx, arr in enumerate(p24_inputs):
        in_str = f"{len(arr)}\n" + "\n".join(str(x) for x in arr) + "\n"
        p24_tests.append({
            "input": in_str,
            "expected_output": f"{solve_majority(arr)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Élément Majoritaire de Boyer-Moore",
        "topic": "Tableaux",
        "difficulty": "Medium",
        "description": (
            "### Détection de l'Élément Majoritaire en O(N)\n\n"
            "Étant donné un tableau de taille `N`, trouvez l'élément qui apparaît strictement plus de $\\lfloor N/2 \\rfloor$ fois.\n"
            "L'existence de l'élément majoritaire est garantie.\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N`\n"
            "- Lignes 2 à N+1 : Les `N` entiers\n\n"
            "#### Format de sortie attendu\n"
            "- La valeur de l'élément majoritaire.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "7\n"
            "2\n"
            "2\n"
            "1\n"
            "1\n"
            "1\n"
            "2\n"
            "2\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "2\n"
            "```"
        ),
        "template_code": (
            "Algorithme ElementMajoritaire;\n"
            "Var\n"
            "    T : Tableau[1..100] de Entier;\n"
            "    N, I, Candidat, Compteur : Entier;\n"
            "Debut\n"
            "    Lire(N);\n"
            "    Pour I De 1 A N Faire Lire(T[I]); FinPour;\n\n"
            "    Candidat <- T[1];\n"
            "    Compteur <- 1;\n"
            "    Pour I De 2 A N Faire\n"
            "        Si Compteur = 0 Alors\n"
            "            Candidat <- T[I];\n"
            "            Compteur <- 1;\n"
            "        Sinon\n"
            "            Si T[I] = Candidat Alors\n"
            "                Compteur <- Compteur + 1;\n"
            "            Sinon\n"
            "                Compteur <- Compteur - 1;\n"
            "            FinSi;\n"
            "        FinSi;\n"
            "    FinPour;\n\n"
            "    Ecrire(Candidat);\n"
            "Fin."
        ),
        "test_cases": p24_tests
    })

    # 25. Recherche de Paire Cible (Two Sum) (Tableaux, Medium)
    def solve_two_sum(arr, target):
        left = 0
        right = len(arr) - 1
        while left < right:
            s = arr[left] + arr[right]
            if s == target:
                return f"{arr[left]} {arr[right]}"
            elif s < target:
                left += 1
            else:
                right -= 1
        return "-1"

    p25_tests = []
    p25_inputs = [
        ([2, 7, 11, 15], 9),
        ([1, 2, 3, 4, 6], 10),
        ([1, 2, 3], 10),
        ([-5, -2, 1, 3, 7], 2),
        ([3, 5, 8, 12, 15], 20),
        ([1, 4, 6, 8, 10], 14),
        ([-10, -5, 0, 5, 10], 0),
        ([2, 3, 4], 6),
        ([10, 20, 30, 40], 50),
        ([-8, -4, -2, 0, 2, 6], -2),
        ([7, 14, 21, 28], 35),
        ([1, 3, 5, 7, 9], 16)
    ]
    for idx, (arr, target) in enumerate(p25_inputs):
        in_str = f"{len(arr)}\n" + "\n".join(str(x) for x in arr) + f"\n{target}\n"
        p25_tests.append({
            "input": in_str,
            "expected_output": f"{solve_two_sum(arr, target)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Recherche de Paire Cible",
        "topic": "Tableaux",
        "difficulty": "Medium",
        "description": (
            "### Deux Éléments de Somme Cible (Two Sum)\n\n"
            "Étant donné un tableau trié dans l'ordre croissant et une valeur `Cible`, trouvez deux éléments distincts dont la somme vaut exactement `Cible`.\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N`\n"
            "- Lignes 2 à N+1 : Les `N` entiers triés\n"
            "- Ligne N+2 : L'entier `Cible`\n\n"
            "#### Format de sortie attendu\n"
            "- Les deux valeurs séparées par un espace, ou `-1` si aucune paire n'existe.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "4\n"
            "2\n"
            "7\n"
            "11\n"
            "15\n"
            "9\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "2 7\n"
            "```"
        ),
        "template_code": (
            "Algorithme RecherchePaireCible;\n"
            "Var\n"
            "    T : Tableau[1..100] de Entier;\n"
            "    N, I, Cible, Gauche, Droite, Somme, Trouve : Entier;\n"
            "Debut\n"
            "    Lire(N);\n"
            "    Pour I De 1 A N Faire Lire(T[I]); FinPour;\n"
            "    Lire(Cible);\n\n"
            "    Gauche <- 1;\n"
            "    Droite <- N;\n"
            "    Trouve <- 0;\n"
            "    TantQue (Gauche < Droite) Et (Trouve = 0) Faire\n"
            "        Somme <- T[Gauche] + T[Droite];\n"
            "        Si Somme = Cible Alors\n"
            "            Ecrire(T[Gauche], \" \", T[Droite]);\n"
            "            Trouve <- 1;\n"
            "        Sinon\n"
            "            Si Somme < Cible Alors Gauche <- Gauche + 1;\n"
            "            Sinon Droite <- Droite - 1;\n"
            "            FinSi;\n"
            "        FinSi;\n"
            "    FinTantQue;\n\n"
            "    Si Trouve = 0 Alors Ecrire(\"-1\"); FinSi;\n"
            "Fin."
        ),
        "test_cases": p25_tests
    })

    # 26. Parcours en Spirale d'une Matrice (Tableaux, Hard)
    def solve_spiral(mat):
        n = len(mat)
        m = len(mat[0])
        top, bottom, left, right = 0, n - 1, 0, m - 1
        res = []
        while top <= bottom and left <= right:
            for j in range(left, right + 1):
                res.append(mat[top][j])
            top += 1
            for i in range(top, bottom + 1):
                res.append(mat[i][right])
            right -= 1
            if top <= bottom:
                for j in range(right, left - 1, -1):
                    res.append(mat[bottom][j])
                bottom -= 1
            if left <= right:
                for i in range(bottom, top - 1, -1):
                    res.append(mat[i][left])
                left += 1
        return " ".join(str(x) for x in res)

    p26_tests = []
    p26_inputs = [
        [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]],
        [[42]],
        [[1, 2], [3, 4]],
        [[1, 2, 3, 4]],
        [[1], [2], [3], [4]],
        [[1, 2, 3], [4, 5, 6]],
        [[1, 2], [3, 4], [5, 6]],
        [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]],
        [[10, 20], [40, 30]],
        [[5, 6, 7], [8, 9, 10], [11, 12, 13]],
        [[1, 2, 3], [8, 9, 4], [7, 6, 5]]
    ]
    for idx, mat in enumerate(p26_inputs):
        n = len(mat)
        m = len(mat[0])
        flat = []
        for row in mat:
            flat.extend(row)
        in_str = f"{n}\n{m}\n" + "\n".join(str(x) for x in flat) + "\n"
        p26_tests.append({
            "input": in_str,
            "expected_output": f"{solve_spiral(mat)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Parcours en Spirale d'une Matrice",
        "topic": "Tableaux",
        "difficulty": "Hard",
        "description": (
            "### Parcours d'une Matrice en Spirale dans le Sens Horaire\n\n"
            "Écrivez un algorithme qui lit une matrice de dimensions `N x M` et affiche ses éléments selon un parcours en spirale partant du coin supérieur gauche vers le centre.\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N`\n"
            "- Ligne 2 : `M`\n"
            "- Les $N \\times M$ lignes suivantes : Éléments de la matrice ligne par ligne\n\n"
            "#### Format de sortie attendu\n"
            "- Les éléments affichés sur une seule ligne séparés par des espaces.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "3\n"
            "3\n"
            "1\n"
            "2\n"
            "3\n"
            "4\n"
            "5\n"
            "6\n"
            "7\n"
            "8\n"
            "9\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "1 2 3 6 9 8 7 4 5\n"
            "```"
        ),
        "template_code": (
            "Algorithme SpiraleMatrice;\n"
            "Var\n"
            "    M : Tableau[1..20, 1..20] de Entier;\n"
            "    N, P, I, J, Haut, Bas, Gauche, Droite, Premier : Entier;\n"
            "Debut\n"
            "    Lire(N);\n"
            "    Lire(P);\n"
            "    Pour I De 1 A N Faire\n"
            "        Pour J De 1 A P Faire Lire(M[I, J]); FinPour;\n"
            "    FinPour;\n\n"
            "    Haut <- 1; Bas <- N; Gauche <- 1; Droite <- P; Premier <- 1;\n"
            "    TantQue (Haut <= Bas) Et (Gauche <= Droite) Faire\n"
            "        Pour J De Gauche A Droite Faire\n"
            "            Si Premier = 0 Alors Ecrire(\" \"); FinSi;\n"
            "            Ecrire(M[Haut, J]); Premier <- 0;\n"
            "        FinPour;\n"
            "        Haut <- Haut + 1;\n"
            "        Pour I De Haut A Bas Faire\n"
            "            Si Premier = 0 Alors Ecrire(\" \"); FinSi;\n"
            "            Ecrire(M[I, Droite]); Premier <- 0;\n"
            "        FinPour;\n"
            "        Droite <- Droite - 1;\n"
            "        Si Haut <= Bas Alors\n"
            "            Pour J De Droite A Gauche Pas -1 Faire\n"
            "                Si Premier = 0 Alors Ecrire(\" \"); FinSi;\n"
            "                Ecrire(M[Bas, J]); Premier <- 0;\n"
            "            FinPour;\n"
            "            Bas <- Bas - 1;\n"
            "        FinSi;\n"
            "        Si Gauche <= Droite Alors\n"
            "            Pour I De Bas A Haut Pas -1 Faire\n"
            "                Si Premier = 0 Alors Ecrire(\" \"); FinSi;\n"
            "                Ecrire(M[I, Gauche]); Premier <- 0;\n"
            "            FinPour;\n"
            "            Gauche <- Gauche + 1;\n"
            "        FinSi;\n"
            "    FinTantQue;\n"
            "    Ecrire(\"\");\n"
            "Fin."
        ),
        "test_cases": p26_tests
    })

    # 27. Rotation de Matrice de 90 Degrés (Tableaux, Hard)
    def solve_rotate_90(mat):
        n = len(mat)
        res = [[mat[n - 1 - j][i] for j in range(n)] for i in range(n)]
        return "\n".join(" ".join(str(x) for x in row) for row in res)

    p27_tests = []
    p27_inputs = [
        [[1, 2], [3, 4]],
        [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        [[42]],
        [[0, 1], [1, 0]],
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        [[10, 20], [30, 40]],
        [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]],
        [[-1, 2], [3, -4]],
        [[7, 8, 9], [1, 2, 3], [4, 5, 6]],
        [[2, 4], [6, 8]],
        [[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]],
        [[9, 8], [7, 6]]
    ]
    for idx, mat in enumerate(p27_inputs):
        n = len(mat)
        flat = []
        for row in mat:
            flat.extend(row)
        in_str = f"{n}\n" + "\n".join(str(x) for x in flat) + "\n"
        p27_tests.append({
            "input": in_str,
            "expected_output": f"{solve_rotate_90(mat)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Rotation de Matrice de 90 Degrés",
        "topic": "Tableaux",
        "difficulty": "Hard",
        "description": (
            "### Rotation d'une Matrice de 90° dans le Sens Horaire\n\n"
            "Écrivez un algorithme qui effectue une rotation de 90° dans le sens horaire d'une matrice carrée `N x N`.\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N`\n"
            "- Les $N \\times N$ lignes suivantes : Éléments de la matrice ligne par ligne\n\n"
            "#### Format de sortie attendu\n"
            "- Les `N` lignes de la matrice tournée, les colonnes étant séparées par des espaces.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "2\n"
            "1\n"
            "2\n"
            "3\n"
            "4\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "3 1\n"
            "4 2\n"
            "```"
        ),
        "template_code": (
            "Algorithme Rotation90;\n"
            "Var\n"
            "    M : Tableau[1..20, 1..20] de Entier;\n"
            "    N, I, J, Temp : Entier;\n"
            "Debut\n"
            "    Lire(N);\n"
            "    Pour I De 1 A N Faire\n"
            "        Pour J De 1 A N Faire Lire(M[I, J]); FinPour;\n"
            "    FinPour;\n\n"
            "    Pour I De 1 A N Faire\n"
            "        Pour J De I + 1 A N Faire\n"
            "            Temp <- M[I, J];\n"
            "            M[I, J] <- M[J, I];\n"
            "            M[J, I] <- Temp;\n"
            "        FinPour;\n"
            "    FinPour;\n\n"
            "    Pour I De 1 A N Faire\n"
            "        Pour J De 1 A N Div 2 Faire\n"
            "            Temp <- M[I, J];\n"
            "            M[I, J] <- M[I, N - J + 1];\n"
            "            M[I, N - J + 1] <- Temp;\n"
            "        FinPour;\n"
            "    FinPour;\n\n"
            "    Pour I De 1 A N Faire\n"
            "        Pour J De 1 A N Faire\n"
            "            Si J > 1 Alors Ecrire(\" \"); FinSi;\n"
            "            Ecrire(M[I, J]);\n"
            "        FinPour;\n"
            "        Ecrire(\"\");\n"
            "    FinPour;\n"
            "Fin."
        ),
        "test_cases": p27_tests
    })

    # 28. Sous-Matrice de Somme Maximale (Tableaux, Hard)
    def solve_max_submatrix(mat):
        n = len(mat)
        m = len(mat[0])
        max_so_far = -10**9
        for top in range(n):
            col_sums = [0] * m
            for bottom in range(top, n):
                for col in range(m):
                    col_sums[col] += mat[bottom][col]
                current_max = col_sums[0]
                best = col_sums[0]
                for x in col_sums[1:]:
                    current_max = max(x, current_max + x)
                    best = max(best, current_max)
                if best > max_so_far:
                    max_so_far = best
        return max_so_far

    p28_tests = []
    p28_inputs = [
        [[1, 2, -1], [-4, -20, -3], [-5, 20, 10]],
        [[1, 2], [3, 4]],
        [[-5]],
        [[0, -2, -7, 0], [9, 2, -6, 2], [-4, 1, -4, 1], [-1, 8, 0, -2]],
        [[-1, -2], [-3, -4]],
        [[5, -3], [-1, 4]],
        [[2, 1, -3, -4, 5], [0, 6, 3, 4, 1], [2, -2, -1, 4, -5]],
        [[10]],
        [[-2, -3], [-4, -1]],
        [[1, -1, 1], [-1, 1, -1], [1, -1, 1]],
        [[10, -5, 2], [-3, 20, -2]],
        [[3, -2, 5], [1, 4, -1]]
    ]
    for idx, mat in enumerate(p28_inputs):
        n = len(mat)
        m = len(mat[0])
        flat = []
        for row in mat:
            flat.extend(row)
        in_str = f"{n}\n{m}\n" + "\n".join(str(x) for x in flat) + "\n"
        p28_tests.append({
            "input": in_str,
            "expected_output": f"{solve_max_submatrix(mat)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Sous-Matrice de Somme Maximale",
        "topic": "Tableaux",
        "difficulty": "Hard",
        "description": (
            "### Somme Maximale d'une Sous-Matrice Rectangulaire\n\n"
            "Étant donné une matrice de dimensions `N x M` pouvant contenir des entiers positifs et négatifs, trouvez la sous-matrice contiguë dont la somme des éléments est maximale.\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N`\n"
            "- Ligne 2 : `M`\n"
            "- Les $N \\times M$ lignes suivantes : Éléments de la matrice\n\n"
            "#### Format de sortie attendu\n"
            "- Un entier représentant la somme maximale.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "3\n"
            "3\n"
            "1\n"
            "2\n"
            "-1\n"
            "-4\n"
            "-20\n"
            "-3\n"
            "-5\n"
            "20\n"
            "10\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "30\n"
            "```"
        ),
        "template_code": (
            "Algorithme SousMatriceMaximale;\n"
            "Var\n"
            "    M : Tableau[1..15, 1..15] de Entier;\n"
            "    ColSomme : Tableau[1..15] de Entier;\n"
            "    N, P, I, J, Haut, Bas, MaxTotal, Courant, BestKadane : Entier;\n"
            "Debut\n"
            "    Lire(N); Lire(P);\n"
            "    Pour I De 1 A N Faire\n"
            "        Pour J De 1 A P Faire Lire(M[I, J]); FinPour;\n"
            "    FinPour;\n\n"
            "    MaxTotal <- -1000000;\n"
            "    Pour Haut De 1 A N Faire\n"
            "        Pour J De 1 A P Faire ColSomme[J] <- 0; FinPour;\n"
            "        Pour Bas De Haut A N Faire\n"
            "            Pour J De 1 A P Faire ColSomme[J] <- ColSomme[J] + M[Bas, J]; FinPour;\n"
            "            Courant <- ColSomme[1];\n"
            "            BestKadane <- ColSomme[1];\n"
            "            Pour J De 2 A P Faire\n"
            "                Si Courant + ColSomme[J] > ColSomme[J] Alors\n"
            "                    Courant <- Courant + ColSomme[J];\n"
            "                Sinon\n"
            "                    Courant <- ColSomme[J];\n"
            "                FinSi;\n"
            "                Si Courant > BestKadane Alors BestKadane <- Courant; FinSi;\n"
            "            FinPour;\n"
            "            Si BestKadane > MaxTotal Alors MaxTotal <- BestKadane; FinSi;\n"
            "        FinPour;\n"
            "    FinPour;\n\n"
            "    Ecrire(MaxTotal);\n"
            "Fin."
        ),
        "test_cases": p28_tests
    })

    # 29. Triplets de Somme Nulle (3Sum) (Tableaux, Hard)
    def solve_3sum_count(arr):
        arr.sort()
        count = 0
        n = len(arr)
        for i in range(n - 2):
            if i > 0 and arr[i] == arr[i - 1]:
                continue
            left = i + 1
            right = n - 1
            while left < right:
                s = arr[i] + arr[left] + arr[right]
                if s == 0:
                    count += 1
                    left += 1
                    right -= 1
                    while left < right and arr[left] == arr[left - 1]:
                        left += 1
                    while left < right and arr[right] == arr[right + 1]:
                        right -= 1
                elif s < 0:
                    left += 1
                else:
                    right -= 1
        return count

    p29_tests = []
    p29_inputs = [
        [-1, 0, 1, 2, -1, -4],
        [0, 1, 1],
        [0, 0, 0],
        [-2, 0, 1, 1, 2],
        [-3, 1, 2],
        [-5, 2, 3, -2, 0, 2],
        [1, 2, -2, -1],
        [-4, -2, -2, -2, 0, 1, 2, 2, 2, 3, 3, 4, 4, 6, 6],
        [-1, 0, 1],
        [3, -3, 0, 2, -2, 1, -1],
        [10, -10, 5, -5, 0],
        [-6, -4, -2, 0, 2, 4, 6]
    ]
    for idx, arr in enumerate(p29_inputs):
        in_str = f"{len(arr)}\n" + "\n".join(str(x) for x in arr) + "\n"
        p29_tests.append({
            "input": in_str,
            "expected_output": f"{solve_3sum_count(arr)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Triplets de Somme Nulle",
        "topic": "Tableaux",
        "difficulty": "Hard",
        "description": (
            "### Le Problème 3Sum (Triplets de Somme 0)\n\n"
            "Étant donné un tableau d'entiers de taille `N`, déterminez le nombre total de triplets distincts `(A[i], A[j], A[k])` avec $i < j < k$ tels que :\n"
            "$$A[i] + A[j] + A[k] = 0$$\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N`\n"
            "- Lignes 2 à N+1 : Les `N` entiers\n\n"
            "#### Format de sortie attendu\n"
            "- Le nombre de triplets uniques de somme nulle.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "6\n"
            "-1\n"
            "0\n"
            "1\n"
            "2\n"
            "-1\n"
            "-4\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "2\n"
            "```"
        ),
        "template_code": (
            "Algorithme TripletsSommeNulle;\n"
            "Var\n"
            "    T : Tableau[1..100] de Entier;\n"
            "    N, I, J, K, Gauche, Droite, Somme, NbTriplets, Temp : Entier;\n"
            "Debut\n"
            "    Lire(N);\n"
            "    Pour I De 1 A N Faire Lire(T[I]); FinPour;\n\n"
            "    Pour I De 1 A N - 1 Faire\n"
            "        Pour J De I + 1 A N Faire\n"
            "            Si T[I] > T[J] Alors\n"
            "                Temp <- T[I]; T[I] <- T[J]; T[J] <- Temp;\n"
            "            FinSi;\n"
            "        FinPour;\n"
            "    FinPour;\n\n"
            "    NbTriplets <- 0;\n"
            "    Pour I De 1 A N - 2 Faire\n"
            "        Si (I = 1) Ou (T[I] <> T[I - 1]) Alors\n"
            "            Gauche <- I + 1;\n"
            "            Droite <- N;\n"
            "            TantQue Gauche < Droite Faire\n"
            "                Somme <- T[I] + T[Gauche] + T[Droite];\n"
            "                Si Somme = 0 Alors\n"
            "                    NbTriplets <- NbTriplets + 1;\n"
            "                    Gauche <- Gauche + 1;\n"
            "                    Droite <- Droite - 1;\n"
            "                    TantQue (Gauche < Droite) Et (T[Gauche] = T[Gauche - 1]) Faire Gauche <- Gauche + 1; FinTantQue;\n"
            "                    TantQue (Gauche < Droite) Et (T[Droite] = T[Droite + 1]) Faire Droite <- Droite - 1; FinTantQue;\n"
            "                Sinon\n"
            "                    Si Somme < 0 Alors Gauche <- Gauche + 1;\n"
            "                    Sinon Droite <- Droite - 1;\n"
            "                    FinSi;\n"
            "                FinSi;\n"
            "            FinTantQue;\n"
            "        FinSi;\n"
            "    FinPour;\n\n"
            "    Ecrire(NbTriplets);\n"
            "Fin."
        ),
        "test_cases": p29_tests
    })

    # 30. Recherche dans une Matrice Triée 2D (Tableaux, Hard)
    def solve_saddleback(mat, target):
        n = len(mat)
        m = len(mat[0])
        row = 0
        col = m - 1
        while row < n and col >= 0:
            if mat[row][col] == target:
                return "1"
            elif mat[row][col] > target:
                col -= 1
            else:
                row += 1
        return "0"

    p30_tests = []
    p30_inputs = [
        ([[1, 4, 7, 11], [2, 5, 8, 12], [3, 6, 9, 16], [10, 13, 14, 17]], 5),
        ([[1, 4, 7, 11], [2, 5, 8, 12], [3, 6, 9, 16], [10, 13, 14, 17]], 20),
        ([[5]], 5),
        ([[5]], 3),
        ([[1, 2], [3, 4]], 3),
        ([[1, 2], [3, 4]], 5),
        ([[1, 3, 5], [7, 9, 11], [13, 15, 17]], 9),
        ([[1, 3, 5], [7, 9, 11], [13, 15, 17]], 8),
        ([[-10, -5], [-2, 4]], -5),
        ([[-10, -5], [-2, 4]], 0),
        ([[10, 20, 30], [40, 50, 60]], 50),
        ([[2, 4, 6, 8], [10, 12, 14, 16]], 14)
    ]
    for idx, (mat, target) in enumerate(p30_inputs):
        n = len(mat)
        m = len(mat[0])
        flat = []
        for row in mat:
            flat.extend(row)
        in_str = f"{n}\n{m}\n" + "\n".join(str(x) for x in flat) + f"\n{target}\n"
        p30_tests.append({
            "input": in_str,
            "expected_output": f"{solve_saddleback(mat, target)}\n",
            "is_public": idx < 2
        })

    problems.append({
        "title": "Recherche dans une Matrice Triée 2D",
        "topic": "Tableaux",
        "difficulty": "Hard",
        "description": (
            "### Recherche Linéaire 2D (Algorithme de la Selle)\n\n"
            "Étant donné une matrice `N x M` où chaque ligne est triée par ordre croissant de gauche à droite, et chaque colonne est triée de haut en bas, déterminez si une valeur `Cible` est présente en $O(N + M)$ sans parcourir toute la matrice.\n\n"
            "#### Format d'entrée\n"
            "- Ligne 1 : `N`\n"
            "- Ligne 2 : `M`\n"
            "- Les $N \\times M$ lignes suivantes : Éléments de la matrice ligne par ligne\n"
            "- Ligne suivante : L'entier `Cible`\n\n"
            "#### Format de sortie attendu\n"
            "- Affichez `1` si la valeur est trouvée, ou `0` sinon.\n\n"
            "#### Exemple concret\n"
            "**Entrée :**\n"
            "```\n"
            "4\n"
            "4\n"
            "1\n"
            "4\n"
            "7\n"
            "11\n"
            "2\n"
            "5\n"
            "8\n"
            "12\n"
            "3\n"
            "6\n"
            "9\n"
            "16\n"
            "10\n"
            "13\n"
            "14\n"
            "17\n"
            "5\n"
            "```\n"
            "**Sortie attendue :**\n"
            "```\n"
            "1\n"
            "```"
        ),
        "template_code": (
            "Algorithme RechercheMatriceTriee;\n"
            "Var\n"
            "    M : Tableau[1..20, 1..20] de Entier;\n"
            "    N, P, I, J, Cible, Ligne, Col, Trouve : Entier;\n"
            "Debut\n"
            "    Lire(N); Lire(P);\n"
            "    Pour I De 1 A N Faire\n"
            "        Pour J De 1 A P Faire Lire(M[I, J]); FinPour;\n"
            "    FinPour;\n"
            "    Lire(Cible);\n\n"
            "    Ligne <- 1;\n"
            "    Col <- P;\n"
            "    Trouve <- 0;\n"
            "    TantQue (Ligne <= N) Et (Col >= 1) Et (Trouve = 0) Faire\n"
            "        Si M[Ligne, Col] = Cible Alors\n"
            "            Trouve <- 1;\n"
            "        Sinon\n"
            "            Si M[Ligne, Col] > Cible Alors Col <- Col - 1;\n"
            "            Sinon Ligne <- Ligne + 1;\n"
            "            FinSi;\n"
            "        FinSi;\n"
            "    FinTantQue;\n\n"
            "    Ecrire(Trouve);\n"
            "Fin."
        ),
        "test_cases": p30_tests
    })

    return problems

def slugify(title):
    import re
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip('-')
    return s

def main():
    problems_data = generate_problems()
    print(f"Generated {len(problems_data)} problem definitions.")

    # 1. Write JSON files
    created_files = []
    start_id = 45
    for idx, p in enumerate(problems_data, start=start_id):
        fname = f"{idx:02d}-{slugify(p['title'])}.json"
        fpath = PROBLEMS_DIR / fname
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump({
                "title": p["title"],
                "topic": p["topic"],
                "difficulty": p["difficulty"],
                "description": p["description"],
                "template_code": p["template_code"],
                "is_published": True,
                "test_cases": p["test_cases"]
            }, f, ensure_ascii=False, indent=2)
            f.write("\n")
        created_files.append(fname)
        print(f"Saved: {fname} ({len(p['test_cases'])} tests: 2 public, 10 hidden).")

    # 2. Update manifest.json
    manifest_path = PROBLEMS_DIR / "manifest.json"
    manifest_files = []
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_files = json.load(f).get("files", [])
        except Exception:
            manifest_files = []
    
    for f in created_files:
        if f not in manifest_files:
            manifest_files.append(f)
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"files": manifest_files}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Updated manifest.json with total {len(manifest_files)} problem files.")

    # 3. Insert directly into PostgreSQL database
    with app.app_context():
        inserted_count = 0
        updated_count = 0
        for p_data in problems_data:
            existing = Problem.query.filter_by(title=p_data["title"]).first()
            if existing:
                existing.topic = p_data["topic"]
                existing.difficulty = p_data["difficulty"]
                existing.description = p_data["description"]
                existing.template_code = p_data["template_code"]
                existing.is_published = True
                # replace test cases
                TestCase.query.filter_by(problem_id=existing.id).delete()
                db.session.flush()
                for tc in p_data["test_cases"]:
                    db.session.add(TestCase(
                        problem_id=existing.id,
                        input_data=tc["input"],
                        expected_output=tc["expected_output"],
                        is_public=tc["is_public"]
                    ))
                updated_count += 1
            else:
                new_p = Problem(
                    title=p_data["title"],
                    topic=p_data["topic"],
                    difficulty=p_data["difficulty"],
                    description=p_data["description"],
                    template_code=p_data["template_code"],
                    is_published=True
                )
                db.session.add(new_p)
                db.session.flush()
                for tc in p_data["test_cases"]:
                    db.session.add(TestCase(
                        problem_id=new_p.id,
                        input_data=tc["input"],
                        expected_output=tc["expected_output"],
                        is_public=tc["is_public"]
                    ))
                inserted_count += 1

        db.session.commit()
        total_in_db = Problem.query.count()
        print(f"Database sync finished: {inserted_count} inserted, {updated_count} updated. Total problems in DB: {total_in_db}")

if __name__ == "__main__":
    main()
