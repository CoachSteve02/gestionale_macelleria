-- 1. Tabella ARTICOLO
CREATE TABLE ARTICOLO (
    id_articolo SERIAL PRIMARY KEY,
    denominazione VARCHAR(255) NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    allergeni TEXT,
    tipo_categoria VARCHAR(20) NOT NULL CHECK (tipo_categoria IN ('PREPARATO', 'TAGLIO', 'VARIO')) DEFAULT 'VARIO'
);

-- 2. Tabella LOTTO_MADRE (Materie prime e carichi da fornitore)
CREATE TABLE LOTTO_MADRE (
    id_lotto_madre SERIAL PRIMARY KEY,
    id_articolo INT NOT NULL REFERENCES ARTICOLO(id_articolo),
    codice_lotto_fornitore VARCHAR(100) NOT NULL,
    fornitore VARCHAR(255) NOT NULL,
    data_carico TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_scadenza DATE,
    data_macellazione DATE,
    paese_nascita VARCHAR(100),       -- o VARCHAR(3) se usi solo sigle ISO come ITA
    paese_allevamento VARCHAR(100),     -- o VARCHAR(3) se usi solo sigle ISO come ITA
    paese_macellazione VARCHAR(100),
    paese_sezionamento VARCHAR(100),
    flg_lotto_del_giorno BOOLEAN DEFAULT FALSE
);

-- Indici prestazionali
CREATE INDEX idx_articolo_tipo ON ARTICOLO(tipo_categoria);

-- 3. Tabella SESSIONE_LAVORAZIONE
CREATE TABLE SESSIONE_LAVORAZIONE (
    id_sessione SERIAL PRIMARY KEY,
    data_ora_inizio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operatore VARCHAR(100) NOT NULL,
    stato_sessione VARCHAR(50) DEFAULT 'Aperta',
    data_fine TIMESTAMP
);

