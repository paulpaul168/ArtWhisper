import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import urllib.request
import time
import concurrent.futures
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

base_url = "https://sammlung.belvedere.at"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
session = requests.Session()


def crawl_belvedere_collection():
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
    print("#" + soup.find("span", class_="max-pages").text + "#")
    page_limit = int(
        soup.find("span", class_="max-pages").text[2:].strip().replace(".", "")
    )

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(crawl_belvedere_collection_page, range(1, page_limit + 1))


def crawl_belvedere_collection_page(page: int):
    gallery_url = f"{base_url}/objects/images?filter=locationssite:Oberes%20Belvedere;onview:true&page={page}"
    print(gallery_url)
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

    store_artwork(title, artist, description, url, image_url)


def store_artwork(name, artist, description, url, image_url):
    # The image
    file_name = f"belvedere_images/{url.split("/")[4]}.jpeg"
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


if __name__ == "__main__":
    crawl_belvedere_collection()
