# Algo: Test_Magic_Transformation

# Helper functions (dependency order)
_algo_input_buffer = []
def _algo_read():
    global _algo_input_buffer
    while True:
        if _algo_input_buffer:
            return _algo_input_buffer.pop(0)
        try:
            line = input()
        except EOFError:
            return ''
        if line is None:
            return ''
        parts = str(line).strip().split()
        if parts:
            _algo_input_buffer.extend(parts)

def _algo_ecrire(*args):
    parts = []
    for a in args:
        s = _algo_to_string(a)
        # Display #0 as the visible null sentinel
        s = s.replace('#0', chr(0))
        s = s.replace('\\n', '\n').replace('\\t', '\t')
        parts.append(s)
    print(' '.join(parts), end='')

def _algo_to_string(val):
    if val is None: return 'NIL'
    if isinstance(val, bool): return 'Vrai' if val else 'Faux'
    if isinstance(val, list):
        res = ''
        for char in val:
            if char is None or char == '\0' or char == '#0': break
            res += str(char)
        return res
    return str(val)

def _algo_deref_to_list(target):
    # Dereference a Pointer to get its backing list
    if hasattr(target, 'base_var') and target.base_var is not None:
        return target.base_var
    if hasattr(target, 'get_target_container'):
        try: return target.get_target_container()
        except: pass
    return target

def _algo_assign_fixed_string(target_list, source_val):
    target_list = _algo_deref_to_list(target_list)
    if not isinstance(target_list, list):
        raise TypeError('Variable Chaine non initialisee. Declarez avec s[N]: Chaine.')
    limit = len(target_list)
    s_val = ''
    if hasattr(source_val, '_get_target_container'):
        targ = source_val._get_target_container()
        while hasattr(targ, '_get_target_container'): targ = targ._get_target_container()
        if isinstance(targ, list):
            s_val = _algo_to_string(targ[source_val.index:])
        else:
            s_val = _algo_to_string(source_val._get_string() if hasattr(source_val, '_get_string') else source_val._get())
    else:
        s_val = _algo_to_string(source_val)
    if limit > 0:
        s_val = s_val[:limit-1]
        for i in range(len(s_val)):
            target_list[i] = s_val[i]
        target_list[len(s_val)] = '#0'
        for i in range(len(s_val)+1, limit):
            target_list[i] = None
    return target_list

def _algo_longueur(val):
    return len(_algo_to_string(val))

def _algo_set_char(target_list, index, char_val):
    target_list = _algo_deref_to_list(target_list)
    if not isinstance(target_list, list):
        raise TypeError(f'Cannot set char: not a list (got {type(target_list).__name__})')
    idx = int(index)  # 0-based index
    if 0 <= idx < len(target_list):
        if char_val == '#0' or char_val is None:
            target_list[idx] = '#0'
        else:
            target_list[idx] = str(char_val)[0]
    return target_list

def _algo_get_char(target_list, index):
    target_list = _algo_deref_to_list(target_list)
    if isinstance(target_list, list):
        idx = int(index)  # 0-based index
        if 0 <= idx < len(target_list):
            c = target_list[idx]
            return c if c is not None and c != '#0' else '#0'
        return ''
    s = str(target_list)
    idx = int(index)
    return s[idx] if 0 <= idx < len(s) else ''

def _algo_concat(val1, val2):
    s1 = _algo_to_string(val1)
    s2 = _algo_to_string(val2)
    # Stop at #0 null terminator in plain strings
    s1 = s1.split('#0')[0] if '#0' in s1 else s1
    s2 = s2.split('#0')[0] if '#0' in s2 else s2
    return s1 + s2

def _algo_make_string(s, max_size=256):
    s = str(s) if not isinstance(s, str) else s
    s = s[:max_size - 1]  # leave room for #0
    arr = [None] * max_size
    for i, c in enumerate(s):
        arr[i] = c
    arr[len(s)] = '#0'
    return arr

