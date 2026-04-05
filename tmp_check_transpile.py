import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from compiler.lexer import lexer
from compiler.parser import parser

algo_code = """
// Definition d'un type Enregistrement
Type
    Etudiant = Enregistrement
        nom : Chaine;
        note : Reel;
    Fin;
Algorithme DemoComplete;
Var
    i, n : Entier;
    somme : Reel;
    e : Etudiant;
    continuer : Booleen;

Debut
    Ecrire("=== Demo Progressive AlgoCompiler ===\\n");
    
    // 1. Initialisation d'un Enregistrement
    e.nom := "Adel";
    e.note := 15.5;
    
    Si e.note >= 10 Alors
        Ecrire(e.nom, " est admis avec ", e.note, "/20\\n");
    Sinon
        Ecrire(e.nom, " est ajourne\\n");
    Finsi;

    // 2. Boucle Pour (Comptage vers l'avant)
    Ecrire("\\nDepart imminent :\\n");
    Pour i := 1 a 3 Faire
        Ecrire(i, "... ");
    FinPour;
    Ecrire("Decollage !\\n");

    // 3. Boucle Tant Que (Sommatoire)
    somme := 0;
    i := 1;
    TantQue i <= 5 Faire
        somme := somme + i;
        i := i + 1;
    FinTantQue;
    Ecrire("Somme des entiers de 1 a 5 = ", somme, "\\n");

    // 4. Boucle Repeter (Conditionnelle)
    n := 0;
    Repeter
        n := n + 1;
        Ecrire("Passage numero : ", n, "\\n");
    Jusqua n >= 3;

    continuer := Vrai;
    Si continuer Alors
        Ecrire("Programme termine avec succes.\\n");
    Finsi;
Fin.
"""

python_code = parser.parse(algo_code, lexer=lexer)
print(python_code)
