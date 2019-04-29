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
    return eval(" ".join([str(binds[el]) if el in binds else str(el) for el in val]), {}, {})

def get_binds(name, binds, global_binds):
    print(name)
    if name[0] == '*':
        print(global_binds)
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
