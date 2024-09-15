import argparse
import json
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import concurrent.futures
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

token = ""
base_url = "https://sammlung.belvedere.at"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
session = requests.Session()
api_session = requests.Session()


def crawl_belvedere_collection(single_threaded: bool = False):
    gallery_url = (
        f"{base_url}/objects/images?filter=locationssite:Oberes%20Belvedere;onview:true"
    )

    try:
        response = session.get(gallery_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        logging.info(f"Successfully accessed gallery page: {gallery_url}")
    except requests.RequestException as e:
        logging.error(f"Failed to access gallery page: {e}")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    page_limit = int(
        soup.find("span", class_="max-pages").text[2:].strip().replace(".", "")
    )

    if single_threaded:
        for page in range(1, page_limit + 1):
            crawl_belvedere_collection_page(page)
    else:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(crawl_belvedere_collection_page, page): page
                for page in range(1, page_limit + 1)
            }
            for future in concurrent.futures.as_completed(futures):
                page = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    logging.error(f"Page {page} generated an exception: {exc}")
                    raise  # Re-raise the exception to stop execution


def crawl_belvedere_collection_page(page: int):
    gallery_url = f"{base_url}/objects/images?filter=locationssite:Oberes%20Belvedere;onview:true&page={page}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = session.get(gallery_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.RequestException as e:
        logging.error(f"Failed to access gallery page: {e}")
        return

    soup = BeautifulSoup(response.content, "html.parser")

    if not os.path.exists("belvedere_images"):
        os.makedirs("belvedere_images")

    artworks = soup.find_all("div", class_="grid-item")
    logging.info(f"Found {len(artworks)} artwork items on the gallery page")

    if not artworks:
        logging.warning(
            "No artwork items found. The page structure might have changed."
        )
        logging.info(
            f"Page content: {soup.prettify()[:500]}..."
        )  # Log first 500 characters of the page

    for artwork in artworks:
        link = artwork.find("a", href=True)
        if link:
            artwork_url = urljoin(base_url, link["href"])
            crawl_artwork_page(artwork_url, headers)
        else:
            logging.warning(f"No link found for artwork: {artwork}")


def crawl_artwork_page(url, headers):
    id = url.split("/")[4]
    file_name = f"belvedere_data/{id}.json"

    if os.path.exists(file_name):
        logging.info(f"Metadata in cache: {file_name}")
        with open(file_name) as f:
            data = json.load(f)
        store_artwork(
            data["title"],
            data["artist"],
            data["description"],
            data["description_page"],
            data["url"],
        )
        return

    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to access artwork page {url}: {e}")
        return

    soup = BeautifulSoup(response.content, "html.parser")

    # Extract detailed information
    title = soup.find("h1")
    title = title.text.strip() if title else "Unknown Title"

    artistDiv = soup.find("div", class_="peopleField")
    artistAnchor = artistDiv.find("a")
    artist = artistAnchor.text.strip() if artistAnchor else "Unknown Artist"

    description = ""
    if soup.find("li", class_="descriptionField"):
        description = soup.find("li", class_="descriptionField").find("p").text.strip()

    image_url = (
        base_url + soup.find("div", class_="detail-item-img").find("img").attrs["src"]
    )

    with open(file_name, "w") as f:
        cache_data = {
            "url": image_url,
            "title": title,
            "description": description,
            "description_page": url,
            "artist": artist,
        }
        json.dump(cache_data, f, indent=2)

    store_artwork(title, artist, description, url, image_url)


def store_artwork(name, artist, description, url, image_url):
    # Post to the db
    id = url.split("/")[4]
    data = {
        "url": image_url,
        "title": name,
        "description": description,
        "description_page": url,
        "artist": artist,
    }

    api_headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",  # Include the token in the Authorization header
    }

    api_response = api_session.post(
        f"http://localhost:8000/images/{id}", headers=api_headers, json=data
    )
    if api_response.status_code == 200:
        pass
    elif api_response.status_code == 409:
        logging.info(f"Artwork {id} already existed on backend")
    else:
        api_response.raise_for_status()

    # Store the image in a folder
    file_name = f"belvedere_images/{id}.jpeg"
    if os.path.exists(file_name):
        logging.info(f"Stored artwork (file cached): {file_name}")
        return

    try:
        response = session.get(image_url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to access artwork page {url}: {e}")
        return

    with open(file_name, "wb") as f:
        f.write(response.content)

    logging.info(f"Stored artwork: {file_name}")


def login_backend():
    global token

    # Step 1: Get the Auth Token
    token_url = "http://127.0.0.1:8000/token"  # Replace with actual token endpoint
    token_data = {
        "username": "admin",  # Replace with your username
        "password": "secret!password",  # Replace with your password
    }
    token_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Request token from the token endpoint
    token_response = api_session.post(token_url, headers=token_headers, json=token_data)

    # Check if the request was successful
    if token_response.status_code == 200:
        # Extract token from the response (assuming token is in the 'access_token' field)
        token = token_response.json().get("access_token")
        logging.info(f"Token obtained: {token}")
    else:
        logging.error(
            f"Failed to obtain token. Status code: {token_response.status_code}"
        )
        logging.error(token_response.text)
        exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl the Belvedere Collection")
    parser.add_argument(
        "--single-threaded",
        action="store_true",
        help="Run the crawler in single-threaded mode (easier for debugging)",
    )
    args = parser.parse_args()

    login_backend()
    crawl_belvedere_collection(single_threaded=args.single_threaded)
