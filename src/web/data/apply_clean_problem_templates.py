import os
import sys
import glob
import json
import re

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, SRC_DIR)

from compiler.parser import compile_algo
from web.app import app, db
from web.models import Problem

# Clean template for Problem 13
P13_TEMPLATE = """Type Maillon = Enregistrement
Debut
    idx  : Entier;
    suiv : ^Maillon;
Fin;

Type PileIdx = Enregistrement
Debut
    sommet : ^Maillon;
Fin;

Procedure Init(Var P : PileIdx)
Debut
    P.sommet := NIL;
Fin;

Procedure Empiler(Var P : PileIdx, i : Entier)
Var n : ^Maillon;
Debut
    n := allouer(taille(Maillon));
    n->idx := i;
    n->suiv := P.sommet;
    P.sommet := n;
Fin;

Procedure Depiler(Var P : PileIdx, Var i : Entier)
Var t : ^Maillon;
Debut
    t := P.sommet;
    i := t->idx;
    P.sommet := t->suiv;
    liberer(t);
Fin;

Fonction EstVide(P : PileIdx) : Booleen
Debut
    Retourner(P.sommet = NIL);
Fin;

Fonction Sommet(P : PileIdx) : Entier
Debut
    Retourner(P.sommet->idx);
Fin;

Algorithme NextGreater;
Var
    N, i, j : Entier;
    T[100000], R[100000] : Entier;
    P : PileIdx;
Debut
    Lire(N);
    Pour i := 1 a N Faire
        Lire(T[i]);
        R[i] := -1;
    FinPour;

    Init(P);

    // TODO: Parcourir le tableau pour trouver le Next Greater Element avec la pile
    // Pour i := 1 a N Faire
    //     tant que pile non vide et T[i] > T[Sommet(P)], remplir R[]
    //     Empiler(P, i)
    // FinPour;

    Pour i := 1 a N Faire
        Ecrire(R[i]);
        Si i < N Alors Ecrire(" " ); FinSi;
    FinPour;
Fin."""

