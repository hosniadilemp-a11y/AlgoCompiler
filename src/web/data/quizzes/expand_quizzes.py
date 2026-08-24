import json
import os

QUIZ_DIR = os.path.dirname(__file__)

tableaux_extra = [
    {
        "difficulty": "Easy",
        "concept": "Indice Tableau",
        "question": "Quel est l'indice du premier élément d'un tableau déclarée T[100] de taille N ?",
        "explanation": "Selon les conventions usuelles du cours, les indices commencent soit à 1 (1..N) soit à 0 (0..N-1).",
        "choices": ["0 ou 1 selon la convention du cours", "Toujours -1", "100", "N"],
        "answer": "0 ou 1 selon la convention du cours"
    },
    {
        "difficulty": "Medium",
        "concept": "Recherche Linéaire",
        "question": "Dans le pire des cas, combien de comparaisons nécessite la recherche séquentielle sur N éléments ?",
        "explanation": "Dans le pire des cas (élément en dernière position ou absent), on doit tester les N cases du tableau.",
        "choices": ["N comparaisons", "Log2(N) comparaisons", "1 comparaison", "N^2 comparaisons"],
        "answer": "N comparaisons"
    },
    {
        "difficulty": "Hard",
        "concept": "Complexité Dichotomie",
        "question": "Quelle est la complexité temporelle optimale d'une recherche dichotomique sur un tableau trié de 1024 éléments ?",
        "explanation": "La recherche dichotomique divisant l'espace par 2 à chaque étape, log2(1024) = 10 étapes au pire cas.",
        "choices": ["10 comparaisons au maximum", "1024 comparaisons", "512 comparaisons", "1 comparaison"],
        "answer": "10 comparaisons au maximum"
    },
    {
        "difficulty": "Medium",
        "concept": "Tri Sélection",
        "question": "Combien d'échanges d'éléments au maximum effectue le tri par sélection sur N éléments ?",
        "explanation": "Le tri par sélection fait N-1 échanges au maximum (un échange par position principale i).",
        "choices": ["O(N) échanges", "O(N^2) échanges", "O(Log N) échanges", "Aucun échange"],
        "answer": "O(N) échanges"
    },
    {
        "difficulty": "Easy",
        "concept": "Tableau 2D",
        "question": "Comment déclare-t-on une matrice de 5 lignes et 10 colonnes d'entiers ?",
        "explanation": "On indique les deux dimensions : T[1..5, 1..10] : Entier.",
        "choices": ["Var M[5, 10] : Entier;", "Var M[50] : Entier;", "Var M : Entier[5][10];", "Var M : Matrix(5,10);"],
        "answer": "Var M[5, 10] : Entier;"
    },
    {
        "difficulty": "Medium",
        "concept": "Tri à Bulles Optimisé",
        "question": "Comment le tri à bulles optimisé détecte-t-il qu'un tableau est déjà trié ?",
        "explanation": "Si lors d'un passage complet sur le tableau aucun échange n'a été effectué (booléen permute = Faux), le tableau est trié.",
        "choices": ["Si un passage s'effectue sans aucun échange d'éléments", "En comparant la première et dernière case", "En calculant la somme des éléments", "Le tri à bulles ne peut pas s'arrêter plus tôt"],
        "answer": "Si un passage s'effectue sans aucun échange d'éléments"
    },
    {
        "difficulty": "Hard",
        "concept": "Tri par Insertion",
        "question": "Quelle est la complexité du tri par insertion sur un tableau DÉJÀ trié ?",
        "explanation": "Si le tableau est déjà trié, la condition de la boucle interne est immédiatement fausse : complexité linéaire O(N).",
        "choices": ["O(N) (linéaire)", "O(N^2) (quadratique)", "O(N log N)", "O(1)"],
        "answer": "O(N) (linéaire)"
    },
    {
        "difficulty": "Easy",
        "concept": "Accès Mémoire",
        "question": "Pourquoi l'accès à un élément `T[i]` d'un tableau est-il en temps constant O(1) ?",
        "explanation": "Grâce à la mémoire contiguë : Adresse(T[i]) = Adresse(T[0]) + i * Taille(Element).",
        "choices": ["Car la mémoire est contiguë et l'adresse est calculable directement", "Parce que l'ordinateur devine l'élément", "Car les tableaux sont stockés dans le CPU", "C'est O(N) et non O(1)"],
        "answer": "Car la mémoire est contiguë et l'adresse est calculable directement"
    },
    {
        "difficulty": "Medium",
        "concept": "Matrice Diagonale",
        "question": "Dans une matrice M[N, N], quelle est la condition d'appartenance à la diagonale principale ?",
        "explanation": "Un élément appartient à la diagonale principale si son indice de ligne égale son indice de colonne (i = j).",
        "choices": ["i = j", "i + j = N + 1", "i > j", "i < j"],
        "answer": "i = j"
    },
    {
        "difficulty": "Hard",
        "concept": "Matrice Transposée",
        "question": "Si M est une matrice de taille N x M, quelle est la taille de sa transposée M^T ?",
        "explanation": "La transposée échange les lignes et les colonnes, sa taille est donc M x N.",
        "choices": ["Taille M x N", "Taille N x N", "Taille M x M", "Taille N * M"],
        "answer": "Taille M x N"
    },
    {
        "difficulty": "Easy",
        "concept": "Initialisation",
        "question": "Que contient un tableau local qui vient d'être déclaré sans initialisation ?",
        "explanation": "Un tableau non initialisé contient des valeurs arbitraires dites 'valeurs poubelles' (garbage values).",
        "choices": ["Des valeurs indéterminées (contenu antérieur de la RAM)", "Toujours des zéros", "Des valeurs NIL", "Une erreur de compilation"],
        "answer": "Des valeurs indéterminées (contenu antérieur de la RAM)"
    },
    {
        "difficulty": "Medium",
        "concept": "Recherche Min/Max",
        "question": "Pour trouver le minimum d'un tableau non trié de N éléments, combien de comparaisons sont nécessaires ?",
        "explanation": "Il faut comparer chaque élément avec le minimum courant, soit exactement N - 1 comparaisons.",
        "choices": ["N - 1 comparaisons", "N / 2 comparaisons", "Log2(N) comparaisons", "N^2 comparaisons"],
        "answer": "N - 1 comparaisons"
    },
    {
        "difficulty": "Hard",
        "concept": "Inversion de Tableau",
        "question": "Pour inverser sur place (in-place) un tableau de N éléments, quelle est la condition de la boucle de permutation ?",
        "explanation": "On échange T[i] avec T[N - i + 1] pour i allant de 1 jusqu'à N div 2.",
        "choices": ["Pour i de 1 à N div 2", "Pour i de 1 à N", "Pour i de 1 à N - 1", "Tant que i <> N"],
        "answer": "Pour i de 1 à N div 2"
    },
    {
        "difficulty": "Easy",
        "concept": "Taille Réelle vs Maximale",
        "question": "Quelle est la différence entre taille maximale et taille réelle d'un tableau ?",
        "explanation": "La taille maximale est la capacité réservée en mémoire (ex: 100), la taille réelle N est le nombre de cases réellement utilisées (ex: 15).",
        "choices": ["La taille maximale est la capacité allouée, la taille réelle est le nombre d'éléments occupés", "C'est la même chose", "La taille réelle est toujours plus grande", "La taille maximale varie pendant l'exécution"],
        "answer": "La taille maximale est la capacité allouée, la taille réelle est le nombre d'éléments occupés"
    },
    {
        "difficulty": "Medium",
        "concept": "Produit Matriciel",
        "question": "Pour multiplier une matrice A(N x P) par B(P x M), quelle est la taille de la matrice résultat C ?",
        "explanation": "Le produit produit une matrice de taille N x M avec P multiplications par élément de C.",
        "choices": ["Taille N x M", "Taille P x P", "Taille N x P", "Taille M x N"],
        "answer": "Taille N x M"
    },
    {
        "difficulty": "Hard",
        "concept": "Stabilité d'un Tri",
        "question": "Que signifie qu'un algorithme de tri est 'stable' ?",
        "explanation": "Un tri est stable s'il préserve l'ordre relatif initial des éléments ayant des clés égales.",
        "choices": ["Il préserve l'ordre relatif des éléments ayant des clés identiques", "Il ne plante jamais pendant l'exécution", "Il utilise O(1) mémoire supplémentaire", "Sa complexité est toujours O(N log N)"],
        "answer": "Il préserve l'ordre relatif des éléments ayant des clés identiques"
    },
    {
        "difficulty": "Easy",
        "concept": "Vecteur",
        "question": "En algorithmique, qu'appelle-t-on un 'Vecteur' ?",
        "explanation": "Un vecteur est la dénomination usuelle pour un tableau à une seule dimension (1D).",
        "choices": ["Un tableau à une dimension (1D)", "Un pointeur vers une fonction", "Une matrice 3D", "Une constante numérique"],
        "answer": "Un tableau à une dimension (1D)"
    },
    {
        "difficulty": "Medium",
        "concept": "Recherche Dichotomique",
        "question": "Si la cible x est inférieure à l'élément du milieu T[m] dans un tableau trié croissant, comment ajuste-t-on la borne droite d ?",
        "explanation": "On sait que x se trouve dans la partie gauche, donc d := m - 1.",
        "choices": ["d := m - 1", "d := m + 1", "g := m + 1", "g := m - 1"],
        "answer": "d := m - 1"
    },
    {
        "difficulty": "Hard",
        "concept": "Tri par Sélection",
        "question": "Quelle est la complexité du tri par sélection sur un tableau DÉJÀ trié ?",
        "explanation": "Le tri par sélection parcourt toujours toutes les paires pour trouver le minimum : complexité O(N^2) dans TOUS les cas.",
        "choices": ["O(N^2) dans tous les cas", "O(N) si trié", "O(N log N)", "O(1)"],
        "answer": "O(N^2) dans tous les cas"
    },
    {
        "difficulty": "Easy",
        "concept": "Parcours Matrice",
        "question": "Combien de boucles imbriquées sont nécessaires pour parcourir une matrice 2D N x M ?",
        "explanation": "Une boucle externe pour les lignes et une boucle interne pour les colonnes (2 boucles).",
        "choices": ["2 boucles imbriquées (ligne et colonne)", "1 seule boucle", "3 boucles imbriquées", "Autant de boucles que d'éléments"],
        "answer": "2 boucles imbriquées (ligne et colonne)"
    }
]

