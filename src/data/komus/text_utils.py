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