CLEAN_TEMPLATES = {
    45: """Algorithme Factorielle;
Var
    N, F : Entier;
Debut
    Lire(N);

    // TODO: Calculer la factorielle de N et stocker le résultat dans F



    Ecrire(F);
Fin.""",

    46: """Algorithme SommeChiffres;
Var
    N, Cnt, Som : Entier;
Debut
    Lire(N);

    // TODO: Déterminer le nombre de chiffres (Cnt) et la somme des chiffres (Som) de N



    Ecrire(Cnt, Som);
Fin.""",

    47: """Algorithme Puissance;
Var
    X, N, P : Entier;
Debut
    Lire(X);
    Lire(N);

    // TODO: Calculer X élevé à la puissance N et stocker dans P



    Ecrire(P);
Fin.""",

    48: """Algorithme TableMultiplication;
Var
    N, K, I : Entier;
Debut
    Lire(N);
    Lire(K);

    // TODO: Afficher la table de multiplication de N de 1 à K (format: N x I = P)



Fin.""",

    49: """Algorithme AnneeBissextile;
Var
    A, Rep : Entier;
Debut
    Lire(A);

    // TODO: Déterminer si l'année A est bissextile (Rep <- 1 si bissextile, sinon 0)



    Ecrire(Rep);
Fin.""",

    50: """Algorithme BinaireDecimal;
Var
    B, D : Entier;
Debut
    Lire(B);

    // TODO: Convertir le nombre binaire B en son équivalent décimal D



    Ecrire(D);
Fin.""",

    51: """Algorithme Syracuse;
Var
    N, Steps, MaxVal : Entier;
Debut
    Lire(N);

    // TODO: Calculer le nombre d'étapes (Steps) et la valeur maximale atteinte (MaxVal)



    Ecrire(Steps, MaxVal);
Fin.""",

    52: """Algorithme PgcdPpcm;
Var
    A, B, G, L : Entier;
Debut
    Lire(A);
    Lire(B);

    // TODO: Calculer le PGCD (G) et le PPCM (L) de A et B



    Ecrire(G, L);
Fin.""",

    53: """Algorithme ProchainPremier;
Var
    N, P : Entier;
Debut
    Lire(N);

    // TODO: Trouver le plus petit nombre premier P strictement supérieur à N



    Ecrire(P);
Fin.""",

    54: """Algorithme Facteurs;
Var
    N : Entier;
Debut
    Lire(N);

    // TODO: Décomposer N en facteurs premiers et afficher le résultat (ex: 2^3*3^1)



Fin.""",

    55: """Algorithme ExpoModulaire;
Var
    A, B, M, R : Entier;
Debut
    Lire(A);
    Lire(B);
    Lire(M);

    // TODO: Calculer (A^B) mod M de manière efficace et stocker dans R



    Ecrire(R);
Fin.""",

    56: """Algorithme HeronSqrt;
Var
    N, S, X, K, IP, FP, R1, R2, R3, R4, Rem : Entier;
Debut
    Lire(N);

    // TODO: Calculer la racine carrée de N par la méthode de Héron (4 décimales)



    Ecrire(Concat(IP, '.', R1, R2, R3, R4));
Fin.""",

    57: """Algorithme ZerosFactorielle;
Var
    N, Z : Entier;
Debut
    Lire(N);

    // TODO: Calculer le nombre de zéros terminaux de N! et stocker dans Z



    Ecrire(Z);
Fin.""",

    58: """Algorithme NombresAmicaux;
Var
    N, Cnt : Entier;
Debut
    Lire(N);

    // TODO: Compter le nombre de paires de nombres amicaux dans [1, N]



    Ecrire(Cnt);
Fin.""",

    59: """Algorithme Josephus;
Var
    N, K, Survivant : Entier;
Debut
    Lire(N);
    Lire(K);

    // TODO: Trouver la position du survivant (1-based) pour N personnes avec pas K



    Ecrire(Survivant);
Fin.""",

    60: """Algorithme SommeMoyenneTableau;
Var
    T[1000] : Entier;
    N, I, S : Entier;
Debut
    Lire(N);
    Pour I <- 0 a N - 1 Faire
        Lire(T[I]);
    FinPour;

    // TODO: Calculer la somme et la moyenne du tableau (format: Somme Moyenne)



Fin.""",

    61: """Algorithme RechercheSequentielle;
Var
    N, I, X, Pos : Entier;
    T[1000] : Entier;
Debut
    Lire(N);
    Pour I <- 0 a N - 1 Faire
        Lire(T[I]);
    FinPour;
    Lire(X);

    // TODO: Trouver l'indice de la première occurrence de X dans T, ou -1



    Ecrire(Pos);
Fin.""",

    62: """Algorithme InversionTableau;
Var
    N, I, J, Temp : Entier;
    T[1000] : Entier;
Debut
    Lire(N);
    Pour I <- 0 a N - 1 Faire
        Lire(T[I]);
    FinPour;

    // TODO: Inverser le tableau T en place



    Pour I <- 0 a N - 1 Faire
        Ecrire(T[I]);
    FinPour;
Fin.""",

    63: """Algorithme ComptageSignes;
Var
    N, I, X, Pos, Neg, Zero : Entier;
Debut
    Lire(N);

    // TODO: Compter le nombre d'entiers positifs, négatifs et nuls (Pos, Neg, Zero)



    Ecrire(Pos, Neg, Zero);
Fin.""",

    64: """Algorithme TraceMatrice;
Var
    N, I, J, Val, Tr : Entier;
    M[50][50] : Entier;
Debut
    Lire(N);
    Pour I <- 0 a N - 1 Faire
        Pour J <- 0 a N - 1 Faire
            Lire(M[I][J]);
        FinPour;
    FinPour;

    // TODO: Calculer la trace de la matrice carrée M (somme des éléments diagonaux)



    Ecrire(Tr);
Fin.""",

    65: """Algorithme SupprimerDoublons;
Var
    N, I, K : Entier;
    T[1000] : Entier;
Debut
    Lire(N);
    Pour I <- 0 a N - 1 Faire
        Lire(T[I]);
    FinPour;

    // TODO: Supprimer les doublons en place dans T trié, puis afficher K et les K éléments uniques



Fin.""",

    66: """Algorithme ProduitMatrices;
Var
    N, M, P, I, J, K, S : Entier;
    A[50][50], B[50][50] : Entier;
Debut
    Lire(N);
    Lire(M);
    Lire(P);
    Pour I <- 0 a N - 1 Faire
        Pour J <- 0 a M - 1 Faire
            Lire(A[I][J]);
        FinPour;
    FinPour;
    Pour I <- 0 a M - 1 Faire
        Pour J <- 0 a P - 1 Faire
            Lire(B[I][J]);
        FinPour;
    FinPour;

    // TODO: Calculer le produit matriciel A x B et afficher la matrice résultante N x P



Fin.""",

    67: """Algorithme TranspositionMatrice;
Var
    N, I, J : Entier;
    M[50][50] : Entier;
Debut
    Lire(N);
    Pour I <- 0 a N - 1 Faire
        Pour J <- 0 a N - 1 Faire
            Lire(M[I][J]);
        FinPour;
    FinPour;

    // TODO: Transposer la matrice carrée M et afficher la matrice transposée



Fin.""",

    68: """Algorithme BoyerMoore;
Var
    N, I, Cand, Count, Val : Entier;
    T[1000] : Entier;
Debut
    Lire(N);
    Pour I <- 0 a N - 1 Faire
        Lire(T[I]);
    FinPour;

    // TODO: Trouver l'élément majoritaire selon l'algorithme de Boyer-Moore et stocker dans Cand



    Ecrire(Cand);
Fin.""",

    69: """Algorithme PaireCible;
Var
    N, I, S, L, R, Sum, Found : Entier;
    T[1000] : Entier;
Debut
    Lire(N);
    Pour I <- 0 a N - 1 Faire
        Lire(T[I]);
    FinPour;
    Lire(S);

    // TODO: Trouver deux éléments dont la somme vaut S, ou afficher -1



Fin.""",

    70: """Algorithme SpiraleMatrice;
Var
    N, M, I, J : Entier;
    Mat[50][50] : Entier;
Debut
    Lire(N);
    Lire(M);
    Pour I <- 0 a N - 1 Faire
        Pour J <- 0 a M - 1 Faire
            Lire(Mat[I][J]);
        FinPour;
    FinPour;

    // TODO: Afficher les éléments de la matrice selon un parcours en spirale horaire



Fin.""",

    71: """Algorithme RotationMatrice;
Var
    N, I, J : Entier;
    M[50][50] : Entier;
Debut
    Lire(N);
    Pour I <- 0 a N - 1 Faire
        Pour J <- 0 a N - 1 Faire
            Lire(M[I][J]);
        FinPour;
    FinPour;

    // TODO: Effectuer une rotation de 90 degrés dans le sens horaire et afficher la matrice



Fin.""",

    72: """Algorithme MaxSousMatrice;
Var
    N, M, R1, C, MaxS : Entier;
    Mat[50][50] : Entier;
Debut
    Lire(N);
    Lire(M);
    Pour R1 <- 0 a N - 1 Faire
        Pour C <- 0 a M - 1 Faire
            Lire(Mat[R1][C]);
        FinPour;
    FinPour;

    // TODO: Trouver la somme maximale d'une sous-matrice et stocker dans MaxS



    Ecrire(MaxS);
Fin.""",

    73: """Algorithme TripletsSommeNulle;
Var
    N, I, NbTriplets : Entier;
    T[1000] : Entier;
Debut
    Lire(N);
    Pour I <- 0 a N - 1 Faire
        Lire(T[I]);
    FinPour;

    // TODO: Compter le nombre de triplets (i, j, k) avec T[i] + T[j] + T[k] = 0



    Ecrire(NbTriplets);
Fin.""",

    74: """Algorithme RechercheMatrice2D;
Var
    N, M, I, J, X, Found : Entier;
    Mat[50][50] : Entier;
Debut
    Lire(N);
    Lire(M);
    Pour I <- 0 a N - 1 Faire
        Pour J <- 0 a M - 1 Faire
            Lire(Mat[I][J]);
        FinPour;
    FinPour;
    Lire(X);

    // TODO: Rechercher X dans la matrice triée (Found <- 1 si présent, sinon 0)



    Ecrire(Found);
Fin."""
}

