CREATE TABLE wort
            (id INTEGER PRIMARY KEY, name TEXT, ganzes_wort TEXT, artikel TEXT, wortart TEXT, haeufigkeit INTEGER, worttrennung TEXT, alternative_worttrennung TEXT, herkunft TEXT, verwandte_form TEXT, alternative_schreibweise TEXT, zeichen TEXT, kurzform TEXT, kurzform_fuer TEXT, fun_fact TEXT, url TEXT
            
             );

CREATE TABLE bedeutungen
            (id INTEGER PRIMARY KEY, bedeutung TEXT, grammatik TEXT, wort_id INTEGER
            ,FOREIGN KEY (wort_id) REFERENCES wort(id)
            ON DELETE CASCADE );

CREATE TABLE wendungen_redensarten_sprichwoerter
            (id INTEGER PRIMARY KEY, wendung_redensart_sprichwort TEXT, bedeutungen_id INTEGER
            ,FOREIGN KEY (bedeutungen_id) REFERENCES bedeutungen(id)
            ON DELETE CASCADE );

CREATE TABLE typische_verbindungen_links
            (id INTEGER PRIMARY KEY, typische_verbindung_url TEXT, wort_id INTEGER
            ,FOREIGN KEY (wort_id) REFERENCES wort(id)
            ON DELETE CASCADE );

CREATE TABLE synonyme_links
            (id INTEGER PRIMARY KEY, synonym_url TEXT, wort_id INTEGER
            ,FOREIGN KEY (wort_id) REFERENCES wort(id)
            ON DELETE CASCADE );

CREATE TABLE synonyme
            (id INTEGER PRIMARY KEY, synonyme TEXT, wort_id INTEGER
            ,FOREIGN KEY (wort_id) REFERENCES wort(id)
            ON DELETE CASCADE );

CREATE TABLE gebrauch
            (id INTEGER PRIMARY KEY, gebrauch TEXT, bedeutungen_id INTEGER
            ,FOREIGN KEY (bedeutungen_id) REFERENCES bedeutungen(id)
            ON DELETE CASCADE );

CREATE TABLE beispiele
            (id INTEGER PRIMARY KEY, beispiel TEXT, bedeutungen_id INTEGER
            ,FOREIGN KEY (bedeutungen_id) REFERENCES bedeutungen(id)
            ON DELETE CASCADE );

CREATE TABLE antonyme_links
            (id INTEGER PRIMARY KEY, antonym_url TEXT, wort_id INTEGER
            ,FOREIGN KEY (wort_id) REFERENCES wort(id)
            ON DELETE CASCADE );

CREATE TABLE antonyme
            (id INTEGER PRIMARY KEY, antonyme TEXT, wort_id INTEGER
            ,FOREIGN KEY (wort_id) REFERENCES wort(id)
            ON DELETE CASCADE );
