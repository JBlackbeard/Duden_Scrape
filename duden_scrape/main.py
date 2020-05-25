import logging
import json
from time import sleep
import numpy as np

from .utils import load_word
from duden_scrape.database import DatabaseManager
from duden_scrape.utils import add_meanings_db, add_word_db
import requests
import OpenSSL
from urllib3.exceptions import ReadTimeoutError


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



LAST_WORD = "/rechtschreibung/24_Stunden_Rennen"

Duden = {}

db = DatabaseManager("Duden")
# db.drop_table("wort")
# db.drop_table("bedeutungen")
# db.drop_table("synonyme")
# db.drop_table("gebrauch")
# db.drop_table("beispiele")
# db.drop_table("wendungen_redensarten_sprichwoerter")

word_dict = {"id": "INTEGER PRIMARY KEY", "name": "TEXT", "ganzes_wort": "TEXT", "artikel": "TEXT",
                "wortart": "TEXT", "haeufigkeit": "INTEGER",
                "worttrennung": "TEXT", "herkunft": "TEXT", "verwandte_form": "TEXT", 
                "alternative_schreibweise": "TEXT", "zeichen": "TEXT", "kurzform": "TEXT",
                "kurzform_fuer": "TEXT", "typische_verbindungen": "TEXT",
                "url": "TEXT"}

synonyme_dict = {"id": "INTEGER PRIMARY KEY", "synonyme": "TEXT", "wort_id": "INTEGER"}
synonyme_references = {"wort_id": "wort(id)"}

meaning_dict = {"id": "INTEGER PRIMARY KEY", "bedeutung": "TEXT",
                "grammatik": "TEXT", "wort_id": "INTEGER"}
meaning_references = {"wort_id": "wort(id)"}

examples_dict = {"id": "INTEGER PRIMARY KEY", "beispiel": "TEXT", "bedeutungen_id": "INTEGER"}
examples_references = {"bedeutungen_id": "bedeutungen(id)"}

sayings_dict = {"id": "INTEGER PRIMARY KEY", "wendung_redensart_sprichwort": "TEXT", "bedeutungen_id": "INTEGER"}
sayings_references = {"bedeutungen_id": "bedeutungen(id)"}

usage_dict = {"id": "INTEGER PRIMARY KEY", "gebrauch": "TEXT", "bedeutungen_id": "INTEGER"}
usage_references = {"bedeutungen_id": "bedeutungen(id)"}


db.create_table(table_name="wort", columns=word_dict)
db.create_table(table_name="synonyme", columns=synonyme_dict, references=synonyme_references, cascade_delete=True)
db.create_table(table_name="bedeutungen", columns=meaning_dict, references=meaning_references, cascade_delete=True)
db.create_table(table_name="beispiele", columns=examples_dict, references=examples_references, cascade_delete=True)
db.create_table(table_name="wendungen_redensarten_sprichwoerter", columns=sayings_dict, references=sayings_references, cascade_delete=True)
db.create_table(table_name="gebrauch", columns=usage_dict, references=usage_references, cascade_delete=True)

first_word = "/rechtschreibung/d_Korrekturzeichen_fuer_tilgen"

if not db.is_empty("wort"):
    url = db.select("url", "wort", order_by="id desc", limit="1").fetchone()[0].replace("https://www.duden.de", "")
    word = load_word(url)
    first_word = word.get_next_word()

url = first_word
recover = False
wait_variance = 5

if __name__ == "__main__":

    while True:
        try:
            if recover and not db.is_empty("wort"):
                db.delete("wort", {"id":db.get_max_id("wort")})
                max_url = db.select("url", "wort", order_by="id desc", limit="1").fetchone()[0].replace("https://www.duden.de", "")
                word = load_word(max_url)
                url = word.get_next_word()
                recover = False
            word = load_word(url)
            word_entry = word.return_word_entry()
            wort_id = add_word_db(word_entry, db, url)

            meanings = word.return_meaning()
            add_meanings_db(meanings, db, wort_id)


            logger.info(f"{url}, wait_variance: {round(wait_variance,3)}, wort_id: {wort_id}")

            if url == LAST_WORD:
                break
            url = word.get_next_word()
            sleep(abs(np.random.normal(0, wait_variance)))
            wait_variance = max(wait_variance-0.005, 2)
        except KeyboardInterrupt:
            logger.debug("KEYBOARD INTERRUPTION")
            db.delete("wort", {"id":db.get_max_id("wort")})
            break
        except requests.exceptions.Timeout:
            logger.error(f"The requests for {url} timed out with wait_variance {round(wait_variance,3)} ", exc_info=True)
            wait_variance += 5
            sleep(300)
        except OSError:
            logger.error(f"The request for {url} with {round(wait_variance,3)} failed", exc_info=True)
            wait_variance += 5
            sleep(300)
        except requests.exceptions.ConnectTimeout:
            logger.error(f"The request for {url} timed out with wait_variance {round(wait_variance,3)}", exc_info=True)
            wait_variance += 5
            sleep(300)
        except ReadTimeoutError:
            logger.error(f"The request for {url} timed out with wait_variance {round(wait_variance,3)}", exc_info=True)
            wait_variance += 5
            sleep(300)
        except:
            logger.error(f"There was an error with {url} \n and word_entry {word_entry} \n with wait_variance {round(wait_variance,3)} ", exc_info=True)
            recover = True
            wait_variance += 5
            sleep(300)






#@TODO: clean up __main__
#@TODO: create table for typische_verbindungen after scraping all data