chaines_extra = [
    {
        "difficulty": "Easy",
        "concept": "Sentinelle",
        "question": "En langage C et systèmes bas niveau, quel caractère marque la fin d'une chaîne ?",
        "explanation": "La sentinelle '\\0' (octet nul, code ASCII 0) marque la fin d'une chaîne de caractères.",
        "choices": ["'\\0' (octet nul)", "' ' (espace)", "'\\n' (retour ligne)", "'.' (point)"],
        "answer": "'\\0' (octet nul)"
    },
    {
        "difficulty": "Medium",
        "concept": "Code ASCII Chiffre",
        "question": "Quel est le code ASCII du caractère chiffre '0' ?",
        "explanation": "Le code ASCII de '0' est 48 (colonne 3, ligne 0 : 3 * 16 + 0 = 48).",
        "choices": ["48", "0", "65", "32"],
        "answer": "48"
    },
    {
        "difficulty": "Hard",
        "concept": "Formule Table ASCII",
        "question": "Si un caractère se situe à la colonne C (0-7) et ligne L (0-15) de la table ASCII, quel est son code ?",
        "explanation": "La formule formelle est Code = (C * 16) + L.",
        "choices": ["(C * 16) + L", "(L * 16) + C", "C + L", "C * L"],
        "answer": "(C * 16) + L"
    },
    {
        "difficulty": "Easy",
        "concept": "Conversion Casse",
        "question": "Quelle est la différence numérique entre le code ASCII de 'a' (97) et 'A' (65) ?",
        "explanation": "97 - 65 = 32. L'écart entre majuscule et minuscule est de 32.",
        "choices": ["32", "10", "26", "16"],
        "answer": "32"
    },
    {
        "difficulty": "Medium",
        "concept": "Comparaison ASCII",
        "question": "Quelle est la valeur de l'expression booleenne ('a' > 'Z') en ordre ASCII ?",
        "explanation": "'a' a le code 97 et 'Z' a le code 90. Comme 97 > 90, l'expression est VRAI.",
        "choices": ["Vrai", "Faux", "Erreur de syntaxe", "Indéterminé"],
        "answer": "Vrai"
    },
    {
        "difficulty": "Hard",
        "concept": "Calcul de Chiffre",
        "question": "Comment convertir un caractère numérique '5' en valeur entière 5 en algorithmique ?",
        "explanation": "En soustrayant le code de '0' : Ord('5') - Ord('0') = 53 - 48 = 5.",
        "choices": ["Ord(c) - Ord('0')", "Ord(c) + 32", "Val(c) * 10", "Chr(c)"],
        "answer": "Ord(c) - Ord('0')"
    },
    {
        "difficulty": "Easy",
        "concept": "Fonction Longueur",
        "question": "Que retourne l'appel `Longueur(\"Algorithme\")` ?",
        "explanation": "La fonction `Longueur` compte le nombre de caractères (10 caractères dans \"Algorithme\").",
        "choices": ["10", "11", "9", "8"],
        "answer": "10"
    },
    {
        "difficulty": "Medium",
        "concept": "Concaténation",
        "question": "Quel est le résultat de `Concat(\"ENP\", \"EI\")` ?",
        "explanation": "La concaténation assemble les deux chaînes pour former \"ENPEI\".",
        "choices": ["\"ENPEI\"", "\"ENP EI\"", "\"ENPEI\\0\"", "\"ENP\""],
        "answer": "\"ENPEI\""
    },
    {
        "difficulty": "Hard",
        "concept": "Comparaison Lexicographique",
        "question": "Parmi les chaînes suivantes, laquelle est la plus PETITE selon l'ordre ASCII : \"ALGO\", \"Alpha\", \"algo\" ?",
        "explanation": "Les majuscules ('A'=65, 'L'=76) viennent avant les minuscules ('a'=97). Pour \"ALGO\" et \"Alpha\", le 2ème caractère 'L' (76) < 'l' (108). Donc \"ALGO\" est la plus petite.",
        "choices": ["\"ALGO\"", "\"Alpha\"", "\"algo\"", "Elles sont égales"],
        "answer": "\"ALGO\""
    },
    {
        "difficulty": "Easy",
        "concept": "Guillemets",
        "question": "Quelle est la convention entre 'A' et \"A\" en algorithmique ?",
        "explanation": "'A' entre guillemets simples est un Caractere (1 octet), \"A\" entre guillemets doubles est une Chaine.",
        "choices": ["'A' est un Caractere, \"A\" est une Chaine", "'A' et \"A\" sont identiques", "'A' est un nombre, \"A\" est un texte", "'A' n'est pas autorisé"],
        "answer": "'A' est un Caractere, \"A\" est une Chaine"
    },
    {
        "difficulty": "Medium",
        "concept": "Espace ASCII",
        "question": "Quel est le code ASCII du caractère espace ' ' ?",
        "explanation": "Le code ASCII du caractère espace est 32.",
        "choices": ["32", "0", "10", "13"],
        "answer": "32"
    },
    {
        "difficulty": "Hard",
        "concept": "Test Palindrome",
        "question": "Quelle condition vérifie qu'un mot de taille N est un palindrome pour la i-ème lettre (de 1 à N/2) ?",
        "explanation": "La i-ème lettre depuis le début mot[i] doit être égale à la i-ème lettre depuis la fin mot[N - i + 1].",
        "choices": ["mot[i] = mot[N - i + 1]", "mot[i] = mot[i + 1]", "mot[i] = mot[N - i]", "mot[i] = mot[1]"],
        "answer": "mot[i] = mot[N - i + 1]"
    },
    {
        "difficulty": "Easy",
        "concept": "Chaîne Vide",
        "question": "Quelle est la longueur de la chaîne vide \"\" ?",
        "explanation": "La chaîne vide ne contient aucun caractère, sa longueur est 0.",
        "choices": ["0", "1", "NIL", "-1"],
        "answer": "0"
    },
    {
        "difficulty": "Medium",
        "concept": "Conversion Majuscule",
        "question": "Si c est un caractère minuscule ('a'..'z'), quelle opération donne son équivalent majuscule ?",
        "explanation": "Chr(Ord(c) - 32) convertit le code d'une minuscule vers sa majuscule.",
        "choices": ["Chr(Ord(c) - 32)", "Chr(Ord(c) + 32)", "Ord(c) - 32", "c - 'A'"],
        "answer": "Chr(Ord(c) - 32)"
    },
    {
        "difficulty": "Hard",
        "concept": "Recherche de Sous-chaîne",
        "question": "Quelle est la complexité pire cas de la recherche d'un motif de taille M dans un texte de taille N (méthode naïve) ?",
        "explanation": "La méthode naïve compare le motif à chaque position possible du texte : O(N * M).",
        "choices": ["O(N * M)", "O(N + M)", "O(N log M)", "O(1)"],
        "answer": "O(N * M)"
    },
    {
        "difficulty": "Easy",
        "concept": "Fonction Chr",
        "question": "Que retourne la fonction `Chr(65)` ?",
        "explanation": "La fonction `Chr(code)` retourne le caractère correspondant au code ASCII transmis (65 -> 'A').",
        "choices": ["Le caractère 'A'", "Le nombre 65", "La chaîne \"65\"", "Une erreur"],
        "answer": "Le caractère 'A'"
    },
    {
        "difficulty": "Medium",
        "concept": "Fonction Ord",
        "question": "Que retourne la fonction `Ord('B')` ?",
        "explanation": "La fonction `Ord(caractere)` retourne le code ASCII ordinal du caractère ('B' -> 66).",
        "choices": ["66", "65", "2", "'b'"],
        "answer": "66"
    },
    {
        "difficulty": "Hard",
        "concept": "Compteur de Mots",
        "question": "Dans une chaîne sans espaces multiples, comment compter le nombre de mots ?",
        "explanation": "Le nombre de mots est égal au nombre d'espaces + 1 (pour une chaîne non vide).",
        "choices": ["Nombre d'espaces + 1", "Nombre de lettres div 5", "Longueur de la chaîne", "Nombre de voyelles"],
        "answer": "Nombre d'espaces + 1"
    },
    {
        "difficulty": "Easy",
        "concept": "Accès Caractère",
        "question": "Comment accéder au 3ème caractère de la chaîne `ch` ?",
        "explanation": "Par indexation directe : `ch[3]` (ou `ch[2]` selon l'index d'origine).",
        "choices": ["ch[3]", "ch.3", "Caractere(ch, 3)", "ch(3)"],
        "answer": "ch[3]"
    },
    {
        "difficulty": "Medium",
        "concept": "Caractère Chiffre",
        "question": "Quelle condition booléenne teste si un caractère c est un chiffre numérique ?",
        "explanation": "Le test vérifie si son code ASCII se trouve dans la plage '0'..'9' : (c >= '0') Et (c <= '9').",
        "choices": ["(c >= '0') Et (c <= '9')", "(c >= 48) Ou (c <= 57)", "c = Chiffre", "EstEntier(c)"],
        "answer": "(c >= '0') Et (c <= '9')"
    }
]

