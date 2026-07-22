def split_csv_line(line):
    (fields, field, i, n, in_q) = ([], [], 0, len(line), False)
    while i < n:
        c = line[i]
        if in_q:
            if c == '"':
                if i + 1 < n and line[i + 1] == '"':
                    field.append('"')
                    i += 1
                else:
                    in_q = False
            else:
                field.append(c)
        elif c == '"':
            in_q = True
        elif c == ',':
            fields.append(''.join(field))
            field = []
        else:
            field.append(c)
        i += 1
    fields.append(''.join(field))
    return fields
