import sys
import traceback
import re

COMPILER_ERROR_CATALOG = {
    "E1.1": {
        "title": "Erreur Lexicale — Caractère Non Reconnu",
        "category": "E1 Lexical",
        "description": "Symbole ou caractère non valide dans la syntaxe algorithmique (ex: caractéristiques spéciales ou guillemets incorrects)."
    },
    "E1.2": {
        "title": "Erreur Lexicale — Chaîne Non Fermée",
        "category": "E1 Lexical",
        "description": "Une chaîne de caractères ouverte n'a pas été fermée par des guillemets."
    },
    "E2.1": {
        "title": "Erreur Syntaxique — Mot-clé ou Structure Invalide",
        "category": "E2 Syntaxe",
        "description": "Structure ou mot-clé non conforme à la grammaire algorithmique (ex: oubli d'un point-virgule, parenthèse, ou mot-clé DEBUT/FIN)."
    },
    "E2.2": {
        "title": "Erreur Syntaxique — Fin de Fichier Inattendue (EOF)",
        "category": "E2 Syntaxe",
        "description": "Fin de fichier prématurée. Vérifiez que toutes les structures (Pour, Si, TantQue, ALGORITHME...FIN) sont fermées."
    },
    "E2.3": {
        "title": "Erreur Syntaxique — Déclaration de Variables",
        "category": "E2 Syntaxe",
        "description": "Erreur de format dans la section VAR. Utilisez: nom_variable : TYPE;"
    },
    "E3.1": {
        "title": "Erreur Sémantique — Variable Non Déclarée",
        "category": "E3 Sémantique",
        "description": "Utilisation d'un identificateur non déclaré dans la section VAR."
    },
    "E3.2": {
        "title": "Erreur Sémantique — Incompatibilité de Types",
        "category": "E3 Sémantique",
        "description": "Affectation ou opération entre types incompatibles."
    },
    "E4.1": {
        "title": "Erreur d'Exécution — Dépassement de Tableau (Index Out of Bounds)",
        "category": "E4 Exécution",
        "description": "Accès à un indice de tableau hors des limites autorisées."
    },
    "E4.2": {
        "title": "Erreur d'Exécution — Division par Zéro",
        "category": "E4 Exécution",
        "description": "Division ou modulo effectué par zéro."
    },
    "E4.3": {
        "title": "Erreur d'Exécution — Déréférencement NIL",
        "category": "E4 Exécution",
        "description": "Accès ou écriture via un pointeur non alloué (NIL)."
    }
}

def get_compiler_error_catalog():
    return COMPILER_ERROR_CATALOG

def translate_exception(exc, py_code="", algo_code=""):
    """
    Translates Python execution exceptions into student-appropriate,
    French algorithmic domain messages without leaking internal symbols or tracebacks.
    """
    tb = traceback.extract_tb(sys.exc_info()[2])
    
    lineno = 1
    for frame in reversed(tb):
        if frame.filename in ('<string>', '<exec>') or 'runner' in frame.filename or 'tmp' in frame.filename:
            if frame.lineno:
                lineno = frame.lineno
            break

    exc_type = type(exc).__name__
    raw_msg = str(exc)

    # Sanitize any accidental internal symbols
    clean_detail = re.sub(r"Pointer\([^)]*\)", "variable", raw_msg)
    clean_detail = re.sub(r"_ref_\w+", "variable", clean_detail)
    clean_detail = re.sub(r"_b_\w+", "élément", clean_detail)
    clean_detail = re.sub(r"_algo_\w+", "opération", clean_detail)

    if isinstance(exc, IndexError):
        msg = f"Ligne {lineno} [E4.1] : Index hors limites — accès à un élément du tableau en dehors des bornes autorisées."
    elif isinstance(exc, TypeError):
        if "unsupported operand" in raw_msg or "can't multiply" in raw_msg:
            msg = f"Ligne {lineno} [E3.2] : Incompatibilité de types — opération entre types incompatibles."
        elif "'NoneType'" in raw_msg or "NIL" in raw_msg:
            msg = f"Ligne {lineno} [E4.3] : Utilisation d'un pointeur non initialisé (NIL) ou d'une valeur absente."
        else:
            msg = f"Ligne {lineno} [E3.2] : Incompatibilité de types dans l'instruction."
    elif isinstance(exc, ZeroDivisionError):
        msg = f"Ligne {lineno} [E4.2] : Division par zéro impossible (division ou modulo par 0)."
    elif isinstance(exc, RecursionError):
        msg = f"Ligne {lineno} [E4.0] : Dépassement de la capacité de récursion — boucle ou appel récursif infini."
    elif isinstance(exc, ValueError):
        if "Type mismatch" in raw_msg:
            msg = f"Ligne {lineno} [E3.2] : {clean_detail}"
        else:
            msg = f"Ligne {lineno} [E4.0] : Valeur incorrecte fournie à l'instruction."
    elif isinstance(exc, NameError):
        var_match = re.search(r"name '(\w+)' is not defined", raw_msg)
        var_name = var_match.group(1) if var_match else "variable"
        if var_name.startswith('_'):
            msg = f"Ligne {lineno} [E3.1] : Identificateur non reconnu ou variable non déclarée."
        else:
            msg = f"Ligne {lineno} [E3.1] : Identificateur '{var_name}' non reconnu ou variable non déclarée."
    elif isinstance(exc, AttributeError):
        msg = f"Ligne {lineno} [E3.2] : Champ ou propriété non valide pour cette structure."
    else:
        msg = f"Ligne {lineno} [E2.1] : Une erreur est survenue lors de l'exécution."

    return msg