def _algo_read_typed(current_val, input_val=None, target_type_name='CHAINE'):
    if input_val is None: input_val = _algo_read()
    t = target_type_name.upper()
    if 'CHAINE' in t:
        if isinstance(current_val, list):
            _algo_assign_fixed_string(current_val, input_val)
            return current_val
        return str(input_val)
    if 'BOOLEEN' in t or isinstance(current_val, bool):
        s = str(input_val).lower()
        if s in ['vrai', 'true', '1']: return True
        if s in ['faux', 'false', '0']: return False
        raise ValueError(f"Type mismatch: '{input_val}' n'est pas un Booleen valide.")
    elif 'ENTIER' in t or isinstance(current_val, int):
        try: return int(input_val)
        except:
            raise ValueError(f"Type mismatch: '{input_val}' n'est pas un Entier valide.")
    elif 'REEL' in t or isinstance(current_val, float):
        try: return float(input_val)
        except:
            raise ValueError(f"Type mismatch: '{input_val}' n'est pas un Reel valide.")
    return input_val

_algo_heap = {}
_algo_heap_next_addr = 50000

def _algo_allouer(size_in_bytes, element_size=1):
    global _algo_heap_next_addr
    addr = _algo_heap_next_addr
    _algo_heap_next_addr += size_in_bytes
    num_elements = size_in_bytes // element_size if element_size > 0 else size_in_bytes
    allocated_list = [None] * max(1, num_elements)
    _algo_heap[addr] = allocated_list
    _algo_vars_info[f'_heap_{addr}'] = {'addr': addr, 'size': size_in_bytes, 'element_size': element_size}
    ptr = Pointer(var_name=f'_heap_{addr}', namespace=_algo_heap, index=0, base_var=allocated_list)
    ptr._heap_addr = addr
    return ptr

def _algo_liberer(ptr):
    if ptr and hasattr(ptr, '_heap_addr'):
        addr = ptr._heap_addr
        if addr in _algo_heap:
            del _algo_heap[addr]
            ptr.base_var = None
            ptr.var_name = None

_algo_record_sizes = {'Cellule': 5}

def _algo_taille(type_name):
    t = type_name.lower()
    if 'pointeur' in t or t.startswith('^'): return 1
    if 'entier' in t: return 4
    if 'reel' in t: return 8
    if 'booleen' in t: return 1
    if 'caractere' in t: return 1
    if 'chaine' in t: return 1
    # User-defined record type — uses precomputed sizes
    if type_name in _algo_record_sizes: return _algo_record_sizes[type_name]
    return 4

def _algo_allouer_record(record_dict):
    global _algo_heap_next_addr
    addr = _algo_heap_next_addr
    _algo_heap_next_addr += 1
    _algo_heap[addr] = record_dict
    ptr = Pointer(var_name=None, namespace=None, index=0, base_var=record_dict)
    ptr._heap_addr = addr
    return ptr

