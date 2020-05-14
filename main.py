import logging
import re
import json
from time import sleep
import numpy as np
from bs4 import BeautifulSoup
import requests


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


BASE_URL = "https://www.duden.de"
FIRST_WORD = "/rechtschreibung/d_Korrekturzeichen_fuer_tilgen"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4), "\
            + "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Chrome/71.0.3578.98"}
Duden = {}

class Word():
    """Class for a single word of the german dictionary DUDEN
    """
    def __init__(self, soup, url):
        self.soup = soup
        self.url = url

    
    @property
    def name(self):
        """
        Word string (without article)
        """
        return self.soup.find("span", class_="breadcrumb__crumb").text.strip()

    @property
    def full_word(self):
        """Get the full word (word plus article)
        """
        return self.soup.find("h1", class_=re.compile(r"lemma__title")).text.replace("\xa0", " ").strip()
        
    def _get_tl_tuple(self, key, element=None):
        if not element:
            element = self.soup
        tuples = element.find_all("dl", class_="tuple")
        for tup in tuples:
            if key in tup.text:
                return tup.find("dd", class_="tuple__val").text.strip()
        return None

    @property
    def part_of_speech(self):
        """Get the part of speech (Wortart)
        """
        try:
            return self._get_tl_tuple(key="Wortart")
        except AttributeError:
            return None

    @property
    def article(self):
        """Get article if the word is a noun
        """
        article = self.soup.find("span", class_="lemma__determiner")
        if article:
            return article.text
        return None

    @property
    def frequency(self):
        """Get the word frequency:
        1: less than one in a million words
        2: more than one in a million
        3: ~ one in a 100k
        4: ~ one in 10k
        5: ~ one in 1k
        """
        try:
            freq = self._get_tl_tuple(key="Häufigkeit")
        except AttributeError:
            return None
        if freq: 
            return len(freq.replace("░", ""))
        return None
        
    @property
    def hyphenation(self):
        """Get the correct hyphenation of the word
        """
        try:
            hyphenation = self._get_tl_tuple(key="Worttrennung")
            if not hyphenation:
                dic = {}
                dic["Von Duden empfohlene Trennung"] = self._get_tl_tuple(key="Von Duden empfohlene Trennung")
                dic["Alle Trennmöglichkeiten"] = self._get_tl_tuple(key="Alle Trennmöglichkeiten")
                return dic
            return hyphenation
        except AttributeError:
            return None

    @property
    def origin(self):
        """Get the origin of the word
        """
        origin = self.soup.find("div", id="herkunft")
        if origin:
            return origin.p.text.strip()
        return None


    @property
    def related_form(self):
        """Get the related form of a word (rare)
        """
        related_form = self._get_tl_tuple(key="Verwandte Form")
        if related_form:
            return related_form.strip()
        return None


    @property
    def alternative_spelling(self):
        """Some words have several ways of spelling them.
        Retrieve those spelling variants.
        """
        rec_spelling = self._get_tl_tuple(key="Von Duden empfohlene Schreibung")
        alt_spelling = self._get_tl_tuple(key="Alternative Schreibung")

        if rec_spelling and alt_spelling:
            dic = {}
            dic["Von Duden empfohlene Schreibung"] = rec_spelling.strip()
            dic["Alternative Schreibung"] = alt_spelling.strip()
            return dic
        return None

    @property
    def sign(self):
        """Some words have a sign that belongs to them.
        Retrieve that sign.
        """
        sign = self._get_tl_tuple(key="Zeichen")
        if sign:
            return sign.strip()
        return None

    @property
    def short_form(self):
        """Get the short version of a word if it exists.
        """
        short = self._get_tl_tuple(key="Kurzform")
        if short:
            return short.strip()
        return None

    @property
    def short_form_of(self):
        """Get the long version of the word
        """
        short = self._get_tl_tuple(key="Kurzform für")
        if short:
            return short.strip()
        return None

    def _get_examples(self, element):

        examples = element.find("dt", string=re.compile(r"Beispiel")).next_sibling
        examples_li = examples.find_all("li")
        examples = []
        for example in examples_li:
            examples.append(example.text)
        
        return examples or None

    def _get_note_list(self, key, element):
        """For a given key such as "Beispiel" in a soup object element, 
        return the list of the key values
        """
        note_title = element.find("dt", class_="note__title", string=re.compile(key))
        res_list = []
        if note_title:
            note_list = note_title.next_sibling.find_all("li")
            
            for li in note_list:
                res_list.append(li.text.strip())
        return res_list or None

    @property
    def meaning(self):
        meanings = []
        dic = {}
        dic["Bedeutungen"] = []
        dic_el = {}
        meaning = self.soup.find("div", id="bedeutung")
        if meaning:
            #examples = self._get_examples(element=meaning)
            #examples = self._get_note_list("Beispiel", meaning)
            if meaning.find("p"):
                dic_el["Bedeutung"] = meaning.p.text.strip().replace("\xa0", " ")
            else: 
                dic_el["Bedeutung"] = None
            dic_el["Beispiele"] = self._get_note_list("Beispiel", meaning)
            dic_el["Gebrauch"] = self._get_tl_tuple("Gebrauch", meaning)
            dic_el["Grammatik"] = self._get_tl_tuple("Grammatik", meaning)
            dic["Bedeutungen"].append(dic_el)
            return dic["Bedeutungen"]

        meaning_elements = self.soup.find("div", id="bedeutungen")

        if not meaning_elements:
            dic = {}
            dic["Bedeutungen"] = None
            dic["Beispiele"] = self._get_note_list("Beispiel", self.soup)
            dic["Gebrauch"] = self._get_tl_tuple("Gebrauch", self.soup)
            dic["Grammatik"] = self._get_tl_tuple("Grammatik", self.soup)
            return dic

        meaning_elements = meaning_elements.find("ol", recursive=False) or meaning_elements.find("ul", recursive=False)

        
        for li in meaning_elements.find_all("li", recursive=False):
            elements = li.find_all("div", class_="enumeration__text")
            for element in elements:
                dic = {}
                meaning = element.text.replace("\xa0", " ")
                dic["Bedeutung"] = meaning

                par = element.parent
                dic["Beispiele"] = self._get_note_list("Beispiel", par)
                dic["Gebrauch"] = self._get_tl_tuple("Gebrauch", par)
                dic["Grammatik"] = self._get_tl_tuple("Grammatik", par)
                meanings.append(dic)

        return meanings



        # @TODO: Implementierung für Bedeutungen am "Haus" Beispiel

    @property
    def synonyms(self):
        """Get the synonyms of the word
        """
        synonyme = self.soup.find("div", id="synonyme")
        if synonyme:
            synonyme = [synonym.text.strip() for synonym in synonyme.find_all("li")]
        return synonyme

    def get_next_word(self):
        next_words = self.soup.find("h3", class_="hookup__title", string = "Im Alphabet danach").next_sibling
        word_link = next_words.find("a")
        if word_link:
            return word_link.get("href")
        return None


    def return_word_entry(self):
        dic_entry = {}
        #dic_entry["Wort"] = self.word
        dic_entry["Ganzes Wort"] = self.full_word
        dic_entry["Artikel"] = self.article
        dic_entry["Wortart"] = self.part_of_speech
        dic_entry["Bedeutungen"] = self.meaning
        dic_entry["Häufigkeit"] = self.frequency
        dic_entry["Worttrennung"] = self.hyphenation
        dic_entry["Herkunft"] = self.origin
        dic_entry["Verwandte Form"] = self.related_form
        dic_entry["Alternative Schreibweise"] = self.alternative_spelling
        dic_entry["Zeichen"] = self.sign
        dic_entry["Kurzform"] = self.short_form
        dic_entry["Kurzform für"] = self.short_form_of
        dic_entry["Synonyme"] = self.synonyms
        dic_entry["URL"] = self.url

        return dic_entry
            

def load_word(word_url):
    """Get new Word instance from Duden Website

    Arguments:
        word_url {String} -- word url of the form "/rechtschreibung/{word}"

    Returns:
        Word -- returns an instance of the Word Class
    """
    url = BASE_URL + word_url

    # try:
    source = requests.get(url, headers=HEADERS)
    # except Exception as errc:
    #         print("There seems to be no internet connection right now. Try again later!", errc)
                        
    code = source.status_code
    if code == 200:
        soup = BeautifulSoup(source.text, 'lxml')
    else:
        raise Exception(f"Unexpected response code: {source.status_code}")
        logger.exception(f"Unexpected response code for {url}: {source.status_code}")

    return Word(soup, url)
    


url = FIRST_WORD
url = "/rechtschreibung/Abbau"
for i in range(2):
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

#@TODO: grammar(): use Abbau as an example
#@TODO: put failed words automatically in a list (their urls)
#@TODO: split up the work in 26 parts and use proxies to scrape all of them
#@TODO: save words on database

