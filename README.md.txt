# System Ekspercki Doboru Metodyki IT

## Opis Projektu

Aplikacja wspomagająca podejmowanie decyzji, która analizuje fazy projektu w oparciu o model PDCA, sugerując dopasowaną metodykę zarządzania (Zwinne, Szczupłe, Kaskadowe lub Hybrydowe).

## Funkcjonalności

- Interaktywny interfejs graficzny (GUI) zbudowany z użyciem ttkbootstrap.
- Dynamiczny, wielofazowy model analityczny oparty na cyklu PDCA.
- Zewnętrzna konfiguracja modelu w pliku `konfiguracja.json`.
- Generowanie raportów PDF z wynikami analizy.

## Instalacja i Uruchomienie

1.  **Sklonuj repozytorium.**
2.  **Zainstaluj wymagane biblioteki:**
    ```
    pip install -r requirements.txt
    ```
3.  **Uruchom aplikację:**
    ```
    python gui_prototyp.py
    ```