allocation_extra = [
    {
        "difficulty": "Easy",
        "concept": "Notion Pointeur",
        "question": "Qu'est-ce qu'un pointeur en mémoire RAM ?",
        "explanation": "Un pointeur est une variable qui contient l'adresse mémoire d'une autre variable.",
        "choices": ["Une variable contenant une adresse mémoire", "Un nombre entier positif", "Un tableau dynamique", "Une instruction de boucle"],
        "answer": "Une variable contenant une adresse mémoire"
    },
    {
        "difficulty": "Medium",
        "concept": "Déclaration Pointeur",
        "question": "Comment déclare-t-on un pointeur p vers un entier en algorithmique ?",
        "explanation": "La syntaxe du cours est `p : ↑Entier;` (ou `p : ^Entier;`).",
        "choices": ["p : ↑Entier;", "p : Pointeur(Entier);", "p : &Entier;", "p = new Entier;"],
        "answer": "p : ↑Entier;"
    },
    {
        "difficulty": "Hard",
        "concept": "Prise d'Adresse",
        "question": "Si x est une variable entière, quelle opération extrait son adresse mémoire pour l'affecter à p ?",
        "explanation": "L'opérateur d'adresse `&` extrait l'adresse : `p := &x;`.",
        "choices": ["p := &x;", "p := x↑;", "p := Allouer(x);", "p := *x;"],
        "answer": "p := &x;"
    },
    {
        "difficulty": "Easy",
        "concept": "Déréférencement",
        "question": "Que signifie la notation `p↑` (ou `*p`) ?",
        "explanation": "Elle déréférence le pointeur, c'est-à-dire qu'elle accède à la valeur stockée à l'adresse pointée par p.",
        "choices": ["Accéder à la valeur située à l'adresse p", "Multiplier p par lui-même", "Libérer la mémoire de p", "Augmenter l'adresse de p"],
        "answer": "Accéder à la valeur située à l'adresse p"
    },
    {
        "difficulty": "Medium",
        "concept": "Valeur NIL",
        "question": "Que représente la valeur spéciale `NIL` (ou `NULL`) pour un pointeur ?",
        "explanation": "NIL indique que le pointeur ne pointe vers aucun emplacement mémoire valide (pointeur nul).",
        "choices": ["Le pointeur ne pointe sur aucune adresse valide", "L'adresse zéro de la ROM", "Une valeur entière valant -1", "Une erreur système"],
        "answer": "Le pointeur ne pointe sur aucune adresse valide"
    },
    {
        "difficulty": "Hard",
        "concept": "Segmentation Fault",
        "question": "Que se passe-t-il si l'on tente d'exécuter `p↑ := 10;` alors que `p = NIL` ?",
        "explanation": "Le déréférencement d'un pointeur NIL provoque un crash mémoire appelé Segmentation Fault (Access Violation).",
        "choices": ["Crash du programme (Segmentation Fault)", "Le programme ignore l'instruction", "p prend automatiquement une nouvelle adresse", "10 est stocké dans la variable NIL"],
        "answer": "Crash du programme (Segmentation Fault)"
    },
    {
        "difficulty": "Easy",
        "concept": "Primitive Allouer",
        "question": "Que fait l'instruction `Allouer(p)` ?",
        "explanation": "Elle réserve un bloc mémoire en RAM dynamique de la taille du type pointé et stocke son adresse dans p.",
        "choices": ["Elle réserve un bloc mémoire dynamique et affecte son adresse à p", "Elle détruit la variable p", "Elle remet p à zéro", "Elle affiche l'adresse de p"],
        "answer": "Elle réserve un bloc mémoire dynamique et affecte son adresse à p"
    },
    {
        "difficulty": "Medium",
        "concept": "Primitive Liberer",
        "question": "Que fait l'instruction `Liberer(p)` ?",
        "explanation": "Elle restitue le bloc mémoire pointé par p au système pour réutilisation ultérieure.",
        "choices": ["Elle restitue la mémoire pointée par p au système", "Elle efface le nom de la variable p", "Elle met la valeur 0 dans p↑", "Elle ferme le programme"],
        "answer": "Elle restitue la mémoire pointée par p au système"
    },
    {
        "difficulty": "Hard",
        "concept": "Fuite Mémoire",
        "question": "Qu'est-ce qu'une 'Fuite Mémoire' (Memory Leak) ?",
        "explanation": "C'est l'omission de liberer un bloc mémoire avant de perdre l'unique pointeur qui y menait, la RAM restant bloquée.",
        "choices": ["Un bloc mémoire dynamique non libéré qui devient inaccessible", "Un virus qui lit les variables", "Une erreur de syntaxe à la compilation", "Une pile qui déborde"],
        "answer": "Un bloc mémoire dynamique non libéré qui devient inaccessible"
    },
    {
        "difficulty": "Easy",
        "concept": "Dangling Pointer",
        "question": "Qu'est-ce qu'un 'Pointeur Pendouillant' (Dangling Pointer) ?",
        "explanation": "Un pointeur qui contient encore l'adresse d'un bloc mémoire qui a déjà été libéré par `Liberer(p)`.",
        "choices": ["Un pointeur contenant l'adresse d'une mémoire déjà libérée", "Un pointeur valant NIL", "Un pointeur non encore déclaré", "Un pointeur vers une constante"],
        "answer": "Un pointeur contenant l'adresse d'une mémoire déjà libérée"
    },
    {
        "difficulty": "Medium",
        "concept": "Bonne Pratique Libération",
        "question": "Quelle est la bonne pratique immédiatement après avoir exécuté `Liberer(p)` ?",
        "explanation": "Réinitialiser le pointeur à NIL (`p := NIL;`) pour éviter les accès accidentels via un pointeur pendouillant.",
        "choices": ["Faire `p := NIL;`", "Re-faire `Allouer(p);`", "Effacer la variable p", "Rien de particulier"],
        "answer": "Faire `p := NIL;`"
    },
    {
        "difficulty": "Hard",
        "concept": "Taille d'un Pointeur",
        "question": "Quelle est la taille en mémoire d'une variable pointeur sur une architecture 64 bits ?",
        "explanation": "Sur une architecture 64 bits, toutes les adresses mémoire font 8 octets, quel que soit le type pointé.",
        "choices": ["8 octets (quelle que soit la taille du type pointé)", "La taille du type pointé", "4 octets", "Variable selon la valeur stockée"],
        "answer": "8 octets (quelle que soit la taille du type pointé)"
    },
    {
        "difficulty": "Easy",
        "concept": "Tableau Dynamique 1D",
        "question": "Comment alloue-t-on dynamiquement un tableau de N entiers pointé par T ?",
        "explanation": "On alloue un bloc de N entiers : `Allouer(T, N);`.",
        "choices": ["Allouer(T, N);", "T := Tableau[N];", "Allouer(T);", "T := &N;"],
        "answer": "Allouer(T, N);"
    },
    {
        "difficulty": "Medium",
        "concept": "Pointeur de Pointeurs",
        "question": "Pour déclarer une matrice dynamique 2D ligne par ligne, quel est le type du pointeur mat ?",
        "explanation": "Il faut un pointeur vers un tableau de pointeurs : `mat : ↑↑Entier;`.",
        "choices": ["mat : ↑↑Entier;", "mat : ↑Entier[2];", "mat : Matrix↑;", "mat : Array↑;"],
        "answer": "mat : ↑↑Entier;"
    },
    {
        "difficulty": "Hard",
        "concept": "Matrice Contiguë Dynamique",
        "question": "Si une matrice N x M est allouée dans un seul bloc contigu pointé par `mat : ↑Entier`, quelle est l'adresse de la case (i, j) ?",
        "explanation": "En indexation linéaire 0-based : `mat + (i * M + j)`.",
        "choices": ["mat + (i * M + j)", "mat + i + j", "mat[i][j]", "mat * i * j"],
        "answer": "mat + (i * M + j)"
    },
    {
        "difficulty": "Easy",
        "concept": "Arithmétique des Pointeurs",
        "question": "Si p est un `↑Entier` (4 octets) pointant à l'adresse 1000, quelle est l'adresse de `p + 1` ?",
        "explanation": "L'arithmétique des pointeurs avance du nombre d'octets du type pointé : 1000 + 4 = 1004.",
        "choices": ["1004", "1001", "1008", "1000"],
        "answer": "1004"
    },
    {
        "difficulty": "Medium",
        "concept": "Comparaison de Pointeurs",
        "question": "Que compare l'expression `p1 = p2` où p1 et p2 sont deux pointeurs ?",
        "explanation": "Elle compare si p1 et p2 contiennent la MÊME adresse mémoire (et non leurs valeurs pointées).",
        "choices": ["Si p1 et p2 contiennent la même adresse mémoire", "Si p1↑ = p2↑", "Si p1 et p2 ont le même nom", "Si p1 et p2 ont été alloués en même temps"],
        "answer": "Si p1 et p2 contiennent la même adresse mémoire"
    },
    {
        "difficulty": "Hard",
        "concept": "Allocation Échouée",
        "question": "Que retourne `Allouer(p)` si la mémoire RAM centrale est totalement saturée ?",
        "explanation": "Si la mémoire est saturée, le système ne peut allouer le bloc et retourne `p = NIL`.",
        "choices": ["p vaut NIL", "Le système redémarre", "p prend l'adresse -1", "Une valeur aléatoire"],
        "answer": "p vaut NIL"
    },
    {
        "difficulty": "Easy",
        "concept": "Opérateur Taille",
        "question": "Quelle fonction retourne le nombre d'octets consommés par un type de donnée ?",
        "explanation": "La fonction `Taille(Type)` (ou `sizeof(Type)`) retourne l'empreinte mémoire du type.",
        "choices": ["Taille(Type)", "Longueur(Type)", "Octets(Type)", "Ram(Type)"],
        "answer": "Taille(Type)"
    },
    {
        "difficulty": "Medium",
        "concept": "Pointeur Générique",
        "question": "Qu'est-ce qu'un pointeur générique ou universel (ex: `void*` en C) ?",
        "explanation": "Un pointeur capable de stocker n'importe quelle adresse sans spécifier le type de la donnée pointée.",
        "choices": ["Un pointeur pouvant contenir l'adresse de n'importe quel type de donnée", "Un pointeur qui s'alloue tout seul", "Un pointeur qui ne peut pas être libéré", "Un pointeur lisible uniquement"],
        "answer": "Un pointeur pouvant contenir l'adresse de n'importe quel type de donnée"
    }
]

