import logging
import json
from time import sleep
import numpy as np

from .utils import load_word


logger = logging.getLogger(__name__) # create a specific logger, so we don't use a root logger
logger.setLevel(logging.DEBUG)

# create file handler which logs even debug messages
fh = logging.FileHandler('duden_main.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


#BASE_URL = "https://www.duden.de"
FIRST_WORD = "/rechtschreibung/Haus"
#HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4), "\
#            + "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Chrome/71.0.3578.98"}
Duden = {}
url = FIRST_WORD

if __name__ == "__main__":
    for i in range(3):
        try:
            word = load_word(url)
            Duden[word.name] = word.return_word_entry()
            logger.info(f"{i}: {url}")
            url = word.get_next_word()
            sleep(abs(np.random.normal(0, 3)))
        except KeyboardInterrupt:
            logger.debug("KEYBOARD INTERRUPTION")
            break
        except:
            logger.debug(f"There was an error with {word.url}", exc_info=True)
            url = word.get_next_word()
            sleep(120)
            pass

    with open('duden_new.json', 'w', encoding="utf8") as fp:
        json.dump(Duden, fp, ensure_ascii=False)

#@TODO: split up the work in 26 parts and use proxies to scrape all of them
#@TODO: save words on database