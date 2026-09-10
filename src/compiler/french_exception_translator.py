import sys
import traceback
import re

COMPILER_ERROR_CATALOG = {
    "E1.1": {
        "title": "Erreur Lexicale — Caractère Non Reconnu",
        "category": "E1 Lexical",
        "description": "Symbole ou caractère non valide dans la syntaxe algorithmique (ex: caractères spéciaux ou guillemets incorrects)."
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
        "title": "Erreur d'Exécution — Boucle Infinie Détectée (Timeout)",
        "category": "E4 Exécution",
        "description": "Temps d'exécution ou nombre maximal d'instructions dépassé (possible boucle infinie)."
    },
    "E4.2": {
        "title": "Erreur d'Exécution — Récursion Infinie",
        "category": "E4 Exécution",
        "description": "Débordement de la pile d'appels par trop d'appels récursifs imbriqués."
    },
    "E4.3": {
        "title": "Erreur d'Exécution — Dépassement de Capacité Mémoire",
        "category": "E4 Exécution",
        "description": "Allocation mémoire excessive ou dépassement de quota (Out of Memory)."
    },
    "E4.4": {
        "title": "Erreur d'Exécution — Accès Hors Limites",
        "category": "E4 Exécution",
        "description": "Accès à un élément de tableau ou pointeur en dehors des bornes allouées."
    },
    "E4.5": {
        "title": "Erreur d'Exécution — Division par Zéro",
        "category": "E4 Exécution",
        "description": "Opération de division ou modulo effectuée avec un diviseur nul."
    },
    "E4.6": {
        "title": "Erreur d'Exécution — Déréférencement NIL",
        "category": "E4 Exécution",
        "description": "Tentative d'accès ou d'écriture via un pointeur non initialisé ou libéré (NIL)."
    }
}

def get_compiler_error_catalog():
    return COMPILER_ERROR_CATALOG

def translate_exception(exc, py_code="", algo_code="", include_lineno=False):
    """
    Translates Python execution exceptions into student-appropriate,
    French algorithmic domain messages without leaking internal symbols or tracebacks.
    Adheres strictly to the canonical [E4.x] error catalog.
    """
    lineno = None
    exc_info = sys.exc_info()
    if exc_info and exc_info[2]:
        tb = traceback.extract_tb(exc_info[2])
        for frame in reversed(tb):
            if frame.filename in ('<string>', '<exec>') or 'runner' in frame.filename or 'tmp' in frame.filename:
                if frame.lineno:
                    lineno = frame.lineno
                break

    raw_msg = str(exc)

    # Sanitize accidental internal symbols
    clean_detail = re.sub(r"Pointer\([^)]*\)", "variable", raw_msg)
    clean_detail = re.sub(r"_ref_\w+", "variable", clean_detail)
    clean_detail = re.sub(r"_b_\w+", "élément", clean_detail)
    clean_detail = re.sub(r"_algo_\w+", "opération", clean_detail)

    prefix = f"Ligne {lineno} " if (include_lineno and lineno is not None) else ""

    if isinstance(exc, (TimeoutError,)):
        return f"{prefix}[E4.1] Boucle infinie détectée (Temps/Instructions dépassés)."
    elif "Limite d'exécution dépassée" in raw_msg or "boucle infinie" in raw_msg:
        return f"{prefix}[E4.1] Boucle infinie détectée (Temps/Instructions dépassés)."
    elif isinstance(exc, RecursionError):
        return f"{prefix}[E4.2] Erreur de récursion infinie (Trop d'appels de sous-programmes)."
    elif isinstance(exc, MemoryError):
        return f"{prefix}[E4.3] Dépassement de capacité mémoire (Trop d'allocations)."
    elif isinstance(exc, IndexError):
        return f"{prefix}[E4.4] Accès au tableau expiré ou hors limites."
    elif isinstance(exc, ZeroDivisionError):
        return f"{prefix}[E4.5] Division par zéro impossible."
    elif isinstance(exc, TypeError):
        if "'NoneType'" in raw_msg or "NIL" in raw_msg or "object is not subscriptable" in raw_msg and "NoneType" in raw_msg:
            return f"{prefix}[E4.6] Utilisation d'un pointeur non initialisé (NIL) ou d'une valeur absente."
        elif "not supported between instances of 'str' and 'int'" in raw_msg:
            return f"{prefix}[E3.2] Impossible de comparer une Chaîne et un Entier."
        elif "not supported between instances of 'int' and 'str'" in raw_msg:
            return f"{prefix}[E3.2] Impossible de comparer un Entier et une Chaîne."
        elif "unsupported operand" in raw_msg:
            return f"{prefix}[E3.2] Opération impossible entre ces types: {clean_detail}"
        else:
            return f"{prefix}[E3.2] Incompatibilité de types dans l'instruction."
    elif isinstance(exc, ValueError):
        if "Type mismatch" in raw_msg:
            return f"{prefix}[E3.2] {clean_detail}"
        return f"{prefix}[E3.2] Valeur incorrecte fournie à l'instruction."
    elif isinstance(exc, NameError):
        var_match = re.search(r"name '(\w+)' is not defined", raw_msg)
        var_name = var_match.group(1) if var_match else "variable"
        if var_name.startswith('_'):
            return f"{prefix}[E3.1] Identificateur non reconnu ou variable non déclarée."
        return f"{prefix}[E3.1] Variable non déclarée ou inconnue: '{var_name}'"
    elif isinstance(exc, AttributeError):
        return f"{prefix}[E3.2] Champ ou propriété non valide pour cette structure."
    else:
        return f"{prefix}[E2.1] Erreur d'exécution: {clean_detail}"
