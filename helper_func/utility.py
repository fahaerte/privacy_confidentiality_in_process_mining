def read_variables_from_file(file_path):
    variables = {}

    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split('=')
            variables[key.strip()] = value.strip()

    return variables