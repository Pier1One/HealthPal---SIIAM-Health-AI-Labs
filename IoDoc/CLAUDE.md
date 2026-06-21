# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Progetto: IoDoc — Health Manager MVP

App locale per centralizzare documenti sanitari personali. L'utente trascina PDF/immagini nell'app, l'AI estrae automaticamente informazioni cliniche rilevanti (farmaci, patologie, visite, esami). L'utente conferma o corregge i dati estratti e può aggiungere manualmente ulteriori informazioni su qualsiasi campo (farmaci, misurazioni, appuntamenti, ecc.). L'app invia notifiche desktop OS nei tempi stabiliti e le mantiene attive finché l'utente non le segna come "fatto" o "non fatto".

**Non è un'app pubblica.** È un MVP locale da dimostrare, senza autenticazione, senza cloud, senza compliance GDPR.

---

## Stack

| Layer | Tecnologia |
|---|---|
| UI | Streamlit (Python) |
| Database | SQLite (`database.db` nella root) |
| Storage documenti | Cartella locale `documents/` |
| AI estrazione | Claude API (`claude-sonnet-4-6`) |
| Parsing PDF | `pdfplumber` o `PyMuPDF` |
| Notifiche desktop | `plyer` |
| Scheduler background | `APScheduler` |

## Struttura Cartelle

```
IoDoc/
├── app.py                  # entry point, navigazione tra pagine
├── database.db             # SQLite, creato automaticamente al primo avvio
├── documents/              # PDF e immagini caricati (creata automaticamente)
├── pages/                  # pagine Streamlit
│   ├── profilo.py
│   ├── upload.py
│   ├── piano_sanitario.py
│   ├── dashboard.py
│   ├── misurazioni.py
│   └── timeline.py
├── db/
│   ├── schema.py           # CREATE TABLE e init del DB
│   └── queries.py          # tutte le funzioni di lettura/scrittura
├── ai/
│   └── extractor.py        # chiamata Claude API + parsing risposta
├── notifications/
│   ├── scheduler.py        # APScheduler background thread, avviato da app.py
│   └── notifier.py         # funzione send_notification() via plyer
├── requirements.txt
└── .env                    # ANTHROPIC_API_KEY (non committare)
```

## Comandi

```bash
# Installa dipendenze
pip install -r requirements.txt

# Avvia l'app
streamlit run app.py

# L'app gira su http://localhost:8501
```

## Modello Dati (SQLite)

Tabelle principali — vedere `db/schema.py` per la definizione completa:

- `user` — profilo paziente (nome, data_nascita, sesso, altezza, peso)
- `condition` — patologie (nome, data_diagnosi, attiva)
- `medication` — farmaci (nome, dosaggio, data_inizio, data_fine, attivo)
- `medication_schedule` — orari assunzione (medication_id, orario, frequenza)
- `monitoring_task` — monitoraggi periodici (tipo, frequenza, orario)
- `appointment_task` — visite (specialista, frequenza, data_ultima, data_prossima)
- `exam_task` — esami (tipo, frequenza, data_ultima, data_prossima)
- `prescription_task` — ricette (farmaco, frequenza_rinnovo, data_prossima)
- `document` — documenti caricati (file_path, nome_file, tipo, data_upload)
- `measurement` — misurazioni (tipo, valore, data, ora)
- `notification` — notifiche generate (tipo, riferimento_id, scheduled_at, sent_at, status: pending/sent/done/skipped)

## Inserimento Manuale Dati

Ogni sezione del piano sanitario (farmaci, misurazioni, appuntamenti, esami, ricette) deve avere:
- Una vista dei dati esistenti (estratti da AI o inseriti manualmente)
- Un form per aggiungere nuove voci manualmente
- La possibilità di modificare o eliminare ogni voce

Le voci inserite manualmente seguono lo stesso schema DB delle voci estratte da AI — non esistono tabelle separate.

## Flusso Upload Documento

1. Utente trascina PDF/immagine in `st.file_uploader()`
2. Il file viene salvato in `documents/{timestamp}_{nome_file}`
3. Il testo viene estratto con `pdfplumber` (PDF) o `pytesseract` (immagini)
4. Il testo viene inviato a Claude API con prompt strutturato
5. Claude restituisce JSON con patologie, farmaci, visite, esami estratti
6. L'utente vede i dati estratti e può confermare / modificare / eliminare
7. I dati confermati vengono salvati nelle rispettive tabelle SQLite

## Sistema Notifiche

Le notifiche sono notifiche desktop OS native (via `plyer`), non notifiche in-app.

### Tempistiche

| Tipo | Anticipo |
|---|---|
| Farmaci | 30 minuti prima dell'orario di assunzione |
| Misurazioni | 30 minuti prima dell'orario pianificato |
| Appuntamenti / Visite | 15 giorni prima della data_prossima |
| Analisi / Esami | 7 giorni prima della data_prossima |
| Ricette | 7 giorni prima della data_prossima |

### Ciclo di vita di una notifica

1. Quando l'utente salva/conferma un elemento con orario o data, `scheduler.py` calcola `scheduled_at` e inserisce una riga in `notification` con `status=pending`
2. `APScheduler` gira in background (thread separato) e ogni minuto controlla le notifiche `pending` il cui `scheduled_at` è nel passato
3. Invia la notifica OS via `plyer` e aggiorna `status=sent`
4. La notifica `sent` rimane visibile nella Dashboard finché l'utente clicca **Fatto** (`status=done`) o **Non fatto** (`status=skipped`)
5. Le notifiche `sent` non risolte compaiono sempre in cima alla Dashboard come banner persistenti

### Rescheduling

Quando l'utente segna una visita, un esame o una ricetta come completata, `scheduler.py` calcola automaticamente la prossima `data_prossima` in base alla frequenza e genera una nuova notifica.

## Estrazione AI

Il file `ai/extractor.py` invia il testo del documento a Claude e si aspetta una risposta JSON strutturata. Usare sempre `model="claude-sonnet-4-6"`. La risposta deve essere parsata con `json.loads()` — istruire il modello a rispondere solo con JSON valido, senza testo aggiuntivo.

## Convenzioni

- Tutto il codice UI è in `pages/` — ogni pagina è un file separato
- Tutta la logica DB è in `db/queries.py` — le pagine non scrivono SQL direttamente
- La chiave API si legge con `os.getenv("ANTHROPIC_API_KEY")` — mai hardcoded
- Il database viene inizializzato all'avvio da `db/schema.py` se non esiste già
- La cartella `documents/` viene creata automaticamente se non esiste

## Priorità MVP (ordine di sviluppo)

1. Schema DB + init automatico (inclusa tabella `notification`)
2. Pagina profilo paziente
3. Upload PDF + salvataggio locale
4. Estrazione AI + schermata conferma + inserimento manuale
5. Piano sanitario (visualizzazione + modifica di tutti i dati)
6. Sistema notifiche: `notifier.py` + `scheduler.py` + generazione notifiche al salvataggio
7. Dashboard "Oggi" con banner notifiche persistenti + azioni Fatto/Non fatto
8. Inserimento misurazioni manuali
9. Timeline
