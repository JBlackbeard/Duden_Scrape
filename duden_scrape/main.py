import sys
import logging
from time import sleep
import numpy as np
from datetime import datetime
from .utils import load_word
from duden_scrape.database import DatabaseManager
from duden_scrape.utils import RangeDict, add_full_word_db, add_link_entries_db, add_meanings_db, add_word_db, create_tables, increase_variance
import requests
import OpenSSL
from urllib3.exceptions import ReadTimeoutError
import sqlite3

# logger properties
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('duden_scrape.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


LAST_WORD = "/rechtschreibung/24_Stunden_Rennen"
word_entry = None
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

min_wait_variance_by_hour = RangeDict(
    {range(0, 7): 0.5, range(7, 21): 5, range(21, 24): 2.5})


if __name__ == "__main__":
    time_hour = datetime.now().hour
    wait_variance = min_wait_variance_by_hour[time_hour]
    if not db.is_empty("wort"):
        old_url = db.select("url", "wort", order_by="id desc", limit="1").fetchone()[
            0].replace("https://www.duden.de", "")
        word = load_word(old_url)
        url = word.get_next_word()
    #url = "rechtschreibung/Saufgelage"
    #url = "rechtschreibung/Saeufernase"

    while True:
        try:
            if recover and not db.is_empty("wort"):
                # if there was an unhandled excpetion delete the last scraped word
                # to make sure the word information wasn't just partially scraped
                # and start scraping that word again
                sleep(wait_variance**2)
                db.delete("wort", {"id": db.get_max_id("wort")})
                max_url = db.select("url", "wort", order_by="id desc", limit="1").fetchone()[
                    0].replace("https://www.duden.de", "")
                word = load_word(max_url)
                url = word.get_next_word()
                recover = False

            word = load_word(url)
            wort_id, word_entry = add_full_word_db(word, url, db)

            logger.info(
                f"{url}, wait_variance: {round(wait_variance,3)}, wort_id: {wort_id}")

            if url == LAST_WORD:
                sys.exit(1)
            url = word.get_next_word()

            sleep(abs(np.random.normal(0, wait_variance)))

            time_hour = datetime.now().hour
            wait_variance = max(wait_variance-0.01,
                                min_wait_variance_by_hour[time_hour])

        except KeyboardInterrupt:
            logger.debug("KEYBOARD INTERRUPTION")
            max_id = db.get_max_id("wort")
            max_url = db.select("url", "wort", order_by="id desc", limit="1").fetchone()[
                0].replace("https://www.duden.de", "")
            db.delete("wort", {"id": max_id})
            logger.warning(f"{max_url} with id {max_id} was deleted")
            sys.exit(1)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout, ReadTimeoutError, requests.exceptions.ConnectionError) as e:
            logger.error(
                f"The requests for {url} timed out with wait_variance {round(wait_variance,3)}: \n {e}")
            wait_variance = increase_variance(wait_variance)
            sleep(300)
        except OSError as e:
            logger.error(
                f"The request for {url} with {round(wait_variance,3)} failed with an OSError: \n {e}")
            wait_variance = increase_variance(wait_variance)
            sleep(300)
        except sqlite3.OperationalError as e:
            logger.error(f"There was an error with sqlite3: \n {e}")
            recover = True
        except:
            if url == LAST_WORD:
                logger.info("The last word was scraped and the program quit")
                sys.exit(1)
            logger.error(
                f"There was an error with {url} \n and word_entry {word_entry} \n with wait_variance {round(wait_variance,3)} ", exc_info=True)
            recover = True
            wait_variance = increase_variance(wait_variance)


# @TODO: clean up __main__
# @TODO: create new ER_diagram with fun_facts and alt_hyphenation
# @TODO: create link tables with added words (not just the links) -> join to wort table
