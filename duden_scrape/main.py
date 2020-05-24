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


FIRST_WORD = "/rechtschreibung/d_Korrekturzeichen_fuer_tilgen"
#FIRST_WORD = "/rechtschreibung/Haus"

Duden = {}
url = FIRST_WORD

db = DatabaseManager("Duden")
db.drop_table("wort")
db.drop_table("bedeutungen")
db.drop_table("synonyme")
db.drop_table("bedeutungen")
db.drop_table("gebrauch")
db.drop_table("beispiele")
db.drop_table("wendungen_redensarten_sprichwoerter")

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
db.create_table(table_name="synonyme", columns=synonyme_dict, references=synonyme_references)
db.create_table(table_name="bedeutungen", columns=meaning_dict, references=meaning_references)
db.create_table(table_name="beispiele", columns=examples_dict, references=examples_references)
db.create_table(table_name="wendungen_redensarten_sprichwoerter", columns=sayings_dict, references=sayings_references)
db.create_table(table_name="gebrauch", columns=usage_dict, references=usage_references)

if __name__ == "__main__":

    for i in range(500):
        try:
            word = load_word(url)
            word_entry = word.return_word_entry()
            synonyme = word_entry.pop("synonyme") or None
            db.add("wort", word_entry)
            wort_id = db.select("id", "wort", {"url": "https://www.duden.de" + url}).fetchone()[0]
            
            if synonyme:
                for synonym in synonyme.split(";"):
                    db.add("synonyme", {"synonyme": synonym, "wort_id": wort_id})

            meanings = word.return_meaning()
            for bedeutung in meanings["bedeutungen"]:
                bedeutung.update({"wort_id": wort_id})
                beispiele = bedeutung.pop("beispiele") or []
                wendungen = bedeutung.pop("wendungen_redensarten_sprichwoerter") or []
                gebrauch = bedeutung.pop("gebrauch") or None
                db.add("bedeutungen", bedeutung)
                
                bedeutung_id = db.select("max(id)", "bedeutungen").fetchone()[0]

                for beispiel in beispiele:
                    db.add("beispiele", {"beispiel": beispiel, "bedeutungen_id": bedeutung_id})

                for wendung in wendungen:
                    db.add("wendungen_redensarten_sprichwoerter", {"wendung_redensart_sprichwort": wendung, 
                    "bedeutungen_id": bedeutung_id})
                
                if gebrauch:
                    for geb in gebrauch.split(";"):
                        db.add("gebrauch", {"gebrauch": geb, "bedeutungen_id": bedeutung_id})


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






#@TODO: split up the work in 26 parts and use proxies to scrape all of them
#@TODO: save words on database
#@TODO: add to database after scraping each word 