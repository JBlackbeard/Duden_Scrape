import logging
import requests
from bs4 import BeautifulSoup
from .models import Word

logger = logging.getLogger(__name__)

def load_word(word_url, base_url="https://www.duden.de",
              headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4), "\
            + "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Chrome/71.0.3578.98"}):
    """Get new Word instance from Duden Website

    Arguments:
        word_url {String} -- word url of the form "/rechtschreibung/{word}"

    Returns:
        Word -- returns an instance of the Word Class
    """
    url = base_url + word_url

    # try:
    source = requests.get(url, headers=headers)
    # except Exception as errc:
    #         print("There seems to be no internet connection right now. Try again later!", errc)
                        
    code = source.status_code
    if code == 200:
        soup = BeautifulSoup(source.text, 'lxml')
    else:
        raise Exception(f"Unexpected response code: {source.status_code}")
        logger.exception(f"Unexpected response code for {url}: {source.status_code}")

    return Word(soup, url)