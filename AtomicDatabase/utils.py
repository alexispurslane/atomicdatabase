from itertools import groupby

def create_text_entities(string):
    new_str = ""
    in_quot = False
    entities = []
    for c in string:
        if c == "\"":
            in_quot = not in_quot
            if in_quot:
                entities.append("")
            else:
                new_str += "ENTITY_" + str(len(entities) - 1)
        else:
            if in_quot:
                entities[-1] += c
            else:
                new_str += c
    return new_str.replace("{", " { ").\
        replace("}", " } "), entities

def between_limits(value, limits):
    (a,b) = limits
    return (value >= a or a == -1) and (value <= b or b == -1)

def eav_hash(a, b):
    return 0.5*(a + b)*(a + b + 1)+b

def eval_expr(val, binds):
    return eval(" ".join([str(v) for v in val]), {}, binds)

def get_binds(name, binds, global_binds):
    if name[0] == '*':
        return global_binds.get(name)
    else:
        return binds.get(name)

def peek(iterable):
    try:
        first = next(iterable)
    except StopIteration:
        return None
    return chain([first], iterable)

def limit_format(obj):
    if isinstance(obj, list):
        return ", ".join(obj[:3])
    elif isinstance(obj, (int, float)):
        if obj == -1:
            return "INF"
        else:
            return str(obj)

def is_variable(e):
    return isinstance(e, str) and e[0].upper() == e[0] and not e[0].isnumeric() and not " " in e

def is_destructuring_pattern(pat):
    return (1, "...") in pat or (1, "@") in pat

def destructure(pattern, value):
    binds = []

    match_vars = []
    rest_var = None
    all_var = None

    all_parse = [list(g[1]) for g in groupby(pattern, lambda x: x == "@")]
    if len(all_parse) == 3:
        all_var = all_parse[0][0]
    else:
        all_parse = [[], [], pattern]

    rest_parse = [list(g[1]) for g in groupby(all_parse[2], lambda x: x == "...")]
    if len(rest_parse) >= 1:
        match_vars = rest_parse[0]
    if len(rest_parse) >= 3:
        rest_var   = rest_parse[2][0]

    if len(match_vars) + int(not not rest_var) > len(value):
        return None

    if all_var:
        binds.append((all_var, value))
    if rest_var:
        binds.append((rest_var, value[len(match_vars):]))
    if len(match_vars) > 0:
        binds.extend(zip(match_vars, value[:len(match_vars)]))

    return binds