actions_extra = [
    {
        "difficulty": "Easy",
        "concept": "Structure Procédure",
        "question": "Quelle est la structure d'entête d'une procédure en algorithmique ?",
        "explanation": "Une procédure s'entête avec `Procedure NomProc(paramètres);` et n'a pas de type de retour.",
        "choices": ["Procedure NomProc(param1 : Type1);", "Fonction NomProc() : Vide;", "Action NomProc() : Boolean;", "Programme NomProc;"],
        "answer": "Procedure NomProc(param1 : Type1);"
    },
    {
        "difficulty": "Medium",
        "concept": "Passage de Paramètre VAR",
        "question": "En algorithmique, quel mot-clé devant un paramètre indique un passage par référence/adresse ?",
        "explanation": "Le mot-clé `VAR` (ou `Ref`) devant un paramètre indique un passage par adresse.",
        "choices": ["VAR", "VAL", "REF", "OUT"],
        "answer": "VAR"
    },
    {
        "difficulty": "Hard",
        "concept": "Effet de Bord",
        "question": "Qu'appelle-t-on un 'Effet de Bord' (Side Effect) dans une fonction ?",
        "explanation": "C'est lorsqu'une fonction modifie une variable globale ou un état extérieur en plus de retourner son résultat.",
        "choices": ["Une modification d'état extérieur ou variable globale par la fonction", "Une erreur de division par zéro", "Une boucle infinie dans la fonction", "Un retour de type flottant"],
        "answer": "Une modification d'état extérieur ou variable globale par la fonction"
    },
    {
        "difficulty": "Easy",
        "concept": "Variable Globale",
        "question": "Où est déclarée une variable globale et quelle est sa portée ?",
        "explanation": "Déclarée au niveau de l'algorithme principal, elle est accessible dans tout le programme et toutes ses sous-actions.",
        "choices": ["Dans l'algorithme principal, accessible partout", "Dans une procédure, accessible dans cette procédure uniquement", "Dans une boucle uniquement", "Dans un fichier externe"],
        "answer": "Dans l'algorithme principal, accessible partout"
    },
    {
        "difficulty": "Medium",
        "concept": "Variable Locale",
        "question": "Que se passe-t-il si une variable locale porte le MÊME nom qu'une variable globale ?",
        "explanation": "La variable locale masquera (masquage/shadowing) la variable globale dans le corps de l'action.",
        "choices": ["La variable locale masque la variable globale dans l'action", "Une erreur de compilation survient", "La variable globale est effacée", "Les deux variables fusionnent"],
        "answer": "La variable locale masque la variable globale dans l'action"
    },
    {
        "difficulty": "Hard",
        "concept": "Récursivité",
        "question": "Quelle est la condition indispensable dans toute fonction récursive pour éviter un blocage ?",
        "explanation": "Un cas de base (condition d'arrêt) sans appel récursif.",
        "choices": ["Un cas de base (condition d'arrêt) non récursif", "Une boucle Pour", "Au moins 3 paramètres VAR", "Une variable globale"],
        "answer": "Un cas de base (condition d'arrêt) non récursif"
    },
    {
        "difficulty": "Easy",
        "concept": "Appel de Procédure",
        "question": "Comment appelle-t-on une procédure `AfficherMsg(m)` dans le programme principal ?",
        "explanation": "Directement comme une instruction autonome : `AfficherMsg(\"Bonjour\");`.",
        "choices": ["AfficherMsg(\"Bonjour\");", "x := AfficherMsg(\"Bonjour\");", "Ecrire(AfficherMsg(\"Bonjour\"));", "Retourner AfficherMsg;"],
        "answer": "AfficherMsg(\"Bonjour\");"
    },
    {
        "difficulty": "Medium",
        "concept": "Paramètres Effectifs vs Formels",
        "question": "Quelle est la différence entre paramètres formels et paramètres effectifs ?",
        "explanation": "Les paramètres formels sont les noms dans la définition de la sous-action, les effectifs sont les valeurs transmises lors de l'appel.",
        "choices": ["Formels = à la définition, Effectifs = à l'appel", "Formels = entiers, Effectifs = réels", "Formels = globaux, Effectifs = locaux", "C'est la même chose"],
        "answer": "Formels = à la définition, Effectifs = à l'appel"
    },
    {
        "difficulty": "Hard",
        "concept": "Dépassement de Pile Récursive",
        "question": "Que provoque une fonction récursive sans condition d'arrêt (récursion infinie) ?",
        "explanation": "Un dépassement de la pile d'exécution (Stack Overflow / RecursionError).",
        "choices": ["Un dépassement de pile (Stack Overflow)", "Une fuite mémoire RAM", "Un résultat valant zéro", "Une boucle infinie CPU sans erreur"],
        "answer": "Un dépassement de pile (Stack Overflow)"
    },
    {
        "difficulty": "Easy",
        "concept": "Type de Retour",
        "question": "Combien de valeurs une fonction standard peut-elle retourner directement via `Retourner` ?",
        "explanation": "Une fonction retourne UNE SEULE valeur directe. Pour en retourner plusieurs, on utilise des paramètres VAR.",
        "choices": ["Une seule valeur", "Plusieurs valeurs séparées par virgule", "Autant qu'on veut", "Aucune valeur"],
        "answer": "Une seule valeur"
    },
    {
        "difficulty": "Medium",
        "concept": "Procédure d'Échange",
        "question": "Pour écrire une procédure `Echanger(a, b)` qui permute 2 variables du programme principal, quel doit être le mode des paramètres ?",
        "explanation": "Les deux paramètres a et b doivent impérativement être transmis par adresse (`VAR a, b : Entier`).",
        "choices": ["Les deux par adresse (VAR a, b : Entier)", "Les deux par valeur", "Seulement le premier par VAR", "Peu importe"],
        "answer": "Les deux par adresse (VAR a, b : Entier)"
    },
    {
        "difficulty": "Hard",
        "concept": "Passage de Tableau à une Action",
        "question": "En algorithmique et en C, comment un tableau est-il transmis par défaut à une fonction ?",
        "explanation": "Un tableau est toujours transmis par adresse (adresse de son premier élément T[0]).",
        "choices": ["Toujours par adresse (pointeur vers le premier élément)", "Par copie intégrale de toutes les cases", "Par valeur uniquement", "Impossible de passer un tableau"],
        "answer": "Toujours par adresse (pointeur vers le premier élément)"
    },
    {
        "difficulty": "Easy",
        "concept": "Signature de Fonction",
        "question": "Qu'appelle-t-on la 'signature' ou 'prototype' d'une action paramétrée ?",
        "explanation": "La combinaison de son nom, du nombre et types de ses paramètres et de son type de retour.",
        "choices": ["Son nom, la liste et le type de ses paramètres et son type de retour", "Le code source complet de son corps", "Sa vitesse d'exécution", "L'auteur qui l'a écrite"],
        "answer": "Son nom, la liste et le type de ses paramètres et son type de retour"
    },
    {
        "difficulty": "Medium",
        "concept": "Procédure vs Fonction",
        "question": "Quand faut-il choisir une Procédure plutôt qu'une Fonction ?",
        "explanation": "Lorsqu'on doit modifier plusieurs variables sortantes ou réaliser une action d'affichage/E/S sans valeur de retour unique.",
        "choices": ["Lorsqu'on doit modifier plusieurs variables ou faire des E/S", "Quand la vitesse est prioritaire", "Quand il n'y a aucun paramètre", "Toujours"],
        "answer": "Lorsqu'on doit modifier plusieurs variables ou faire des E/S"
    },
    {
        "difficulty": "Hard",
        "concept": "Pile d'Appel",
        "question": "Quelle structure de données le système utilise-t-il pour gérer les empilements d'appels de fonctions et variables locales ?",
        "explanation": "Le système d'exploitation et l'exécuteur utilisent une Pile d'Appel (Call Stack).",
        "choices": ["La Pile d'Appel (Call Stack)", "Une File FIFO", "Un Tableau 2D", "Un Arbre binaire"],
        "answer": "La Pile d'Appel (Call Stack)"
    },
    {
        "difficulty": "Easy",
        "concept": "Mot-clé Fonction",
        "question": "Quelle est la syntaxe d'entête d'une fonction de calcul de carré d'un entier ?",
        "explanation": "`Fonction Carre(x : Entier) : Entier;`.",
        "choices": ["Fonction Carre(x : Entier) : Entier;", "Procedure Carre(x : Entier);", "Fonction Carre(x);", "Carre(x : Entier) -> Entier;"],
        "answer": "Fonction Carre(x : Entier) : Entier;"
    },
    {
        "difficulty": "Medium",
        "concept": "Modularité",
        "question": "Quel est le principal avantage de la programmation modulaire avec fonctions ?",
        "explanation": "La réutilisabilité du code, la lisibilité et la facilité de débogage ciblé.",
        "choices": ["Réutilisabilité, lisibilité et débogage simplifié", "Augmentation du nombre de lignes", "Suppression des variables", "Rendre le code secret"],
        "answer": "Réutilisabilité, lisibilité et débogage simplifié"
    },
    {
        "difficulty": "Hard",
        "concept": "Transparence Référentielle",
        "question": "Qu'est-ce qu'une fonction 'pure' (transparence référentielle) ?",
        "explanation": "Une fonction sans effet de bord qui retourne TOUJOURS le même résultat pour les mêmes arguments.",
        "choices": ["Une fonction sans effet de bord retournant le même résultat pour les mêmes arguments", "Une fonction écrite en C", "Une fonction sans paramètre", "Une fonction qui ne contient pas de boucles"],
        "answer": "Une fonction sans effet de bord retournant le même résultat pour les mêmes arguments"
    },
    {
        "difficulty": "Easy",
        "concept": "Appel de Fonction",
        "question": "Où peut-on placer l'appel d'une fonction `Somme(a, b)` ?",
        "explanation": "Dans toute expression de calcul, d'affectation ou d'affichage : `s := Somme(a, b);`.",
        "choices": ["Dans une expression ou une affectation `s := Somme(a, b);`", "Uniquement seule sur une ligne", "Dans la section Var", "Uniquement dans une boucle"],
        "answer": "Dans une expression ou une affectation `s := Somme(a, b);`"
    },
    {
        "difficulty": "Medium",
        "concept": "Durée de Vie",
        "question": "Quelle est la durée de vie d'une variable locale déclarée dans une fonction ?",
        "explanation": "Sa durée de vie commence à l'entrée de la fonction et se termine dès que la fonction s'achève.",
        "choices": ["Du début à la fin de l'exécution de la fonction", "Pendant toute la durée du programme", "1 seconde", "Jusqu'au prochain redémarrage"],
        "answer": "Du début à la fin de l'exécution de la fonction"
    }
]

