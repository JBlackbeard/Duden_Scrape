from time import sleep
from main import load_word


def test_load_word():
    url = "/rechtschreibung/Haus"
    word_haus = load_word(url)
    assert word_haus is not None

url = "/rechtschreibung/Haus"
word_haus = load_word(url)
sleep(0.5)

def test_name():
    assert word_haus.name == "Haus"

def test_article():
    assert word_haus.article == "das"

def test_full_name():
    assert word_haus.full_word == "Haus, das"

def test_part_of_speech():
    assert word_haus.part_of_speech == "Substantiv, Neutrum"

def test_origin():
    assert word_haus.origin.replace("\xa0", " ") == "mittelhochdeutsch, althochdeutsch hūs, eigentlich = das Bedeckende, Umhüllende"

def test_meaning_haus():
    assert word_haus.meaning != []

url = "/rechtschreibung/Heber"
word_heber = load_word(url)

def test_meaning_heber():
    assert word_heber.meaning != []

url = "/rechtschreibung/Hausflur"
word_hausflur = load_word(url)
sleep(0.5)

def test_frequency():
    assert word_hausflur.frequency == 2

def test_hyphenation():
    assert word_hausflur.hyphenation == "Haus|flur"

url = "/rechtschreibung/Hausarrest"

word_hausarrest = load_word(url)
sleep(1)

def test_meaning_hausarrest():
    assert word_hausarrest.meaning == [{'Bedeutung': 'Strafe, bei der dem Bestraften verboten ist, das Haus zu verlassen',
                            'Beispiele': ['jemanden unter Hausarrest stellen',
                                          'er steht unter Hausarrest']}]


url = "/rechtschreibung/Hausbibliothek"
word_hausbibliothek = load_word(url)
sleep(0.5)

def test_hyphenation_edge():
    assert word_hausbibliothek.hyphenation == {'Alle Trennmöglichkeiten': 'Haus|bi|blio|thek', 
    'Von Duden empfohlene Trennung': 'Haus|bi|blio|thek'}

url = "/rechtschreibung/Hauserin"
word_hauserin = load_word(url)
sleep(1)

def test_related_form():
    assert word_hauserin.related_form == "Häuserin"

url = "/rechtschreibung/Haussa_Sprache_Afrika"
word_hussa = load_word(url)

def test_alternative_spelling():
    assert word_hussa.alternative_spelling == {"Alternative Schreibung": "Hausa", 
    "Von Duden empfohlene Schreibung": "Haussa"}

url = "/rechtschreibung/H_Dur"
word_hdur = load_word(url)
sleep(1)

def test_sign():
    assert "H" == word_hdur.sign

url = "/rechtschreibung/Haute_Couture"
word_haute = load_word(url)
sleep(1)

def test_short_form():
    assert word_haute.short_form == "Couture"