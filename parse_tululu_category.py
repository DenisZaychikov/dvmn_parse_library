import requests
from bs4 import BeautifulSoup
import json
import re
import argparse
import os
from urllib.parse import urljoin
from pathvalidate import sanitize_filename

BOOKS_FOLDER = 'books'
IMAGES_FOLDER = 'images'


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_page', type=int, default=1)
    parser.add_argument('--end_page', type=int, default=2)
    parser.add_argument('--dest_folder', default='.')
    parser.add_argument('--skip_imgs', action='store_const', const=False)
    parser.add_argument('--skip_txt', action='store_const', const=False)
    parser.add_argument('--json_path')
    parser.add_argument('--category', default='l55')

    return parser


def raise_redirect_error(response):
    if response.status_code in [301, 302]:
        http_redirect_error_msg = 'Redirect error'
        raise requests.HTTPError(http_redirect_error_msg)


def get_soup_obj(url):
    resp = requests.get(url, allow_redirects=False)
    raise_redirect_error(resp)
    soup = BeautifulSoup(resp.text, 'lxml')

    return soup


def get_book_id(reference):
    link = reference['href']
    book_id = re.search(r'\d+', link)[0]

    return book_id


def check_title(title):
    book_title = sanitize_filename(title)

    return book_title


def save_book(file_path, book_path, book):
    os.makedirs(file_path, exist_ok=True)
    with open(book_path, 'w', encoding='utf-8') as file:
        file.write(book)


def save_image(img_file_path, full_book_img_link, img_src):
    os.makedirs(img_file_path, exist_ok=True)
    resp = requests.get(full_book_img_link)
    raise_redirect_error(resp)

    with open(img_src, 'wb') as img_file:
        img_file.write(resp.content)


def get_book_title_and_author(soup):
    parsed_book_title_and_author = soup.select_one('#content h1').text
    title, author_name = parsed_book_title_and_author.split('::')
    title, author_name = title.strip(), author_name.strip()
    book_title = check_title(title)

    return book_title, author_name


def get_book_comments(soup):
    comments = []
    parsed_comments = soup.select('.texts .black')
    for comment in parsed_comments:
        comments.append(comment.text)

    return comments


def get_book_genres(soup):
    genres = []
    parsed_genres = soup.select('span.d_book a')
    for genre in parsed_genres:
        genres.append(genre.text)

    return genres


def get_img_src(soup, skip_imgs, dest_folder):
    if not skip_imgs:
        parsed_book_img_link = soup.select_one('.bookimage img')['src']
        full_book_img_link = urljoin('http://tululu.org/', parsed_book_img_link)
        img_name = parsed_book_img_link.split('/')[-1]
        img_src = os.path.join(dest_folder, IMAGES_FOLDER, img_name)
        img_file_path = os.path.join(dest_folder, IMAGES_FOLDER)
        save_image(img_file_path, full_book_img_link, img_src)

        return img_src


def get_book_info(book_id, dest_folder, skip_txt, skip_imgs, resp):
    url = f'http://tululu.org/b{book_id}/'
    soup = get_soup_obj(url)
    book_title, author_name = get_book_title_and_author(soup)
    comments = get_book_comments(soup)
    genres = get_book_genres(soup)
    img_src = get_img_src(soup, skip_imgs, dest_folder)

    if not skip_txt:
        book = resp.text
        book_path = os.path.join(dest_folder, BOOKS_FOLDER, f'{book_title}.txt')
        file_path = os.path.join(dest_folder, BOOKS_FOLDER)
        save_book(file_path, book_path, book)
    else:
        book_path = None

    return {
        'title': book_title,
        'author': author_name,
        'img_src': img_src,
        'book_path': book_path,
        'comments': comments,
        'genres': genres
    }


def save_books_info_to_json(books_info, path_to_file):
    if not os.path.exists(path_to_file):
        os.makedirs(path_to_file)
    with open(os.path.join(path_to_file, 'books_info.json'), 'w') as file:
        json.dump(books_info, file, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    start_page, end_page, dest_folder = args.start_page, args.end_page, args.dest_folder
    skip_imgs, skip_txt, json_path = args.skip_imgs, args.skip_txt, args.json_path
    category = args.category
    if start_page and not end_page:
        url = f'http://tululu.org/{category}/{start_page}/'
        soup = get_soup_obj(url)
        end_page = soup.select('.npage')[-1].text
        end_page = int(end_page) + 1
    books_info = []
    for page in range(start_page, end_page):
        url = f'http://tululu.org/{category}/{page}'
        soup = get_soup_obj(url)
        references = soup.select('.bookimage a')
        for reference in references:
            book_id = get_book_id(reference)
            url = f'http://tululu.org/txt.php?id={book_id}'
            resp = requests.get(url, allow_redirects=False)
            resp.raise_for_status()
            if resp.status_code not in [301, 302]:
                book_info = get_book_info(book_id, dest_folder, skip_txt, skip_imgs, resp)
                books_info.append(book_info)
    if not json_path:
        save_books_info_to_json(books_info, dest_folder)
    else:
        save_books_info_to_json(books_info, json_path)
