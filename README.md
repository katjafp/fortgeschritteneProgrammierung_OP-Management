# Digitales OP-Planungs- & Ressourcenmanagement

Ein Python-Projekt zur digitalen Verwaltung von OP-Sälen, Personal, Geräten,
chirurgischen Instrumenten und Verbrauchsmaterial in einer Klinik. Das System
prüft bei jeder Buchung automatisch alle benötigten Ressourcen, verwaltet
Lagerbestände und kann bereits geplante Operationen zeitlich verschieben
(inkl. automatischer Anpassung aller Folgetermine im selben Saal).

## Installation & Ausführung

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Konsolen-Testszenario** 
```bash
python main.py
```

**Streamlit-Oberfläche:**
```bash
streamlit run app.py
```

## Tests ausführen

```bash
python -m unittest discover tests
```

## Aufbau

Drei Kernklassen bilden über Vererbung die Ressourcen ab:
- `Ressource` ist die Basisklasse für alles, was für eine OP blockiert werden
  kann (z.B. ein Arzt oder ein Röntgengerät).
- `Instrument` erbt davon und braucht nach jeder Nutzung automatisch eine
  Sterilisationszeit, bevor es wieder einsatzbereit ist.
- `Einmalartikel` erbt ebenfalls davon, hat aber statt einer Zeitplanung
  einen Lagerbestand mit Meldebestand-Warnung.

Für die Zeitplanung gibt es `OPTyp` (das "Rezept" – wie lange dauert eine
Knie-OP normalerweise, was wird dafür gebraucht), `OP` (eine konkret
gebuchte Operation) und `OPSaal` (verwaltet, welche OPs wann in welchem Saal
laufen, inkl. Reinigungszeiten zwischen zwei OPs).

Den Überblick über alles hat der `OPManager`: Er verbindet die Ressourcen
mit der Saal-Zeitplanung, prüft bei jeder Buchung, ob alles verfügbar ist,
und kümmert sich beim Verschieben einer OP darum, dass Folgetermine korrekt
mitgezogen werden.

`main.py` ist mein Testskript für die Konsole, `app.py` die Streamlit-Oberfläche
für die Live-Demo.

### Ablauf einer Buchung (`plane_operation`)

1. OP-Typ ("Rezept") anhand des Namens aus dem Katalog holen
2. Für jede benötigte Ressource prüfen: Einmalartikel → Lagerbestand
   verbrauchen; Personal/Gerät/Instrument → Verfügbarkeit im Zeitraum prüfen
3. Sind alle Ressourcen frei, werden sie blockiert und die OP wird im
   `OPSaal` eingetragen
4. Schlägt irgendein Schritt fehl, werden bereits reservierte Ressourcen
   wieder freigegeben (kein Teil-Zustand bleibt hängen)

### Verschieben einer OP (`verschiebe_op`)

Ändert sich die Dauer einer OP, verschieben sich automatisch alle
nachfolgenden OPs im selben Saal um denselben Betrag (in beide Richtungen:
kürzer = alle rücken vor, länger = alle rücken nach hinten). Vor der
eigentlichen Änderung wird zweifach geprüft:

1. Überschreitet die letzte betroffene OP die Schließzeit des Saals?
2. Sind alle beteiligten Ressourcen zu den neuen Zeiten noch verfügbar?

Nur wenn beide Prüfungen erfolgreich sind, wird die Änderung übernommen –
andernfalls bleibt der komplette ursprüngliche Zustand erhalten.