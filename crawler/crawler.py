import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import urllib.request
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def crawl_belvedere_collection():
    base_url = "https://sammlung.belvedere.at"
    gallery_url = f"{base_url}/objects/images?filter=locationssite:Oberes%20Belvedere;onview:true"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(gallery_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        logging.info(f"Successfully accessed gallery page: {gallery_url}")
    except requests.RequestException as e:
        logging.error(f"Failed to access gallery page: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    if not os.path.exists('belvedere_images'):
        os.makedirs('belvedere_images')

    artworks = soup.find_all('div', class_='artwork-item')
    logging.info(f"Found {len(artworks)} artwork items on the gallery page")

    if not artworks:
        logging.warning("No artwork items found. The page structure might have changed.")
        logging.info(f"Page content: {soup.prettify()[:500]}...")  # Log first 500 characters of the page

    for artwork in artworks:
        link = artwork.find('a', href=True)
        if link:
            artwork_url = urljoin(base_url, link['href'])
            crawl_artwork_page(artwork_url, headers)
        else:
            logging.warning(f"No link found for artwork: {artwork}")
        
        time.sleep(1)  # Be polite, wait between requests

def crawl_artwork_page(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logging.info(f"Successfully accessed artwork page: {url}")
    except requests.RequestException as e:
        logging.error(f"Failed to access artwork page {url}: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract detailed information
    title = soup.find('h1')
    title = title.text.strip() if title else "Unknown Title"
    artist = soup.find('div', class_='artist-name')
    artist = artist.text.strip() if artist else "Unknown Artist"
    
    logging.info(f"Extracted info - Title: {title}, Artist: {artist}")

    # Find the main image
    img_tag = soup.find('img', class_='artwork-image')
    if img_tag and 'src' in img_tag.attrs:
        img_url = urljoin(url, img_tag['src'])
        
        # Create a valid filename
        valid_filename = "".join(c for c in title if c.isalnum() or c in (' ', '.', '_')).rstrip()
        filename = f"{valid_filename}_{artist}.jpg"
        filepath = os.path.join('belvedere_images', filename)
        
        # Download the image
        try:
            urllib.request.urlretrieve(img_url, filepath)
            logging.info(f"Downloaded: {filename}")
            
            # Save metadata to a text file
            with open(f"{filepath}.txt", 'w', encoding='utf-8') as f:
                f.write(f"Title: {title}\n")
                f.write(f"Artist: {artist}\n")
                f.write(f"Source URL: {url}\n")
            
        except Exception as e:
            logging.error(f"Error downloading {filename}: {str(e)}")
    else:
        logging.warning(f"No image found for artwork: {url}")

if __name__ == "__main__":
    crawl_belvedere_collection()