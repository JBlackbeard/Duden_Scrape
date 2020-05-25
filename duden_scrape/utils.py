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

DEFAULT_TIMEOUT = 5
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
    db.add("wort", word_entry)
    wort_id = db.select("id", "wort", {"url": "https://www.duden.de" + url}).fetchone()[0]
    
    if synonyme:
        for synonym in synonyme.split(";"):
            db.add("synonyme", {"synonyme": synonym, "wort_id": wort_id})

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