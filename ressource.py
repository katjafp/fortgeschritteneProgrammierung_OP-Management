"""
Modul: ressource (ressource.py)

Hier werden alle physischen Ressourcen der Klinik verwaltet, die für eine OP 
eingeplant, blockiert oder verbraucht werden müssen.
Es nutzt Vererbung, um die Gemeinsamkeiten von Personal/Geräten (Basisklasse), 
chirurgischen Instrumenten (mit Sterilisationsprozess) und Einmalartikeln 
(mit Lager- und Meldebestand) abzubilden.
"""

class Ressource:
    """Basisklasse für alle Entitäten (Personal, Geräte), die für eine OP blockiert werden."""
    def __init__(self, name: str):
        self.name: str = name
        #geplante OPs für Ressource mit Zeitstempel
        self.geplante_ops: list[dict]=[]

    def ist_verfuegbar(self, von_minute: int, bis_minute: int) -> bool:
        """Prüft, ob die Ressource im angeforderten Zeitraum einsatzbereit ist."""
        for op in self.geplante_ops:
            if von_minute < op["bis"] and bis_minute > op["von"]:
                return False
        return True

    def blockieren(self, op_name: str, von_minute: int, bis_minute: int) -> None:
        """Reserviert die Ressource für eine bestimmte Operation."""
        karteikarte = {
            "name": op_name,
            "von": von_minute,
            "bis": bis_minute
        }
        self.geplante_ops.append(karteikarte)

    def freigeben(self, op_name:str) -> None:
        """Macht die Ressource nach der OP wieder für das System verfügbar."""
        self.geplante_ops = [op for op in self.geplante_ops if op["name"] != op_name]


class Instrument(Ressource):
    """Erbt von Ressource. Nach jeder OP braucht das Sieb zusätzlich eine 
    Sterilisationszeit, bevor es für die nächste OP wieder einsatzbereit ist."""
    
    sterilisationsdauer: int = 60  # Minuten Sterilisation nach jeder Nutzung

    def blockieren(self, op_name: str, von_minute: int, bis_minute: int) -> None:
        """Reserviert das Sieb für eine OP - inkl. der anschließenden 
        Sterilisationszeit. Dadurch zeigt ist_verfuegbar() automatisch erst 
        NACH der Sterilisation wieder 'frei' an."""
        super().blockieren(op_name, von_minute, bis_minute + self.sterilisationsdauer)


class Einmalartikel(Ressource):
    """Erbt von Ressource und verwaltet Bestände und Meldebestände für Verbrauchsmaterialien."""
    def __init__(self, name: str, bestand: int, meldebestand: int):
        super().__init__(name)
        self.bestand: int = bestand
        self.meldebestand: int = meldebestand

    def konsumiere(self, menge: int) -> None:
        """Prüft das Lager, reduziert den Bestand und warnt bei Unterschreitung des Meldebestands."""
        if menge <= 0:
            raise ValueError(f"Fehler: Verbrauchsmenge muss positiv sein (erhalten: {menge}).")

        if self.bestand < menge:
            raise ValueError(f"Kritischer Fehler: Nicht genügend Material von '{self.name}' vorhanden!")
        
        self.bestand -= menge
        
        # Automatischer Nachbestell-Trigger
        if self.bestand <= self.meldebestand:
            print(f"Warnung! Meldebestand für '{self.name}' unterschritten! Aktueller Bestand: {self.bestand}")

class RessourcenPool(Ressource):
    """Erbt von Ressource. Bildet mehrere GLEICHARTIGE Einheiten ab (z.B. 3 Operateure
    derselben Fachrichtung), die als eine gemeinsame Ressource verwaltet werden.

    Statt 'frei oder belegt' (wie bei der Basisklasse) wird gezählt, wie viele
    Einheiten zeitgleich schon gebucht sind. Erst wenn alle 'anzahl' Einheiten
    gleichzeitig belegt sind, gilt der Pool als voll."""

    def __init__(self, name: str, anzahl: int):
        super().__init__(name)
        if anzahl <= 0:
            raise ValueError(f"Fehler: Anzahl muss positiv sein (erhalten: {anzahl}).")
        self.anzahl: int = anzahl

    def ist_verfuegbar(self, von_minute: int, bis_minute: int) -> bool:
        """Frei, solange nicht bereits 'anzahl' Buchungen im selben Zeitraum liegen."""
        ueberschneidungen = sum(
            1 for op in self.geplante_ops
            if von_minute < op["bis"] and bis_minute > op["von"]
        )
        return ueberschneidungen < self.anzahl