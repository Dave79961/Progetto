Progetto: Fanta Manager 2026/27 - Lega CertiFanta

Descrizione:
Applicazione web per gestire una lega di fantacalcio (CertiFanta League 2026-2027).
Backend: Flask (Python)
Frontend: React + Vite

Funzionalità attuali:
- Lista giocatori (asta) con filtri per ruolo e squadra.
- Gestione rosa personale (aggiungi/rimuovi giocatori, budget, limiti per ruolo).
- Calcolo formazione suggerita in base al modulo scelto.
- Sezione mercato (ancora vuota, da implementare).
- Sezione regolamento lega.

Problemi noti:
- Alcuni nomi dei giocatori sono errati o spezzati (es. "Carne Ecchi" invece di "Sarcarne Secchi").
- Il frontend resta bloccato su "Caricamento giocatori…" anche se /api/auction risponde 200.
- Possibile disallineamento tra i campi restituiti dal backend e quelli attesi dal frontend.

Obiettivi da implementare:
1. Correggere i nomi dei giocatori nel dataset.
2. Far sì che il frontend carichi correttamente i giocatori da /api/auction.
3. Implementare agenti per:
   - consigli di mercato personalizzati (in base alla rosa e ai ruoli scoperti);
   - monitoraggio calciomercato (acquisti, cessioni, svincolati);
   - aggiornamento semi-automatico del database giocatori.
4. Rendere l'applicazione accessibile via internet da telefono (deploy su un hosting pubblico).
5. Eventualmente: salvare la rosa su backend invece che solo in localStorage.

Struttura:
- backend/: Flask API
- frontend/: React app
- data/: file Excel/CSV con i giocatori (se presente)

Istruzioni per eseguire in locale:
Backend:
  cd backend
  python -m flask --app app run --debug

Frontend:
  cd frontend
  npm install (se non è mai stato fatto)
  npm run dev