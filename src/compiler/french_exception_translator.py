import sys
import traceback
import re

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
        msg = f"Ligne {lineno} : Index hors limites — accès à un élément du tableau en dehors des bornes autorisées."
    elif isinstance(exc, TypeError):
        if "unsupported operand" in raw_msg or "can't multiply" in raw_msg:
            msg = f"Ligne {lineno} : Incompatibilité de types — opération entre types incompatibles."
        elif "'NoneType'" in raw_msg or "NIL" in raw_msg:
            msg = f"Ligne {lineno} : Utilisation d'un pointeur non initialisé (NIL) ou d'une valeur absente."
        else:
            msg = f"Ligne {lineno} : Incompatibilité de types dans l'instruction."
    elif isinstance(exc, ZeroDivisionError):
        msg = f"Ligne {lineno} : Division par zéro impossible (division ou modulo par 0)."
    elif isinstance(exc, RecursionError):
        msg = f"Ligne {lineno} : Dépassement de la capacité de récursion — boucle ou appel récursif infini."
    elif isinstance(exc, ValueError):
        if "Type mismatch" in raw_msg:
            msg = f"Ligne {lineno} : {clean_detail}"
        else:
            msg = f"Ligne {lineno} : Valeur incorrecte fournie à l'instruction."
    elif isinstance(exc, NameError):
        var_match = re.search(r"name '(\w+)' is not defined", raw_msg)
        var_name = var_match.group(1) if var_match else "variable"
        if var_name.startswith('_'):
            msg = f"Ligne {lineno} : Identificateur non reconnu ou variable non déclarée."
        else:
            msg = f"Ligne {lineno} : Identificateur '{var_name}' non reconnu ou variable non déclarée."
    elif isinstance(exc, AttributeError):
        msg = f"Ligne {lineno} : Champ ou propriété non valide pour cette structure."
    else:
        msg = f"Ligne {lineno} : Une erreur est survenue lors de l'exécution."

    return msg