-- 4. Tabella RICETTA e RICETTA_RIGA (Distinta Base Teorica)
CREATE TABLE RICETTA (
    id_ricetta SERIAL PRIMARY KEY,
    id_articolo_preparato INT NOT NULL REFERENCES ARTICOLO(id_articolo),
    versione INT DEFAULT 1,
    attiva BOOLEAN DEFAULT TRUE,
    data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indice unico parziale per garantire una sola ricetta attiva per preparato
CREATE UNIQUE INDEX idx_ricetta_attiva ON RICETTA(id_articolo_preparato) WHERE attiva = TRUE;

CREATE TABLE RICETTA_RIGA (
    id_ricetta_riga SERIAL PRIMARY KEY,
    id_ricetta INT REFERENCES RICETTA(id_ricetta),
    id_articolo_ingrediente INT REFERENCES ARTICOLO(id_articolo),
    ordine_etichetta INT NOT NULL
);

-- 5. Tabella LOTTO_PREPARATO (Prodotti finiti creati in laboratorio)
CREATE TABLE LOTTO_PREPARATO (
    id_lotto_preparato SERIAL PRIMARY KEY,
    id_sessione INT REFERENCES SESSIONE_LAVORAZIONE(id_sessione),
    id_articolo INT REFERENCES ARTICOLO(id_articolo),
    id_ricetta INT REFERENCES RICETTA(id_ricetta),
    codice_lotto_interno VARCHAR(100) UNIQUE NOT NULL,
    data_lavorazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_scadenza_preparato DATE NOT NULL
);

-- 6. Tabella COMPOSIZIONE_LAVORAZIONE (Tracciabilità HACCP N:M fisicamente avvenuta)
CREATE TABLE COMPOSIZIONE_LAVORAZIONE (
    id_composizione SERIAL PRIMARY KEY,
    id_lotto_preparato INT REFERENCES LOTTO_PREPARATO(id_lotto_preparato),
    id_lotto_madre INT REFERENCES LOTTO_MADRE(id_lotto_madre),
    note_associazione VARCHAR(255)
);

-- 7. Vista VW_ETICHETTA_PREPARATO
CREATE VIEW VW_ETICHETTA_PREPARATO AS
SELECT 
    lp.id_lotto_preparato,
    lp.codice_lotto_interno,
    ing.denominazione AS ingrediente,
    ing.allergeni,
    rr.ordine_etichetta
FROM LOTTO_PREPARATO lp
JOIN RICETTA r ON lp.id_ricetta = r.id_ricetta
JOIN RICETTA_RIGA rr ON r.id_ricetta = rr.id_ricetta
JOIN ARTICOLO ing ON rr.id_articolo_ingrediente = ing.id_articolo
ORDER BY lp.id_lotto_preparato, rr.ordine_etichetta;


-- 8. DML / Dati Iniziali

-- Popola ARTICOLO
-- TAGLI
INSERT INTO ARTICOLO (denominazione, categoria, allergeni, tipo_categoria) VALUES 
('Capocollo di Maiale', 'Suino', NULL, 'TAGLIO'),
('Carne Macinata Bovino', 'Bovino', NULL, 'TAGLIO'),
('Petto di Pollo', 'Avicolo', NULL, 'TAGLIO'),
('Bistecca Fiorentina', 'Bovino', NULL, 'TAGLIO');

-- VARI
INSERT INTO ARTICOLO (denominazione, categoria, allergeni, tipo_categoria) VALUES 
('Sale Marino Fine', 'Spezie', NULL, 'VARIO'),
('Pepe Nero Macinato', 'Spezie', NULL, 'VARIO'),
('Formaggio Caciocavallo', 'Latticini', 'Latte e derivati', 'VARIO'),
('Pane Grattugiato', 'Farinacei', 'Glutine', 'VARIO'),
('Uova Fresche', 'Uova', 'Uova', 'VARIO'),
('Budello Naturale', 'Involucri', NULL, 'VARIO');

-- PREPARATI
INSERT INTO ARTICOLO (denominazione, categoria, allergeni, tipo_categoria) VALUES 
('Polpette di Carne', 'Pronto Cuoci', 'Glutine, Uova, Latte e derivati', 'PREPARATO'),
('Bombette Pugliesi', 'Pronto Cuoci', 'Latte e derivati', 'PREPARATO'),
('Hamburger Classico', 'Pronto Cuoci', NULL, 'PREPARATO'),
('Salsiccia Fresca', 'Insaccati', NULL, 'PREPARATO');

-- Popola RICETTA e RICETTA_RIGA
-- Ricetta Polpette di Carne
INSERT INTO RICETTA (id_articolo_preparato, attiva) VALUES ((SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Polpette di Carne'), TRUE);
INSERT INTO RICETTA_RIGA (id_ricetta, id_articolo_ingrediente, ordine_etichetta) VALUES 
((SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Polpette di Carne')), (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Carne Macinata Bovino'), 1),
((SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Polpette di Carne')), (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Pane Grattugiato'), 2),
((SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Polpette di Carne')), (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Uova Fresche'), 3),
((SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Polpette di Carne')), (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Sale Marino Fine'), 4);

-- Ricetta Bombette Pugliesi
INSERT INTO RICETTA (id_articolo_preparato, attiva) VALUES ((SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Bombette Pugliesi'), TRUE);
INSERT INTO RICETTA_RIGA (id_ricetta, id_articolo_ingrediente, ordine_etichetta) VALUES 
((SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Bombette Pugliesi')), (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Capocollo di Maiale'), 1),
((SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Bombette Pugliesi')), (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Formaggio Caciocavallo'), 2),
((SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Bombette Pugliesi')), (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Sale Marino Fine'), 3),
((SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Bombette Pugliesi')), (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Pepe Nero Macinato'), 4);

-- Ricetta Hamburger Classico
INSERT INTO RICETTA (id_articolo_preparato, attiva) VALUES ((SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Hamburger Classico'), TRUE);
INSERT INTO RICETTA_RIGA (id_ricetta, id_articolo_ingrediente, ordine_etichetta) VALUES 
((SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Hamburger Classico')), (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Carne Macinata Bovino'), 1),
((SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Hamburger Classico')), (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Sale Marino Fine'), 2);

-- Ricetta Salsiccia Fresca
INSERT INTO RICETTA (id_articolo_preparato, attiva) VALUES ((SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Salsiccia Fresca'), TRUE);
INSERT INTO RICETTA_RIGA (id_ricetta, id_articolo_ingrediente, ordine_etichetta) VALUES 
((SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Salsiccia Fresca')), (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Capocollo di Maiale'), 1),
((SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Salsiccia Fresca')), (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Budello Naturale'), 2),
((SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Salsiccia Fresca')), (SELECT id_articolo FROM ARTICOLO WHERE denominazione = 'Sale Marino Fine'), 3);

-- Popola LOTTO_MADRE per articoli VARI come lotto del giorno
INSERT INTO LOTTO_MADRE (id_articolo, codice_lotto_fornitore, fornitore, data_scadenza)
SELECT id_articolo, 'LOTTO-DEFAULT', 'Fornitore Interno', CURRENT_DATE + INTERVAL '1 year'
FROM ARTICOLO WHERE tipo_categoria = 'VARIO';