import re

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
            if re.search(key, tup.text):
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
                return dic["Von Duden empfohlene Trennung"]
            return hyphenation
        except AttributeError:
            return None

    @property
    def alt_hyphenation(self):
        """Get alternative hyphenation of a word
        """
        try:
            alt_hyphenation = self._get_tl_tuple(key="Worttrennung")
            if not alt_hyphenation:
                dic = {}
                dic["Alle Trennmöglichkeiten"] = self._get_tl_tuple(key="Alle Trennmöglichkeiten")
                return dic["Alle Trennmöglichkeiten"]
            return alt_hyphenation
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
            return dic["Alternative Schreibung"] # just return one value
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
        short = self._get_tl_tuple(key="Kurzform(?!\s+für)") # don't match "Kurzform für"
        if short:
            return short.strip()
        return None

    @property
    def short_form_of(self):
        """Get the long version of the word
        """
        short = self._get_tl_tuple(key="Kurzform für")
        if not short:
            short = self._get_tl_tuple(key="Kurz für")
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
            if note_title.next_sibling == ' ':
                note_title = note_title.next_sibling
            if note_title and note_title is not ' ':
                note_list = note_title.next_sibling.find_all("li")
                
                for li in note_list:
                    res_list.append(li.text.strip())
        return res_list or None
        #return "; ".join(res for res in res_list) or None

    @property
    def meaning(self):
        meanings = []
        dic = {}
        dic["Bedeutungen"] = []
        dic_el = {}
        meaning = self.soup.find("div", id="bedeutung")
        if meaning:
            if meaning.find("p"):
                dic_el["Bedeutung"] = meaning.p.text.strip().replace("\xa0", " ")
            else: 
                dic_el["Bedeutung"] = None
            dic_el = self._get_meaning_additions(dic_el, meaning)
            dic["Bedeutungen"].append(dic_el)
            return dic["Bedeutungen"]

        meaning_elements = self.soup.find("div", id="bedeutungen")

        if not meaning_elements:
            #dic = {}
            #dic["Bedeutungen"] = []
            dic_el["Bedeutung"] = None
            dic_el = self._get_meaning_additions(dic_el, self.soup)
            dic["Bedeutungen"].append(dic_el)
            return dic["Bedeutungen"]

        meaning_elements = meaning_elements.find("ol", recursive=False) or meaning_elements.find("ul", recursive=False)

        
        for li in meaning_elements.find_all("li", recursive=False):
            elements = li.find_all("div", class_="enumeration__text")
            for element in elements:
                dic = {}
                meaning = element.text.replace("\xa0", " ")
                dic["Bedeutung"] = meaning

                par = element.parent
                dic = self._get_meaning_additions(dic, par)
                meanings.append(dic)

        return meanings

    @property
    def synonyms(self):
        """Get the synonyms of the word
        """
        synonyme = self.soup.find("div", id="synonyme")
        if synonyme:
            synonyme = [synonym.text.strip() for synonym in synonyme.find_all("li")]
            synonyme = "; ".join(synonym for synonym in synonyme)
        return synonyme

    @property
    def antonyms(self):
        """Get the antonyms of the word
        """
        antonyme = self.soup.find("div", id="antonyme")
        if antonyme:
            antonyme = [antonym.text.strip() for antonym in antonyme.find_all("li")]
            antonyme = "; ".join(antonym for antonym in antonyme)
        return antonyme

    @property
    def synonym_links(self):
        """Get the duden links for the linked synonyms
        """
        synonyme = self.soup.find("div", id="synonyme")
        if synonyme:
            synonym_urls = synonyme.find("ul").find_all("a")
            synonym_urls = [synonym_url.get("href") for synonym_url in synonym_urls]
            return synonym_urls
        return None

    @property
    def antonym_links(self):
        """Get the duden links for the linked antonyms
        """
        antonyme = self.soup.find("div", id="antonyme")
        if antonyme:
            antonym_urls = antonyme.find("ul").find_all("a")
            antonym_urls = [antonym_url.get("href") for antonym_url in antonym_urls]
            return antonym_urls
        return None

    @property
    def typical_connections(self):
        """Get words that often appear together with this word
        """
        element = self.soup.find("figure", class_="tag-cluster__cluster")
        if element:
            link_elements = element.find_all("a")
            if link_elements:
                related_words = [rel_word.text for rel_word in link_elements]
                related_words = "; ".join(rel_word for rel_word in related_words)
            return related_words
        return None

    @property
    def typical_connections_links(self):
        """Get words (links) that often appear together with this word
        """
        element = self.soup.find("figure", class_="tag-cluster__cluster")
        if element:
            link_elements = element.find_all("a")
            if link_elements:
                related_word_urls = [rel_word.get("href") for rel_word in link_elements]
            return related_word_urls
        return None

    @property
    def fun_fact(self):
        """trivia info about the word"""
        element = self.soup.find("div", id="wussten_sie_schon")
        if element:
            fun_facts = [li.text for li in element.find_all("li")]
            fun_facts = "; ".join(fun_fact for fun_fact in fun_facts)
            return fun_facts
        return None

    def _get_meaning_additions(self, dic, soup):
        """Add additional informations to the meaning
        """
        dic["beispiele"] = self._get_note_list("Beispiel", soup)
        dic["wendungen_redensarten_sprichwoerter"] = self._get_note_list("Wendungen", soup)
        dic["gebrauch"] = self._get_tl_tuple("Gebrauch", soup)
        dic["grammatik"] = self._get_tl_tuple("Grammatik", soup)

        return dic
        
    def get_next_word(self):
        next_words = self.soup.find("h3", class_="hookup__title", string="Im Alphabet danach").next_sibling
        word_link = next_words.find("a")
        if word_link:
            return word_link.get("href")
        return None


    def return_word_entry(self):
        dic_entry = {}
        #dic_entry["Wort"] = self.word
        dic_entry["name"] = self.name
        dic_entry["ganzes_wort"] = self.full_word
        dic_entry["artikel"] = self.article
        dic_entry["wortart"] = self.part_of_speech
        #dic_entry["Bedeutungen"] = self.meaning
        dic_entry["haeufigkeit"] = self.frequency
        dic_entry["worttrennung"] = self.hyphenation
        dic_entry["alternative_worttrennung"] = self.alt_hyphenation
        dic_entry["herkunft"] = self.origin
        dic_entry["verwandte_form"] = self.related_form
        dic_entry["alternative_schreibweise"] = self.alternative_spelling
        dic_entry["zeichen"] = self.sign
        dic_entry["kurzform"] = self.short_form
        dic_entry["kurzform_fuer"] = self.short_form_of
        dic_entry["synonyme"] = self.synonyms
        dic_entry["antonyme"] = self.antonyms
        #dic_entry["typische_verbindungen"] = self.typical_connections
        dic_entry["fun_fact"] = self.fun_fact
        dic_entry["url"] = self.url

        return dic_entry

    def return_meaning(self):
        dic_entry = {}
        dic_entry["bedeutungen"] = self.meaning

        return dic_entry

    def return_links(self):
        """
        """
        dic_entry = {}
        dic_entry["synonyme_links"] = self.synonym_links
        dic_entry["antonyme_links"] = self.antonym_links
        dic_entry["typische_verbindungen_links"] = self.typical_connections_links

        return dic_entry

