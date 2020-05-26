import logging
import random
import requests
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
from requests.packages.urllib3.util.retry import Retry
from .models import Word

logger = logging.getLogger(__name__)

HEADERS = [{"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4), "\
            + "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Chrome/71.0.3578.98"},
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64), "\
            + "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"},
            {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"},
            {"User-Agent": "Mozilla/5.0 CK={} (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"},
            {"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)"},
            {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"},
            {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko)"},
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363"},
            {"User-Agent": "Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36"},
            {"User-Agent": "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)"},
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"}
            ]

class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)

DEFAULT_TIMEOUT = 10
adapter = TimeoutHTTPAdapter(timeout=2.5)


retries = Retry(
    total=2,
    status_forcelist=[429, 500, 502, 503, 504],
    backoff_factor=1
)

http = requests.Session()
http.mount("https://", TimeoutHTTPAdapter(max_retries=retries))
http.mount("http://", TimeoutHTTPAdapter(max_retries=retries))

def load_word(word_url, base_url="https://www.duden.de",
              headers=random.choice(HEADERS)):
    """Get new Word instance from Duden Website

    Arguments:
        word_url {String} -- word url of the form "/rechtschreibung/{word}"

    Returns:
        Word -- returns an instance of the Word Class
    """
    url = base_url + word_url

    # try:
    source = http.get(url, headers=headers)
    # except Exception as errc:
    #         print("There seems to be no internet connection right now. Try again later!", errc)
                        
    code = source.status_code
    if code == 200:
        soup = BeautifulSoup(source.text, 'lxml')
    else:
        raise Exception(f"Unexpected response code: {source.status_code}")
        logger.exception(f"Unexpected response code for {url}: {source.status_code}")

    return Word(soup, url)

def add_word_db(word_entry, db, url):
    synonyme = word_entry.pop("synonyme") or None
    antonyme = word_entry.pop("antonyme") or None
    db.add("wort", word_entry)
    wort_id = db.select("id", "wort", {"url": "https://www.duden.de" + url}).fetchone()[0]
    
    if synonyme:
        for synonym in synonyme.split(";"):
            db.add("synonyme", {"synonyme": synonym, "wort_id": wort_id})

    if antonyme:
        for antonym in antonyme.split(";"):
            db.add("antonyme", {"antonyme": antonym, "wort_id": wort_id})

    return wort_id

def add_meanings_db(meanings, db, wort_id):
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

def add_link_entries_db(link_entries, db, wort_id, table_name, column_link_name):
    if link_entries:
        for link in link_entries:
            if link:
                db.add(table_name, {column_link_name: "https://www.duden.de" + link, "wort_id": wort_id})

def create_tables(db):
    word_dict = {"id": "INTEGER PRIMARY KEY", "name": "TEXT", "ganzes_wort": "TEXT", "artikel": "TEXT",
                    "wortart": "TEXT", "haeufigkeit": "INTEGER",
                    "worttrennung": "TEXT", "alternative_worttrennung": "TEXT", "herkunft": "TEXT", "verwandte_form": "TEXT", 
                    "alternative_schreibweise": "TEXT", "zeichen": "TEXT", "kurzform": "TEXT",
                    "kurzform_fuer": "TEXT", "fun_fact": "TEXT",
                    "url": "TEXT"}

    synonyms_dict = {"id": "INTEGER PRIMARY KEY", "synonyme": "TEXT", "wort_id": "INTEGER"}
    synonyms_references = {"wort_id": "wort(id)"}

    antonyms_dict = {"id": "INTEGER PRIMARY KEY", "antonyme": "TEXT", "wort_id": "INTEGER"}
    antonyms_references = {"wort_id": "wort(id)"}

    meaning_dict = {"id": "INTEGER PRIMARY KEY", "bedeutung": "TEXT",
                    "grammatik": "TEXT", "wort_id": "INTEGER"}
    meaning_references = {"wort_id": "wort(id)"}

    examples_dict = {"id": "INTEGER PRIMARY KEY", "beispiel": "TEXT", "bedeutungen_id": "INTEGER"}
    examples_references = {"bedeutungen_id": "bedeutungen(id)"}

    sayings_dict = {"id": "INTEGER PRIMARY KEY", "wendung_redensart_sprichwort": "TEXT", "bedeutungen_id": "INTEGER"}
    sayings_references = {"bedeutungen_id": "bedeutungen(id)"}

    usage_dict = {"id": "INTEGER PRIMARY KEY", "gebrauch": "TEXT", "bedeutungen_id": "INTEGER"}
    usage_references = {"bedeutungen_id": "bedeutungen(id)"}

    synonyms_url_dict = {"id": "INTEGER PRIMARY KEY", "synonym_url": "TEXT", "wort_id": "INTEGER"}
    synonyms_url_references = {"wort_id": "wort(id)"}

    antonyms_url_dict = {"id": "INTEGER PRIMARY KEY", "antonym_url": "TEXT", "wort_id": "INTEGER"}
    antonyms_url_references = {"wort_id": "wort(id)"}

    typical_connections_url_dict = {"id": "INTEGER PRIMARY KEY", "typische_verbindung_url": "TEXT", "wort_id": "INTEGER"}
    typical_connections_url_references = {"wort_id": "wort(id)"}
 


    db.create_table(table_name="wort", columns=word_dict)
    db.create_table(table_name="synonyme", columns=synonyms_dict, references=synonyms_references, cascade_delete=True)
    db.create_table(table_name="antonyme", columns=antonyms_dict, references=antonyms_references, cascade_delete=True)
    db.create_table(table_name="bedeutungen", columns=meaning_dict, references=meaning_references, cascade_delete=True)
    db.create_table(table_name="beispiele", columns=examples_dict, references=examples_references, cascade_delete=True)
    db.create_table(table_name="wendungen_redensarten_sprichwoerter", columns=sayings_dict, references=sayings_references, cascade_delete=True)
    db.create_table(table_name="gebrauch", columns=usage_dict, references=usage_references, cascade_delete=True)
    db.create_table(table_name="synonyme_links", columns=synonyms_url_dict, references=synonyms_url_references, cascade_delete=True)
    db.create_table(table_name="antonyme_links", columns=antonyms_url_dict, references=antonyms_url_references, cascade_delete=True)
    db.create_table(table_name="typische_verbindungen_links", columns=typical_connections_url_dict, references=typical_connections_url_references, cascade_delete=True)

class RangeDict(dict):
    def __getitem__(self, item):
        if not isinstance(item, range):
            for key in self:
                if item in key:
                    return self[key]
            raise KeyError(item)
        else:
            return super().__getitem__(item)