small_extra_5 = [
    {
        "difficulty": "Easy",
        "concept": "Champs",
        "question": "Comment accède-t-on au champ 'age' de l'enregistrement 'e' ?",
        "explanation": "Par l'opérateur point : e.age.",
        "choices": ["e.age", "e->age", "e[age]", "age(e)"],
        "answer": "e.age"
    },
    {
        "difficulty": "Medium",
        "concept": "Structures Imbriquées",
        "question": "Peut-on déclarer un champ d'un enregistrement qui est lui-même un autre enregistrement ?",
        "explanation": "Oui, les enregistrements peuvent être imbriqués (ex: etudiant.adresse.codePostal).",
        "choices": ["Oui, les structures peuvent être imbriquées", "Non, c'est interdit", "Uniquement si ce sont des entiers", "Seulement 1 niveau"],
        "answer": "Oui, les structures peuvent être imbriquées"
    },
    {
        "difficulty": "Hard",
        "concept": "Tableau de Structures",
        "question": "Comment accède-t-on au champ 'nom' du 3ème étudiant d'un tableau promo ?",
        "explanation": "En combinant l'indice du tableau et le point de champ : promo[3].nom.",
        "choices": ["promo[3].nom", "promo.nom[3]", "nom(promo[3])", "promo->3.nom"],
        "answer": "promo[3].nom"
    },
    {
        "difficulty": "Easy",
        "concept": "Mot-clé Type",
        "question": "Quel mot-clé permet de définir un nouveau type enregistrement en algorithmique ?",
        "explanation": "On utilise `Type NomStructure = Enregistrement ... Fin Enregistrement;`.",
        "choices": ["Type", "Struct", "Class", "Define"],
        "answer": "Type"
    },
    {
        "difficulty": "Medium",
        "concept": "Copie d'Enregistrement",
        "question": "Que fait l'affectation `e1 := e2;` entre deux enregistrements de même type ?",
        "explanation": "Elle copie champ par champ l'intégralité des données de e2 dans e1.",
        "choices": ["Elle copie tous les champs de e2 dans e1", "Elle crée un pointeur", "Elle génère une erreur", "Elle échange e1 et e2"],
        "answer": "Elle copie tous les champs de e2 dans e1"
    }
]


