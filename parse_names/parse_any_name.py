suffixes = ["sr.","jr."]
prefixes = ["Abu",
                "Al",
                "Bet",
                "Bint",
                "El",
                "Ter",
                "Der",
                "Berber",
                "Aït",
                "At",
                "Ath",
                "Ter",
                "Tre",
                "Van",
                "von",
                "zu",
                "Bath",
                "Ben",
                "Del",
                "Degli",
                "Della",
                "Di",
                "A",
                "Ab",
                "Ap",
                "Ferch",
                "Verch",
                "Erch",
                "Af",
                "Ālam",
                "Bar",
                "Chaudhary",
                "Da",
                "Das",
                "De",
                "Dele",
                "Dos",
                "Du",
                "E",
                "Fitz",
                "i",
                "ka",
                "Kil",
                "Gil",
                "Mal",
                "Mul",
                "La",
                "Le",
                "Lu",
                "M",
                "Mac",
                "Mc",
                "Mck",
                "Mhic",
                "Mic",
                "Mala",
                "Na",
                "Ngā",
                "Nic",
                "Ní",
                "Nin",
                "O",
                "Ó",
                "Ua",
                "Uí",
                "Öz",
                "Pour",
                "Te",
                "Van De",
                "Van Den",
                "Van Der",
                "Van Het",
                "Van",
                "war"]

prefixes = [a.lower() for a in prefixes]
ignore = ['1st','2nd','3rd','4th','5th','7th','8th','9th']

def parse_long_names(parts):
    for count, part in enumerate(parts):
        if part in ignore:
            #ignore parts here to end
            parts = [a.replace(",","") for a in parts[:count]]
            continue
    for count, part in enumerate(parts):
        if part.lower() in prefixes:
            #start of surname (assuming prefix is correct)
            first_name = parts[0]
            middle_name = ' '.join(parts[1:count])
            last_name = ' '.join(parts[count:])
            return {"first_name":first_name,"middle_name":middle_name,"last_name":last_name}
            break
    if len(parts) >= 1:
        return parts
    else:
        raise ValueError(f"Unable to parse this name using PLN\n{parts}")
            
def parse_name(name, suffixes=suffixes, prefixes=prefixes):
    if name == '':
        return None
    surname_prefixes = [a.lower() for a in prefixes]
    person_name = {"first_name":None, "middle_name":None, "last_name":None}
    name = name.split("(")[0]
    parts = [a.strip() for a in name.split("_") if a.strip()]
    if len(parts) == 3:
        person_name = dict(zip(person_name.keys(), parts))
        middle_name = person_name['middle_name']
        if middle_name:
            if middle_name in surname_prefixes:
                person_name["middle_name"] = None
                person_name["last_name"] = ' '.join([middle_name, person_name['last_name']])
    elif len(parts) == 2:
        person_name['first_name'] = parts[0]
        person_name['last_name'] = parts[-1]
    elif len(parts) == 1:
        person_name['first_name'] = parts[0]
    elif len(parts) > 3:
        person_name = parse_long_names(parts)
    else:
        return None
    return person_name
