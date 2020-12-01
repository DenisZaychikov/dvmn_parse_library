import requests


def get_title():
    url = 'https://github.com/not_found'
    resp = requests.get(url)
    resp.raise_for_status()

    return resp.status_code

def get_book():
    text = get_title()

    return text


if __name__ == '__main__':
    c = 1
    for a in [100, 200, 300]:
        for b in [1000, 2000, 3000]:
            if c == 1:
                try:
                    code = get_book()
                except requests.exceptions.HTTPError:
                    continue
                else:
                    print(code)