def append_to_file(filename, new_items, target_min=30):
    filepath = os.path.join(QUIZ_DIR, filename)
    if not os.path.exists(filepath):
        print(f"File {filename} not found.")
        return

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    if isinstance(data, list):
        current_len = len(data)
        needed = max(0, target_min - current_len)
        items_to_add = new_items[:needed] if len(new_items) >= needed else new_items
        data.extend(items_to_add)
        new_len = len(data)
    else:
        qs = data.get('questions', [])
        current_len = len(qs)
        needed = max(0, target_min - current_len)
        items_to_add = new_items[:needed] if len(new_items) >= needed else new_items
        qs.extend(items_to_add)
        data['questions'] = qs
        new_len = len(qs)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"[{filename}] {current_len} -> {new_len} questions (Added {len(items_to_add)})")


if __name__ == '__main__':
    append_to_file('tableaux.json', tableaux_extra, 30)
    append_to_file('chaines.json', chaines_extra, 30)
    append_to_file('allocation.json', allocation_extra, 30)
    append_to_file('actions.json', actions_extra, 30)
    append_to_file('enregistrements.json', small_extra_5, 30)
    append_to_file('fichiers.json', small_extra_5, 30)
    append_to_file('listes_chainees.json', small_extra_5, 30)
    append_to_file('piles.json', small_extra_5, 30)
    append_to_file('files.json', small_extra_5, 30)
