import logging
import json
from time import sleep
import numpy as np

from .utils import load_word
from duden_scrape.database import DatabaseManager


logger = logging.getLogger(__name__) # create a specific logger, so we don't use a root logger
logger.setLevel(logging.DEBUG)

# create file handler which logs even debug messages
fh = logging.FileHandler('duden_scrape.log')
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
FIRST_WORD = "/rechtschreibung/d_Korrekturzeichen_fuer_tilgen"
FIRST_WORD = "/rechtschreibung/Hausbewohnerin"
#HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4), "\
#            + "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Chrome/71.0.3578.98"}
Duden = {}
url = FIRST_WORD

db = DatabaseManager("Duden")
db.drop_table("wort")
db.drop_table("bedeutungen")
word_dict = {"id": "INTEGER PRIMARY KEY", "name": "TEXT", "ganzes_wort": "TEXT", "artikel": "TEXT",
                "wortart": "TEXT", "haeufigkeit": "INTEGER",
                "worttrennung": "TEXT", "herkunft": "TEXT", "verwandte_form": "TEXT", 
                "alternative_schreibweise": "TEXT", "zeichen": "TEXT", "kurzform": "TEXT",
                "kurzform_fuer": "TEXT", "synonyme": "TEXT", "typische_verbindungen": "TEXT",
                "url": "TEXT"}
meaning_dict = {"id": "INTEGER PRIMARY KEY", "bedeutung": "TEXT", "beispiele": "TEXT", 
                "wendungen_redensarten_sprichwoerter": "TEXT", 
                 "gebrauch": "TEXT", "grammatik": "TEXT", "wort_id": "INTEGER"}
meaning_references = {"wort_id": "wort(id)"}


db.create_table(table_name="wort", columns=word_dict)
db.create_table(table_name="bedeutungen", columns=meaning_dict, references=meaning_references)

if __name__ == "__main__":

    for i in range(500):
        try:
            word = load_word(url)
            word_entry = word.return_word_entry()
            db.add("wort", word_entry)
            wort_id = db.select("id", "wort", {"url": "https://www.duden.de" + url}).fetchone()[0]
            meanings = word.return_meaning()
            for bedeutung in meanings["bedeutungen"]:
                bedeutung.update({"wort_id": wort_id})
                db.add("bedeutungen", bedeutung)

            logger.info(f"{i}: {url}, wort_id: {wort_id}")
            url = word.get_next_word()
            sleep(abs(np.random.normal(0, 5)))
        except KeyboardInterrupt:
            logger.debug("KEYBOARD INTERRUPTION")
            break
        except:
            logger.error(f"There was an error with {word.url} \n and word_entry {word_entry} ", exc_info=True)
            url = word.get_next_word()
            sleep(120)
            pass

    if Duden==1:
        with open('duden.json', 'w', encoding="utf8") as fp:
            json.dump(Duden, fp, ensure_ascii=False)




#@TODO: split up the work in 26 parts and use proxies to scrape all of them
#@TODO: save words on database
#@TODO: add to database after scraping each word 