global _algo_vars_info
_algo_vars_info = {"milieu.L": {"addr": 1000, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "milieu.rapide": {"addr": 1001, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "milieu.lent": {"addr": 1002, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "inverser.L": {"addr": 1003, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "inverser.suiv": {"addr": 1004, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "inverser.courant": {"addr": 1005, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "inverser.prec": {"addr": 1006, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "alterner.A": {"addr": 1007, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "alterner.B": {"addr": 1008, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "alterner.startA": {"addr": 1009, "size": 1, "element_size": 1, "type": "Booleen"}, "alterner.pb": {"addr": 1010, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "alterner.pa": {"addr": 1011, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "alterner.dernier": {"addr": 1012, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "alterner.tete": {"addr": 1013, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "alterner.tourA": {"addr": 1014, "size": 1, "element_size": 1, "type": "Booleen"}, "semiMagicTransformation.A": {"addr": 1015, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "semiMagicTransformation.B": {"addr": 1016, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "semiMagicTransformation.revB": {"addr": 1017, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "transformerPremiereMoitie.L": {"addr": 1018, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "transformerPremiereMoitie.temp": {"addr": 1019, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "transformerPremiereMoitie.suivant": {"addr": 1020, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "transformerPremiereMoitie.droite": {"addr": 1021, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "transformerPremiereMoitie.gauche": {"addr": 1022, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "transformerPremiereMoitie.m": {"addr": 1023, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "transformerDeuxiemeMoitie.L": {"addr": 1024, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "transformerDeuxiemeMoitie.temp": {"addr": 1025, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "transformerDeuxiemeMoitie.droite": {"addr": 1026, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "transformerDeuxiemeMoitie.gauche": {"addr": 1027, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "transformerDeuxiemeMoitie.m": {"addr": 1028, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "magicTransformation.L": {"addr": 1029, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "magicTransformation.resultat": {"addr": 1030, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "magicTransformation.temp": {"addr": 1031, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "magicTransformation.deuxieme": {"addr": 1032, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "magicTransformation.premiere": {"addr": 1033, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "magicTransformation.m": {"addr": 1034, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "resultat": {"addr": 1035, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "L": {"addr": 1036, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "curr": {"addr": 1037, "size": 1, "element_size": 1, "type": "POINTEUR_Cellule"}, "i": {"addr": 1038, "size": 4, "element_size": 4, "type": "Entier"}}


class Pointer:
    def __init__(self, var_name=None, namespace=None, index=0, base_var=None, alloc_name=None):
        self.var_name = var_name
        self.namespace = namespace if namespace is not None else {}
        self.index = index
        self.base_var = base_var
        self.alloc_name = alloc_name if alloc_name is not None else var_name

    def _get_target_container(self):
        # base_var takes priority — used for record-backed pointers from _algo_allouer_record
        if self.base_var is not None:
            return self.base_var
        # Only after checking base_var do we apply the NIL check on var_name
        if self.var_name is None:
            raise ValueError("Cannot dereference NIL pointer")
        if self.var_name in self.namespace:
            return self.namespace[self.var_name]
        elif self.var_name in globals():
            return globals()[self.var_name]
        else:
            raise NameError(f"Variable '{self.var_name}' not found")

    def _get(self):
        target = self._get_target_container()
        if isinstance(target, list):
            if not (0 <= self.index < len(target)):
                raise IndexError(f"Segmentation fault: Access out of bounds at index {self.index}")
            return target[self.index]
        if self.index != 0:
             raise IndexError("Segmentation fault: Pointer arithmetic on scalar variable out of bounds")
        return target

    def _get_string(self):
        target = self._get_target_container()
        if isinstance(target, list):
            if not (0 <= self.index < len(target)): return ""
            return _algo_to_string(target[self.index:])
        return str(target)

    
    def _set(self, value):
        target = self._get_target_container()
        if isinstance(target, list):
            if not (0 <= self.index < len(target)):
                raise IndexError(f"Segmentation fault: Write out of bounds at index {self.index}")
            target[self.index] = value
        else:
            if self.index != 0:
                 raise IndexError("Segmentation fault: Pointer arithmetic on scalar variable out of bounds")
            if self.var_name in self.namespace:
                self.namespace[self.var_name] = value
            else:
                globals()[self.var_name] = value
    
    def _assign(self, other):
        # Mutates this pointer to point to what 'other' points to (used for Var parameters)
        if isinstance(other, Pointer):
            self.var_name = other.var_name
            self.namespace = other.namespace
            self.index = other.index
            self.base_var = other.base_var
            self.alloc_name = getattr(other, 'alloc_name', other.var_name)
            if hasattr(other, '_heap_addr'):
                self._heap_addr = getattr(other, '_heap_addr')
            elif hasattr(self, '_heap_addr'):
                delattr(self, '_heap_addr')
        elif other is None:
            self.var_name = None
            self.namespace = {}
            self.index = 0
            self.base_var = None
            self.alloc_name = None
            if hasattr(self, '_heap_addr'):
                delattr(self, '_heap_addr')
        else:
             raise TypeError("Cannot assign non-pointer to pointer via _assign")

    def _clone(self):
        new_ptr = Pointer(self.var_name, self.namespace, self.index, self.base_var, getattr(self, 'alloc_name', self.var_name))
        if hasattr(self, '_heap_addr'):
            new_ptr._heap_addr = self._heap_addr
        return new_ptr

    def __add__(self, offset):
        return Pointer(self.var_name, self.namespace, self.index + int(offset), self.base_var, getattr(self, 'alloc_name', self.var_name))

    def __sub__(self, offset):
        return Pointer(self.var_name, self.namespace, self.index - int(offset), self.base_var, getattr(self, 'alloc_name', self.var_name))

    def __eq__(self, other):
        if other is None:
            # If it has a heap address or base_var, it's not NIL
            if hasattr(self, '_heap_addr') or self.base_var is not None:
                return False
            return self.var_name is None
        if isinstance(other, Pointer):
            # Check for heap address equality if both have it
            if hasattr(self, '_heap_addr') and hasattr(other, '_heap_addr'):
                return self._heap_addr + self.index == other._heap_addr + other.index
            return (self.var_name == other.var_name and 
                    self.index == other.index and 
                    id(self.base_var) == id(other.base_var))
        return False
    
    def __str__(self):
        if hasattr(self, '_heap_addr'):
            return f"@{self._heap_addr + self.index}"
        if self.var_name is None:
            return "NIL"
        try:
            lookup_name = self.alloc_name if hasattr(self, 'alloc_name') and self.alloc_name else self.var_name
            if lookup_name in _algo_vars_info:
                info = _algo_vars_info[lookup_name]
                base = info['addr']
                stride = info.get('element_size', 1)
                addr = base + (self.index * stride)
                return f"@{addr}"
            else:
                return f"@{lookup_name}+{self.index}"

        except:
            return "UNKNOWN"

    def __repr__(self):
        return str(self)

    def __getitem__(self, i):
        return (self + i)._get()

    def __setitem__(self, i, value):
        (self + i)._set(value)


L = Pointer("L", globals())
resultat = Pointer("resultat", globals()) # POINTEUR_Cellule
curr = Pointer("curr", globals()) # POINTEUR_Cellule
i = 0 # Entier


def milieu(L):
    L = L._clone() if hasattr(L, '_clone') else L
    lent = Pointer("lent", locals())
    rapide = Pointer("rapide", locals()) # POINTEUR_Cellule

    if L == None:
        return (None)
    _tmp_lent = L
    lent._assign(Pointer("lent_ptr_src", locals(), index=0, base_var=_tmp_lent) if isinstance(_tmp_lent, list) and not hasattr(_tmp_lent, '_get_target_container') else _tmp_lent)
    _tmp_rapide = L
    rapide._assign(Pointer("rapide_ptr_src", locals(), index=0, base_var=_tmp_rapide) if isinstance(_tmp_rapide, list) and not hasattr(_tmp_rapide, '_get_target_container') else _tmp_rapide)
    while rapide != None and (rapide)._get()['suiv'] != None:
        _tmp_lent = (lent)._get()['suiv']
        lent._assign(Pointer("lent_ptr_src", locals(), index=0, base_var=_tmp_lent) if isinstance(_tmp_lent, list) and not hasattr(_tmp_lent, '_get_target_container') else _tmp_lent)
        _tmp_rapide = ((rapide)._get()['suiv'])._get()['suiv']
        rapide._assign(Pointer("rapide_ptr_src", locals(), index=0, base_var=_tmp_rapide) if isinstance(_tmp_rapide, list) and not hasattr(_tmp_rapide, '_get_target_container') else _tmp_rapide)
    return (lent)

def inverser(L):
    L = L._clone() if hasattr(L, '_clone') else L
    prec = Pointer("prec", locals())
    courant = Pointer("courant", locals())
    suiv = Pointer("suiv", locals()) # POINTEUR_Cellule

    _tmp_prec = None
    prec._assign(Pointer("prec_ptr_src", locals(), index=0, base_var=_tmp_prec) if isinstance(_tmp_prec, list) and not hasattr(_tmp_prec, '_get_target_container') else _tmp_prec)
    _tmp_courant = L
    courant._assign(Pointer("courant_ptr_src", locals(), index=0, base_var=_tmp_courant) if isinstance(_tmp_courant, list) and not hasattr(_tmp_courant, '_get_target_container') else _tmp_courant)
    while courant != None:
        _tmp_suiv = (courant)._get()['suiv']
        suiv._assign(Pointer("suiv_ptr_src", locals(), index=0, base_var=_tmp_suiv) if isinstance(_tmp_suiv, list) and not hasattr(_tmp_suiv, '_get_target_container') else _tmp_suiv)
        _tmp_val = prec
        (courant)._get()['suiv'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
        _tmp_prec = courant
        prec._assign(Pointer("prec_ptr_src", locals(), index=0, base_var=_tmp_prec) if isinstance(_tmp_prec, list) and not hasattr(_tmp_prec, '_get_target_container') else _tmp_prec)
        _tmp_courant = suiv
        courant._assign(Pointer("courant_ptr_src", locals(), index=0, base_var=_tmp_courant) if isinstance(_tmp_courant, list) and not hasattr(_tmp_courant, '_get_target_container') else _tmp_courant)
    return (prec)

def alterner(A, B, startA):
    A = A._clone() if hasattr(A, '_clone') else A
    B = B._clone() if hasattr(B, '_clone') else B
    tete = Pointer("tete", locals())
    dernier = Pointer("dernier", locals())
    pa = Pointer("pa", locals())
    pb = Pointer("pb", locals()) # POINTEUR_Cellule
    tourA = False # Booleen

    if A == None:
        return (B)
    if B == None:
        return (A)
    _tmp_tete = None
    tete._assign(Pointer("tete_ptr_src", locals(), index=0, base_var=_tmp_tete) if isinstance(_tmp_tete, list) and not hasattr(_tmp_tete, '_get_target_container') else _tmp_tete)
    _tmp_dernier = None
    dernier._assign(Pointer("dernier_ptr_src", locals(), index=0, base_var=_tmp_dernier) if isinstance(_tmp_dernier, list) and not hasattr(_tmp_dernier, '_get_target_container') else _tmp_dernier)
    _tmp_pa = A
    pa._assign(Pointer("pa_ptr_src", locals(), index=0, base_var=_tmp_pa) if isinstance(_tmp_pa, list) and not hasattr(_tmp_pa, '_get_target_container') else _tmp_pa)
    _tmp_pb = B
    pb._assign(Pointer("pb_ptr_src", locals(), index=0, base_var=_tmp_pb) if isinstance(_tmp_pb, list) and not hasattr(_tmp_pb, '_get_target_container') else _tmp_pb)
    tourA = startA
    while pa != None and pb != None:
        if tourA:
            if dernier == None:
                _tmp_tete = pa
                tete._assign(Pointer("tete_ptr_src", locals(), index=0, base_var=_tmp_tete) if isinstance(_tmp_tete, list) and not hasattr(_tmp_tete, '_get_target_container') else _tmp_tete)
            else:
                _tmp_val = pa
                (dernier)._get()['suiv'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
            _tmp_dernier = pa
            dernier._assign(Pointer("dernier_ptr_src", locals(), index=0, base_var=_tmp_dernier) if isinstance(_tmp_dernier, list) and not hasattr(_tmp_dernier, '_get_target_container') else _tmp_dernier)
            _tmp_pa = (pa)._get()['suiv']
            pa._assign(Pointer("pa_ptr_src", locals(), index=0, base_var=_tmp_pa) if isinstance(_tmp_pa, list) and not hasattr(_tmp_pa, '_get_target_container') else _tmp_pa)
        else:
            if dernier == None:
                _tmp_tete = pb
                tete._assign(Pointer("tete_ptr_src", locals(), index=0, base_var=_tmp_tete) if isinstance(_tmp_tete, list) and not hasattr(_tmp_tete, '_get_target_container') else _tmp_tete)
            else:
                _tmp_val = pb
                (dernier)._get()['suiv'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
            _tmp_dernier = pb
            dernier._assign(Pointer("dernier_ptr_src", locals(), index=0, base_var=_tmp_dernier) if isinstance(_tmp_dernier, list) and not hasattr(_tmp_dernier, '_get_target_container') else _tmp_dernier)
            _tmp_pb = (pb)._get()['suiv']
            pb._assign(Pointer("pb_ptr_src", locals(), index=0, base_var=_tmp_pb) if isinstance(_tmp_pb, list) and not hasattr(_tmp_pb, '_get_target_container') else _tmp_pb)
        tourA = not (tourA)
    if pa != None:
        _tmp_val = pa
        (dernier)._get()['suiv'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    else:
        if pb != None:
            _tmp_val = pb
            (dernier)._get()['suiv'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    return (tete)

def semiMagicTransformation(A, B):
    A = A._clone() if hasattr(A, '_clone') else A
    B = B._clone() if hasattr(B, '_clone') else B
    revB = Pointer("revB", locals()) # POINTEUR_Cellule

    _tmp_revB = inverser(B)
    revB._assign(Pointer("revB_ptr_src", locals(), index=0, base_var=_tmp_revB) if isinstance(_tmp_revB, list) and not hasattr(_tmp_revB, '_get_target_container') else _tmp_revB)
    return (alterner(A, revB, True))

def transformerPremiereMoitie(L):
    L = L._clone() if hasattr(L, '_clone') else L
    m = Pointer("m", locals())
    gauche = Pointer("gauche", locals())
    droite = Pointer("droite", locals())
    suivant = Pointer("suivant", locals())
    temp = Pointer("temp", locals()) # POINTEUR_Cellule

    if L == None or (L)._get()['suiv'] == None:
        return (L)
    _tmp_m = milieu(L)
    m._assign(Pointer("m_ptr_src", locals(), index=0, base_var=_tmp_m) if isinstance(_tmp_m, list) and not hasattr(_tmp_m, '_get_target_container') else _tmp_m)
    _tmp_gauche = L
    gauche._assign(Pointer("gauche_ptr_src", locals(), index=0, base_var=_tmp_gauche) if isinstance(_tmp_gauche, list) and not hasattr(_tmp_gauche, '_get_target_container') else _tmp_gauche)
    _tmp_temp = L
    temp._assign(Pointer("temp_ptr_src", locals(), index=0, base_var=_tmp_temp) if isinstance(_tmp_temp, list) and not hasattr(_tmp_temp, '_get_target_container') else _tmp_temp)
    while (temp)._get()['suiv'] != m:
        _tmp_temp = (temp)._get()['suiv']
        temp._assign(Pointer("temp_ptr_src", locals(), index=0, base_var=_tmp_temp) if isinstance(_tmp_temp, list) and not hasattr(_tmp_temp, '_get_target_container') else _tmp_temp)
    _tmp_val = None
    (temp)._get()['suiv'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    _tmp_droite = inverser(m)
    droite._assign(Pointer("droite_ptr_src", locals(), index=0, base_var=_tmp_droite) if isinstance(_tmp_droite, list) and not hasattr(_tmp_droite, '_get_target_container') else _tmp_droite)
    return (alterner(gauche, droite, True))

def transformerDeuxiemeMoitie(L):
    L = L._clone() if hasattr(L, '_clone') else L
    m = Pointer("m", locals())
    gauche = Pointer("gauche", locals())
    droite = Pointer("droite", locals())
    temp = Pointer("temp", locals()) # POINTEUR_Cellule

    if L == None or (L)._get()['suiv'] == None:
        return (L)
    _tmp_m = milieu(L)
    m._assign(Pointer("m_ptr_src", locals(), index=0, base_var=_tmp_m) if isinstance(_tmp_m, list) and not hasattr(_tmp_m, '_get_target_container') else _tmp_m)
    _tmp_temp = L
    temp._assign(Pointer("temp_ptr_src", locals(), index=0, base_var=_tmp_temp) if isinstance(_tmp_temp, list) and not hasattr(_tmp_temp, '_get_target_container') else _tmp_temp)
    while (temp)._get()['suiv'] != m:
        _tmp_temp = (temp)._get()['suiv']
        temp._assign(Pointer("temp_ptr_src", locals(), index=0, base_var=_tmp_temp) if isinstance(_tmp_temp, list) and not hasattr(_tmp_temp, '_get_target_container') else _tmp_temp)
    _tmp_val = None
    (temp)._get()['suiv'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    _tmp_gauche = inverser(L)
    gauche._assign(Pointer("gauche_ptr_src", locals(), index=0, base_var=_tmp_gauche) if isinstance(_tmp_gauche, list) and not hasattr(_tmp_gauche, '_get_target_container') else _tmp_gauche)
    _tmp_droite = m
    droite._assign(Pointer("droite_ptr_src", locals(), index=0, base_var=_tmp_droite) if isinstance(_tmp_droite, list) and not hasattr(_tmp_droite, '_get_target_container') else _tmp_droite)
    return (alterner(droite, gauche, True))

def magicTransformation(L):
    L = L._clone() if hasattr(L, '_clone') else L
    m = Pointer("m", locals())
    premiere = Pointer("premiere", locals())
    deuxieme = Pointer("deuxieme", locals())
    temp = Pointer("temp", locals())
    resultat = Pointer("resultat", locals()) # POINTEUR_Cellule

    if L == None or (L)._get()['suiv'] == None:
        return (L)
    _tmp_m = milieu(L)
    m._assign(Pointer("m_ptr_src", locals(), index=0, base_var=_tmp_m) if isinstance(_tmp_m, list) and not hasattr(_tmp_m, '_get_target_container') else _tmp_m)
    _tmp_deuxieme = m
    deuxieme._assign(Pointer("deuxieme_ptr_src", locals(), index=0, base_var=_tmp_deuxieme) if isinstance(_tmp_deuxieme, list) and not hasattr(_tmp_deuxieme, '_get_target_container') else _tmp_deuxieme)
    _tmp_premiere = L
    premiere._assign(Pointer("premiere_ptr_src", locals(), index=0, base_var=_tmp_premiere) if isinstance(_tmp_premiere, list) and not hasattr(_tmp_premiere, '_get_target_container') else _tmp_premiere)
    _tmp_temp = L
    temp._assign(Pointer("temp_ptr_src", locals(), index=0, base_var=_tmp_temp) if isinstance(_tmp_temp, list) and not hasattr(_tmp_temp, '_get_target_container') else _tmp_temp)
    while (temp)._get()['suiv'] != m:
        _tmp_temp = (temp)._get()['suiv']
        temp._assign(Pointer("temp_ptr_src", locals(), index=0, base_var=_tmp_temp) if isinstance(_tmp_temp, list) and not hasattr(_tmp_temp, '_get_target_container') else _tmp_temp)
    _tmp_val = None
    (temp)._get()['suiv'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    _tmp_premiere = transformerPremiereMoitie(premiere)
    premiere._assign(Pointer("premiere_ptr_src", locals(), index=0, base_var=_tmp_premiere) if isinstance(_tmp_premiere, list) and not hasattr(_tmp_premiere, '_get_target_container') else _tmp_premiere)
    _tmp_deuxieme = transformerDeuxiemeMoitie(deuxieme)
    deuxieme._assign(Pointer("deuxieme_ptr_src", locals(), index=0, base_var=_tmp_deuxieme) if isinstance(_tmp_deuxieme, list) and not hasattr(_tmp_deuxieme, '_get_target_container') else _tmp_deuxieme)
    _tmp_resultat = premiere
    resultat._assign(Pointer("resultat_ptr_src", locals(), index=0, base_var=_tmp_resultat) if isinstance(_tmp_resultat, list) and not hasattr(_tmp_resultat, '_get_target_container') else _tmp_resultat)
    if resultat != None:
        _tmp_temp = resultat
        temp._assign(Pointer("temp_ptr_src", locals(), index=0, base_var=_tmp_temp) if isinstance(_tmp_temp, list) and not hasattr(_tmp_temp, '_get_target_container') else _tmp_temp)
        while (temp)._get()['suiv'] != None:
            _tmp_temp = (temp)._get()['suiv']
            temp._assign(Pointer("temp_ptr_src", locals(), index=0, base_var=_tmp_temp) if isinstance(_tmp_temp, list) and not hasattr(_tmp_temp, '_get_target_container') else _tmp_temp)
        _tmp_val = deuxieme
        (temp)._get()['suiv'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    else:
        _tmp_resultat = deuxieme
        resultat._assign(Pointer("resultat_ptr_src", locals(), index=0, base_var=_tmp_resultat) if isinstance(_tmp_resultat, list) and not hasattr(_tmp_resultat, '_get_target_container') else _tmp_resultat)
    return (resultat)


_algo_ecrire('=== TEST MAGIC TRANSFORMATION ===\n')
_tmp_L = None
L._assign(Pointer("L_ptr_src", globals(), index=0, base_var=_tmp_L) if isinstance(_tmp_L, list) and not hasattr(_tmp_L, '_get_target_container') else _tmp_L)
for i in range(1, 16 + 1):
    _tmp_curr = _algo_allouer_record({'val': 0, 'suiv': {}})
    curr._assign(Pointer("curr_ptr_src", globals(), index=0, base_var=_tmp_curr) if isinstance(_tmp_curr, list) and not hasattr(_tmp_curr, '_get_target_container') else _tmp_curr)
    _tmp_val = i
    (curr)._get()['val'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    _tmp_val = L
    (curr)._get()['suiv'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    _tmp_L = curr
    L._assign(Pointer("L_ptr_src", globals(), index=0, base_var=_tmp_L) if isinstance(_tmp_L, list) and not hasattr(_tmp_L, '_get_target_container') else _tmp_L)
_algo_ecrire('Liste initiale : ')
_tmp_curr = L
curr._assign(Pointer("curr_ptr_src", globals(), index=0, base_var=_tmp_curr) if isinstance(_tmp_curr, list) and not hasattr(_tmp_curr, '_get_target_container') else _tmp_curr)
while curr != None:
    _algo_ecrire((curr)._get()['val'])
    if (curr)._get()['suiv'] != None:
        _algo_ecrire(' -> ')
    _tmp_curr = (curr)._get()['suiv']
    curr._assign(Pointer("curr_ptr_src", globals(), index=0, base_var=_tmp_curr) if isinstance(_tmp_curr, list) and not hasattr(_tmp_curr, '_get_target_container') else _tmp_curr)
_algo_ecrire('\n')
_tmp_resultat = magicTransformation(L)
resultat._assign(Pointer("resultat_ptr_src", globals(), index=0, base_var=_tmp_resultat) if isinstance(_tmp_resultat, list) and not hasattr(_tmp_resultat, '_get_target_container') else _tmp_resultat)
_algo_ecrire('\nApres Magic Transformation :\n')
_tmp_curr = resultat
curr._assign(Pointer("curr_ptr_src", globals(), index=0, base_var=_tmp_curr) if isinstance(_tmp_curr, list) and not hasattr(_tmp_curr, '_get_target_container') else _tmp_curr)
while curr != None:
    _algo_ecrire((curr)._get()['val'])
    if (curr)._get()['suiv'] != None:
        _algo_ecrire(' -> ')
    _tmp_curr = (curr)._get()['suiv']
    curr._assign(Pointer("curr_ptr_src", globals(), index=0, base_var=_tmp_curr) if isinstance(_tmp_curr, list) and not hasattr(_tmp_curr, '_get_target_container') else _tmp_curr)
_algo_ecrire('\n')
