import sys
import logging
import atexit
import json
from time import sleep
import numpy as np
from datetime import datetime
from .utils import load_word
from duden_scrape.database import DatabaseManager
from duden_scrape.utils import RangeDict, add_link_entries_db, add_meanings_db, add_word_db, create_tables
import requests
import OpenSSL
from urllib3.exceptions import ReadTimeoutError
import sqlite3


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

def exit_handler(db, url):
    max_id = db.get_max_id("wort")
    db.delete("wort", {"id":max_id})
    logger.info(f"Deleted word {url} with id {max_id}")

LAST_WORD = "/rechtschreibung/24_Stunden_Rennen"
db = DatabaseManager("Duden")
# db.drop_table("wort")
# db.drop_table("bedeutungen")
# db.drop_table("synonyme")
# db.drop_table("gebrauch")
# db.drop_table("beispiele")
# db.drop_table("wendungen_redensarten_sprichwoerter")
# db.drop_table("synonyme_links")
# db.drop_table("antonyme_links")
# db.drop_table("typische_verbindungen_links")
create_tables(db)
first_word = "/rechtschreibung/d_Korrekturzeichen_fuer_tilgen"
url = first_word
recover = False
wait_variance = 5

min_wait_variance_by_hour = RangeDict({range(0, 9): 1.5, range(9, 21): 3.5, range(21, 24): 2.5})

if __name__ == "__main__":
    if not db.is_empty("wort"):
        old_url = db.select("url", "wort", order_by="id desc", limit="1").fetchone()[0].replace("https://www.duden.de", "")
        word = load_word(old_url)
        url = word.get_next_word()

    while True:
        try:
            if recover and not db.is_empty("wort"):
                # if there was an unhandled excpetion delete the last scraped word
                # to make sure the word information wasn't just partially scraped
                # and start scraping that word again
                sleep(3)
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

            link_entries = word.return_links()
            add_link_entries_db(link_entries["synonyme_links"], db, wort_id, "synonyme_links", "synonym_url")
            add_link_entries_db(link_entries.pop("antonyme_links"), db, wort_id, "antonyme_links", "antonym_url")
            add_link_entries_db(link_entries.pop("typische_verbindungen_links"), db, wort_id,
             "typische_verbindungen_links", "typische_verbindung_url")

            logger.info(f"{url}, wait_variance: {round(wait_variance,3)}, wort_id: {wort_id}")

            if url == LAST_WORD:
                break
            url = word.get_next_word()
            sleep(abs(np.random.normal(0, wait_variance)))

            time_hour = datetime.now().hour
            wait_variance = max(wait_variance-0.005, min_wait_variance_by_hour[time_hour])

            
        except KeyboardInterrupt:
            logger.debug("KEYBOARD INTERRUPTION")
            max_id = db.get_max_id("wort")
            max_url = db.select("url", "wort", order_by="id desc", limit="1").fetchone()[0].replace("https://www.duden.de", "")
            db.delete("wort", {"id": max_id})
            logger.warning(f"{max_url} with id {max_id} was deleted")
            sys.exit(1)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout, ReadTimeoutError):
            logger.error(f"The requests for {url} timed out with wait_variance {round(wait_variance,3)} ", exc_info=True)
            wait_variance += 5
            sleep(300)
        except OSError as e:
            logger.error(f"The request for {url} with {round(wait_variance,3)} failed with an OSError: \n {e}", exc_info=True)
            wait_variance += 5
            sleep(300)
        except sqlite3.OperationalError as e:
            logger.error(f"There was an error with sqlite3: \n {e}")
            recover = True
        except:
            logger.error(f"There was an error with {url} \n and word_entry {word_entry} \n with wait_variance {round(wait_variance,3)} ", exc_info=True)
            max_id = db.get_max_id("wort")
            recover = True
            wait_variance += 5
    







#@TODO: clean up __main__
#@TODO: create new ER_diagram with fun_facts and alt_hyphenation
#@TODO: create link tables with added words (not just the links) -> join to wort table