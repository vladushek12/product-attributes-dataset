def get_category_name(link: str) -> str:
    import re

    pattern = r"([A-Za-z\-]+)\/c\/"
    match = re.search(pattern, link)

    if match:
        return str(match.group(1))
    else:
        return ''
    

def create_params(**params):
    return "&".join([f"{key}={value}" for key, value in params.items()])


def fix_category_name(header: str):
    tmp = header.split()    

    if tmp[-1].isnumeric():
        category_name = " ".join(tmp[:-1])

        return category_name, int(tmp[-1])
    
    return header, 0