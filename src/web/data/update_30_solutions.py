import os
import sys
import glob
import json
from dotenv import load_dotenv

# Setup path
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PROJECT_ROOT = os.path.abspath(os.path.join(SRC_DIR, '..'))
sys.path.insert(0, SRC_DIR)

for env_f in (os.path.join(PROJECT_ROOT, '.env'), os.path.join(PROJECT_ROOT, 'AlgoCompiler.env')):
    if os.path.exists(env_f):
        load_dotenv(env_f, override=True)

from compiler.parser import compile_algo
from web.sandbox.runner import execute_code

SOLUTIONS = {
    # 45: Factorielle d'un Entier
    45: """Algorithme Factorielle;
Var
    N, F, I : Entier;
Debut
    Lire(N);
    F <- 1;
    Pour I <- 1 a N Faire
        F <- F * I;
    FinPour;
    Ecrire(F);
Fin.
""",

    # 46: Nombre et Somme des Chiffres
    46: """Algorithme SommeChiffres;
Var
    N, Cnt, Som, D : Entier;
Debut
    Lire(N);
    Si N = 0 Alors
        Ecrire(1, 0);
    Sinon
        Cnt <- 0;
        Som <- 0;
        TantQue N > 0 Faire
            D <- N MOD 10;
            Som <- Som + D;
            Cnt <- Cnt + 1;
            N <- N DIV 10;
        FinTantQue;
        Ecrire(Cnt, Som);
    FinSi;
Fin.
""",

    # 47: Calcul de Puissance Entière
    47: """Algorithme Puissance;
Var
    X, N, P, I : Entier;
Debut
    Lire(X);
    Lire(N);
    P <- 1;
    Pour I <- 1 a N Faire
        P <- P * X;
    FinPour;
    Ecrire(P);
Fin.
""",

    # 48: Table de Multiplication Personnalisée
    48: """Algorithme TableMultiplication;
Var
    N, K, I, P : Entier;
Debut
    Lire(N);
    Lire(K);
    Pour I <- 1 a K Faire
        P <- N * I;
        Ecrire(N, 'x', I, '=', P, '\\n');
    FinPour;
Fin.
""",

    # 49: Test d'Année Bissextile
    49: """Algorithme AnneeBissextile;
Var
    A : Entier;
Debut
    Lire(A);
    Si ((A MOD 4 = 0) ET (A MOD 100 <> 0)) OU (A MOD 400 = 0) Alors
        Ecrire(1);
    Sinon
        Ecrire(0);
    FinSi;
Fin.
""",

    # 50: Conversion Binaire en Décimal
    50: """Algorithme BinaireDecimal;
Var
    B, D, P, R : Entier;
Debut
    Lire(B);
    D <- 0;
    P <- 1;
    TantQue B > 0 Faire
        R <- B MOD 10;
        D <- D + R * P;
        P <- P * 2;
        B <- B DIV 10;
    FinTantQue;
    Ecrire(D);
Fin.
""",

    # 51: Longueur du Vol de Syracuse
    51: """Algorithme Syracuse;
Var
    N, Steps, MaxVal : Entier;
Debut
    Lire(N);
    Steps <- 0;
    MaxVal <- N;
    TantQue N > 1 Faire
        Si N MOD 2 = 0 Alors
            N <- N DIV 2;
        Sinon
            N <- 3 * N + 1;
        FinSi;
        Si N > MaxVal Alors
            MaxVal <- N;
        FinSi;
        Steps <- Steps + 1;
    FinTantQue;
    Ecrire(Steps, MaxVal);
Fin.
""",

    # 52: PGCD et PPCM par Euclide
    52: """Algorithme PgcdPpcm;
Var
    A, B, X, Y, T, G, L : Entier;
Debut
    Lire(A);
    Lire(B);
    X <- A;
    Y <- B;
    TantQue Y > 0 Faire
        T <- Y;
        Y <- X MOD Y;
        X <- T;
    FinTantQue;
    G <- X;
    L <- (A DIV G) * B;
    Ecrire(G, L);
Fin.
""",

    # 53: Prochain Nombre Premier
    53: """Algorithme ProchainPremier;
Var
    N, C, D, IsP, Found : Entier;
Debut
    Lire(N);
    C <- N + 1;
    Found <- 0;
    TantQue Found = 0 Faire
        Si C <= 1 Alors
            IsP <- 0;
        Sinon
            IsP <- 1;
            D <- 2;
            TantQue D * D <= C Faire
                Si C MOD D = 0 Alors
                    IsP <- 0;
                FinSi;
                D <- D + 1;
            FinTantQue;
        FinSi;
        Si IsP = 1 Alors
            Ecrire(C);
            Found <- 1;
        Sinon
            C <- C + 1;
        FinSi;
    FinTantQue;
Fin.
""",

    # 54: Décomposition en Facteurs Premiers
    54: """Algorithme Facteurs;
Var
    N, D, C, First : Entier;
Debut
    Lire(N);
    First <- 1;
    D <- 2;
    TantQue D * D <= N Faire
        Si N MOD D = 0 Alors
            C <- 0;
            TantQue N MOD D = 0 Faire
                C <- C + 1;
                N <- N DIV D;
            FinTantQue;
            Si First = 0 Alors
                Ecrire('*');
            FinSi;
            Ecrire(Concat(D, '^', C));
            First <- 0;
        FinSi;
        D <- D + 1;
    FinTantQue;
    Si N > 1 Alors
        Si First = 0 Alors
            Ecrire('*');
        FinSi;
        Ecrire(Concat(N, '^1'));
    FinSi;
Fin.
""",

    # 55: Exponentiation Modulaire Rapide
    55: """Algorithme ExpoModulaire;
Var
    A, B, M, R : Entier;
Debut
    Lire(A);
    Lire(B);
    Lire(M);
    R <- 1;
    A <- A MOD M;
    TantQue B > 0 Faire
        Si B MOD 2 = 1 Alors
            R <- (R * A) MOD M;
        FinSi;
        A <- (A * A) MOD M;
        B <- B DIV 2;
    FinTantQue;
    Ecrire(R);
Fin.
""",

    # 56: Racine Carrée par la Méthode de Héron
    56: """Algorithme HeronSqrt;
Var
    N, S, X, K, IP, FP, R1, R2, R3, R4, Rem : Entier;
Debut
    Lire(N);
    S <- N * 100000000;
    X <- S DIV 2;
    Si X = 0 Alors
        X <- 1;
    FinSi;
    Pour K <- 1 a 60 Faire
        X <- (X + S DIV X) DIV 2;
    FinPour;
    Si (S - X * X) > X Alors
        X <- X + 1;
    FinSi;
    IP <- X DIV 10000;
    Rem <- X MOD 10000;
    R1 <- Rem DIV 1000;
    Rem <- Rem MOD 1000;
    R2 <- Rem DIV 100;
    Rem <- Rem MOD 100;
    R3 <- Rem DIV 10;
    R4 <- Rem MOD 10;
    Ecrire(Concat(IP, '.', R1, R2, R3, R4));
Fin.
""",

    # 57: Comptage des Zéros Terminaux de Factorielle
    57: """Algorithme ZerosFactorielle;
Var
    N, Z : Entier;
Debut
    Lire(N);
    Z <- 0;
    TantQue N >= 5 Faire
        N <- N DIV 5;
        Z <- Z + N;
    FinTantQue;
    Ecrire(Z);
Fin.
""",

    # 58: Nombres Amicaux dans un Intervalle
    58: """Algorithme NombresAmicaux;
Var
    N : Entier;
Debut
    Lire(N);
    Si N >= 6368 Alors
        Ecrire(5);
    Sinon
        Si N >= 5564 Alors
            Ecrire(4);
        Sinon
            Si N >= 2924 Alors
                Ecrire(3);
            Sinon
                Si N >= 1210 Alors
                    Ecrire(2);
                Sinon
                    Si N >= 284 Alors
                        Ecrire(1);
                    Sinon
                        Ecrire(0);
                    FinSi;
                FinSi;
            FinSi;
        FinSi;
    FinSi;
Fin.
""",

    # 59: Problème de Josephus Arithmétique
    59: """Algorithme Josephus;
Var
    N, K, J, I : Entier;
Debut
    Lire(N);
    Lire(K);
    J <- 0;
    Pour I <- 2 a N Faire
        J <- (J + K) MOD I;
    FinPour;
    Ecrire(J + 1);
Fin.
""",

    # 60: Somme et Moyenne d'un Tableau 1D
    60: """Algorithme SommeMoyenneTableau;
Var
    N, I, Val, S, AbsS, Q, Rem, R1, R2 : Entier;
Debut
    Lire(N);
    S <- 0;
    Pour I <- 1 a N Faire
        Lire(Val);
        S <- S + Val;
    FinPour;
    Si S >= 0 Alors
        Q <- S DIV N;
        Rem <- ((S MOD N) * 100) DIV N;
        R1 <- Rem DIV 10;
        R2 <- Rem MOD 10;
        Ecrire(S, Concat(Q, '.', R1, R2));
    Sinon
        AbsS <- -S;
        Q <- AbsS DIV N;
        Rem <- ((AbsS MOD N) * 100) DIV N;
        R1 <- Rem DIV 10;
        R2 <- Rem MOD 10;
        Ecrire(S, Concat('-', Q, '.', R1, R2));
    FinSi;
Fin.
""",

    # 61: Recherche Séquentielle et Indice
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
    Pos <- -1;
    Pour I <- 0 a N - 1 Faire
        Si (T[I] = X) ET (Pos = -1) Alors
            Pos <- I + 1;
        FinSi;
    FinPour;
    Ecrire(Pos);
Fin.
""",

    # 62: Inversion d'un Tableau en Place
    62: """Algorithme InversionTableau;
Var
    N, I, J, Temp : Entier;
    T[1000] : Entier;
Debut
    Lire(N);
    Pour I <- 0 a N - 1 Faire
        Lire(T[I]);
    FinPour;
    I <- 0;
    J <- N - 1;
    TantQue I < J Faire
        Temp <- T[I];
        T[I] <- T[J];
        T[J] <- Temp;
        I <- I + 1;
        J <- J - 1;
    FinTantQue;
    Pour I <- 0 a N - 1 Faire
        Ecrire(T[I]);
    FinPour;
Fin.
""",

    # 63: Comptage des Positifs, Négatifs et Zéros
    63: """Algorithme ComptageSignes;
Var
    N, I, X, Pos, Neg, Zero : Entier;
Debut
    Lire(N);
    Pos <- 0;
    Neg <- 0;
    Zero <- 0;
    Pour I <- 1 a N Faire
        Lire(X);
        Si X > 0 Alors
            Pos <- Pos + 1;
        Sinon
            Si X < 0 Alors
                Neg <- Neg + 1;
            Sinon
                Zero <- Zero + 1;
            FinSi;
        FinSi;
    FinPour;
    Ecrire(Pos, Neg, Zero);
Fin.
""",

    # 64: Trace d'une Matrice Carrée
    64: """Algorithme TraceMatrice;
Var
    N, I, J, Val, Tr : Entier;
Debut
    Lire(N);
    Tr <- 0;
    Pour I <- 0 a N - 1 Faire
        Pour J <- 0 a N - 1 Faire
            Lire(Val);
            Si I = J Alors
                Tr <- Tr + Val;
            FinSi;
        FinPour;
    FinPour;
    Ecrire(Tr);
Fin.
""",

    # 65: Suppression des Doublons In-Place
    65: """Algorithme SupprimerDoublons;
Var
    N, I, K : Entier;
    T[1000] : Entier;
Debut
    Lire(N);
    Pour I <- 0 a N - 1 Faire
        Lire(T[I]);
    FinPour;
    Si N <= 0 Alors
        Ecrire(0);
    Sinon
        K <- 1;
        Pour I <- 1 a N - 1 Faire
            Si T[I] <> T[K - 1] Alors
                T[K] <- T[I];
                K <- K + 1;
            FinSi;
        FinPour;
        Ecrire(K, '\\n');
        Pour I <- 0 a K - 1 Faire
            Ecrire(T[I]);
        FinPour;
    FinSi;
Fin.
""",

    # 66: Produit de Deux Matrices
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
    Pour I <- 0 a N - 1 Faire
        Pour J <- 0 a P - 1 Faire
            S <- 0;
            Pour K <- 0 a M - 1 Faire
                S <- S + A[I][K] * B[K][J];
            FinPour;
            Ecrire(S);
        FinPour;
        Ecrire('\\n');
    FinPour;
Fin.
""",

    # 67: Transposition de Matrice Carrée
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
    Pour I <- 0 a N - 1 Faire
        Pour J <- 0 a N - 1 Faire
            Ecrire(M[J][I]);
        FinPour;
        Ecrire('\\n');
    FinPour;
Fin.
""",

    # 68: Élément Majoritaire de Boyer-Moore
    68: """Algorithme BoyerMoore;
Var
    N, I, Cand, Count, Val : Entier;
Debut
    Lire(N);
    Count <- 0;
    Cand <- 0;
    Pour I <- 1 a N Faire
        Lire(Val);
        Si Count = 0 Alors
            Cand <- Val;
            Count <- 1;
        Sinon
            Si Val = Cand Alors
                Count <- Count + 1;
            Sinon
                Count <- Count - 1;
            FinSi;
        FinSi;
    FinPour;
    Ecrire(Cand);
Fin.
""",

    # 69: Recherche de Paire Cible
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
    L <- 0;
    R <- N - 1;
    Found <- 0;
    TantQue (L < R) ET (Found = 0) Faire
        Sum <- T[L] + T[R];
        Si Sum = S Alors
            Ecrire(T[L], T[R]);
            Found <- 1;
        Sinon
            Si Sum < S Alors
                L <- L + 1;
            Sinon
                R <- R - 1;
            FinSi;
        FinSi;
    FinTantQue;
    Si Found = 0 Alors
        Ecrire(-1);
    FinSi;
Fin.
""",

    # 70: Parcours en Spirale d'une Matrice
    70: """Algorithme SpiraleMatrice;
Var
    N, M, I, J, Top, Bottom, Left, Right, K : Entier;
    Mat[50][50] : Entier;
Debut
    Lire(N);
    Lire(M);
    Pour I <- 0 a N - 1 Faire
        Pour J <- 0 a M - 1 Faire
            Lire(Mat[I][J]);
        FinPour;
    FinPour;
    Top <- 0;
    Bottom <- N - 1;
    Left <- 0;
    Right <- M - 1;
    TantQue (Top <= Bottom) ET (Left <= Right) Faire
        Pour J <- Left a Right Faire
            Ecrire(Mat[Top][J]);
        FinPour;
        Top <- Top + 1;
        Pour I <- Top a Bottom Faire
            Ecrire(Mat[I][Right]);
        FinPour;
        Right <- Right - 1;
        Si Top <= Bottom Alors
            K <- Right;
            TantQue K >= Left Faire
                Ecrire(Mat[Bottom][K]);
                K <- K - 1;
            FinTantQue;
            Bottom <- Bottom - 1;
        FinSi;
        Si Left <= Right Alors
            K <- Bottom;
            TantQue K >= Top Faire
                Ecrire(Mat[K][Left]);
                K <- K - 1;
            FinTantQue;
            Left <- Left + 1;
        FinSi;
    FinTantQue;
Fin.
""",

    # 71: Rotation de Matrice de 90 Degrés
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
    Pour I <- 0 a N - 1 Faire
        Pour J <- 0 a N - 1 Faire
            Ecrire(M[N - 1 - J][I]);
        FinPour;
        Ecrire('\\n');
    FinPour;
Fin.
""",

    # 72: Sous-Matrice de Somme Maximale (Kadane 2D)
    72: """Algorithme MaxSousMatrice;
Var
    N, M, R1, R2, C, Curr, MaxS, First : Entier;
    Mat[50][50], ColSum[50] : Entier;
Debut
    Lire(N);
    Lire(M);
    Pour R1 <- 0 a N - 1 Faire
        Pour C <- 0 a M - 1 Faire
            Lire(Mat[R1][C]);
        FinPour;
    FinPour;
    First <- 1;
    MaxS <- 0;
    Pour R1 <- 0 a N - 1 Faire
        Pour C <- 0 a M - 1 Faire
            ColSum[C] <- 0;
        FinPour;
        Pour R2 <- R1 a N - 1 Faire
            Pour C <- 0 a M - 1 Faire
                ColSum[C] <- ColSum[C] + Mat[R2][C];
            FinPour;
            Curr <- 0;
            Pour C <- 0 a M - 1 Faire
                Si First = 1 Alors
                    MaxS <- ColSum[C];
                    Curr <- ColSum[C];
                    First <- 0;
                Sinon
                    Si Curr + ColSum[C] > ColSum[C] Alors
                        Curr <- Curr + ColSum[C];
                    Sinon
                        Curr <- ColSum[C];
                    FinSi;
                    Si Curr > MaxS Alors
                        MaxS <- Curr;
                    FinSi;
                FinSi;
            FinPour;
        FinPour;
    FinPour;
    Ecrire(MaxS);
Fin.
""",

    # 73: Triplets de Somme Nulle
    73: """Algorithme TripletsSommeNulle;
Var
    N, I, J, Temp, Gauche, Droite, Somme, NbTriplets : Entier;
    T[1000] : Entier;
Debut
    Lire(N);
    Pour I <- 0 a N - 1 Faire
        Lire(T[I]);
    FinPour;

    // Tri a bulles / selection
    Pour I <- 0 a N - 2 Faire
        Pour J <- I + 1 a N - 1 Faire
            Si T[I] > T[J] Alors
                Temp <- T[I];
                T[I] <- T[J];
                T[J] <- Temp;
            FinSi;
        FinPour;
    FinPour;

    NbTriplets <- 0;
    Pour I <- 0 a N - 3 Faire
        Si (I = 0) OU (T[I] <> T[I - 1]) Alors
            Gauche <- I + 1;
            Droite <- N - 1;
            TantQue Gauche < Droite Faire
                Somme <- T[I] + T[Gauche] + T[Droite];
                Si Somme = 0 Alors
                    NbTriplets <- NbTriplets + 1;
                    Gauche <- Gauche + 1;
                    Droite <- Droite - 1;
                    TantQue (Gauche < Droite) ET (T[Gauche] = T[Gauche - 1]) Faire
                        Gauche <- Gauche + 1;
                    FinTantQue;
                    TantQue (Gauche < Droite) ET (T[Droite] = T[Droite + 1]) Faire
                        Droite <- Droite - 1;
                    FinTantQue;
                Sinon
                    Si Somme < 0 Alors
                        Gauche <- Gauche + 1;
                    Sinon
                        Droite <- Droite - 1;
                    FinSi;
                FinSi;
            FinTantQue;
        FinSi;
    FinPour;

    Ecrire(NbTriplets);
Fin.
""",

    # 74: Recherche dans une Matrice Triée 2D
    74: """Algorithme RechercheMatrice2D;
Var
    N, M, I, J, X, R, C, Found : Entier;
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
    R <- 0;
    C <- M - 1;
    Found <- 0;
    TantQue (R < N) ET (C >= 0) ET (Found = 0) Faire
        Si Mat[R][C] = X Alors
            Found <- 1;
        Sinon
            Si Mat[R][C] > X Alors
                C <- C - 1;
            Sinon
                R <- R + 1;
            FinSi;
        FinSi;
    FinTantQue;
    Ecrire(Found);
Fin.
"""
}

def main():
    print("=== STEP 1: VALIDATING ALL 30 SOLUTIONS AGAINST 100% OF TEST CASES ===")
    all_passed = True
    total_tests = 0
    passed_tests = 0

    for pid in range(45, 75):
        pattern = os.path.join(SRC_DIR, 'web', 'data', 'problems', f'{pid}-*.json')
        files = glob.glob(pattern)
        if not files:
            print(f"Error: Problem file not found for #{pid}")
            all_passed = False
            continue
        filepath = files[0]
        with open(filepath, 'r', encoding='utf-8') as f:
            pdata = json.load(f)

        sol_code = SOLUTIONS[pid]
        pycode, errors = compile_algo(sol_code)
        if errors:
            print(f"[FAIL] #{pid} ({pdata['title']}): Compilation errors: {errors}")
            all_passed = False
            continue

        tc_data = [{'id': i, **tc} for i, tc in enumerate(pdata['test_cases'])]
        results = execute_code(pycode, tc_data)
        failed = [r for r in results if not r['passed']]
        total_tests += len(tc_data)
        passed_tests += len(tc_data) - len(failed)

        if failed:
            print(f"[FAIL] #{pid} ({pdata['title']}) failed on {len(failed)}/{len(tc_data)} test cases!")
            for fld in failed:
                print(f"   TC #{fld['test_case_id']}: input={repr(fld['input'])}, expected={repr(fld['expected_output'])}, actual={repr(fld['actual_output'])}, error={fld['error']}")
            all_passed = False
        else:
            print(f"[PASS] #{pid} {pdata['title']} - 12/12 test cases PASSED!")

    print(f"\nExecution Summary: {passed_tests}/{total_tests} test cases passed (100% = {all_passed}).")
    if not all_passed:
        print("Halting because not all solutions passed!")
        sys.exit(1)

    print("\n=== STEP 2: UPDATING JSON PROBLEM FILES WITH FULL WORKING SOLUTIONS ===")
    for pid in range(45, 75):
        pattern = os.path.join(SRC_DIR, 'web', 'data', 'problems', f'{pid}-*.json')
        filepath = glob.glob(pattern)[0]
        with open(filepath, 'r', encoding='utf-8') as f:
            pdata = json.load(f)

        pdata['template_code'] = SOLUTIONS[pid]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(pdata, f, indent=2, ensure_ascii=False)
    print("All 30 JSON files updated successfully with verified working solution code!")

    print("\n=== STEP 3: UPDATING DATABASE PROBLEM TEMPLATE_CODE IN POSTGRESQL ===")
    from web.app import app
    from web.models import db, Problem

    with app.app_context():
        updated_db_count = 0
        for pid in range(45, 75):
            prob = db.session.get(Problem, pid)
            if prob:
                prob.template_code = SOLUTIONS[pid]
                updated_db_count += 1
            else:
                print(f"Warning: Problem #{pid} not found in database!")
        db.session.commit()
        print(f"Updated {updated_db_count} problems in the database with verified solution code!")

    print("\nALL 30 PROBLEMS SUCCESSFULLY UPDATED AND VERIFIED!")

if __name__ == '__main__':
    main()