def update_problem_13():
    path = os.path.join(SRC_DIR, 'web', 'data', 'problems', '13-next-greater-element.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
        data['template_code'] = P13_TEMPLATE
        with open(path, 'w', encoding='utf-8') as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)
        print("Updated 13-next-greater-element.json")

def update_problems_45_74():
    problems_dir = os.path.join(SRC_DIR, 'web', 'data', 'problems')
    for pid, tmpl in CLEAN_TEMPLATES.items():
        pattern = os.path.join(problems_dir, f'{pid}-*.json')
        matching = glob.glob(pattern)
        if not matching:
            print(f"Warning: No file found for problem #{pid}")
            continue
        filepath = matching[0]
        with open(filepath, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
        data['template_code'] = tmpl
        with open(filepath, 'w', encoding='utf-8') as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)
        print(f"Updated problem #{pid} JSON file with clean template.")

def update_templates_script():
    script_path = os.path.join(SRC_DIR, 'web', 'data', 'update_30_templates.py')
    # Generate TEMPLATES dict representation
    templates_code = "import json\nimport glob\nimport re\nimport os\n\nTEMPLATES = {\n"
    for pid, tmpl in sorted(CLEAN_TEMPLATES.items()):
        escaped = tmpl.replace('\\', '\\\\').replace('\"\"\"', '\\\"\\\"\\\"')
        templates_code += f'    {pid}: """{escaped}""",\n'
    templates_code += """}

def update_json_files():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    problems_dir = os.path.join(base_dir, 'problems')
    files = glob.glob(os.path.join(problems_dir, '*.json'))
    updated = 0
    for f in files:
        m = re.search(r'[/\\\\](\d+)-', f)
        if not m:
            continue
        pid = int(m.group(1))
        if pid in TEMPLATES:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
            data['template_code'] = TEMPLATES[pid]
            with open(f, 'w', encoding='utf-8') as fp:
                json.dump(data, fp, indent=2, ensure_ascii=False)
            updated += 1
    print(f"Updated {updated} JSON problem files with clean template skeletons.")

def update_db():
    import sys
    base_dir = os.path.abspath(os.path.dirname(__file__))
    src_dir = os.path.abspath(os.path.join(base_dir, '..', '..'))
    sys.path.insert(0, src_dir)
    from web.app import app, db
    from web.models import Problem

    with app.app_context():
        updated = 0
        for pid, tmpl in TEMPLATES.items():
            prob = db.session.get(Problem, pid)
            if prob:
                prob.template_code = tmpl
                updated += 1
        db.session.commit()
        print(f"Updated {updated} Problem records in the database.")

if __name__ == '__main__':
    update_json_files()
    update_db()
"""
    with open(script_path, 'w', encoding='utf-8') as fp:
        fp.write(templates_code)
    print("Updated update_30_templates.py with verified clean templates.")

def update_database():
    with app.app_context():
        updated = 0
        # Update problem 13 if exists in DB
        p13 = db.session.get(Problem, 13)
        if p13:
            p13.template_code = P13_TEMPLATE
            updated += 1
            print("Updated Problem #13 in database.")
        
        # Update problems 45-74 in DB
        for pid, tmpl in CLEAN_TEMPLATES.items():
            prob = db.session.get(Problem, pid)
            if prob:
                prob.template_code = tmpl
                updated += 1
                print(f"Updated Problem #{pid} in database.")
        
        db.session.commit()
        print(f"Total problems updated in database: {updated}")

if __name__ == '__main__':
    update_problem_13()
    update_problems_45_74()
    update_templates_script()
    update_database()
    print("\nALL PROBLEMS SKELETONS SUCCESSFULLY CLEANED AND UPDATED!")
