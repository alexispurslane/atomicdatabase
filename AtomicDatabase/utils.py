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
    return new_str, entities
