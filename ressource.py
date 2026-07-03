"""
Modul: ressource (ressource.py)

Hier werden alle physischen Ressourcen der Klinik verwaltet, die für eine OP 
eingeplant, blockiert oder verbraucht werden müssen.
Es nutzt Vererbung, um die Gemeinsamkeiten von Personal/Geräten (Basisklasse), 
chirurgischen Instrumenten (mit Sterilisationsprozess) und Einmalartikeln 
(mit Lager- und Meldebestand) abzubilden.
"""

from unicodedata import name


class Ressource:
    """Basisklasse für alle Entitäten (Personal, Geräte), die für eine OP blockiert werden."""
    def __init__(self, name: str):
        self.name: str = name
        #geplante OPs für Ressource mit Zeitstempel
        self.geplante_ops: list[dict]=[]

    def ist_verfuegbar(self, von_minute: int, bis_minute: int) -> bool:
        """Prüft, ob die Ressource im angeforderten Zeitraum einsatzbereit ist."""
        #wir gehen alle OPs durch die schon im k
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
    """Erbt von Ressource und fügt die Logik des Sterilisationsprozesses hinzu."""
    def __init__(self, name: str):
        super().__init__(name)
        self.steri_bis_minute: int = 0
        self.verfuegbar: bool = True 

    def starte_sterilisation(self, end_minute_op: int) -> None:
        """Setzt den Status auf nicht verfügbar, bis der Steri-Prozess beendet ist."""
        self.verfuegbar = False
        # Einheitliche Sterilisationszeit: 60 Minuten
        self.steri_bis_minute = end_minute_op + 60

    def pruefe_einsatzzeit(self, ziel_minute: int) -> bool:
        """Prüft, ob das chirurgische Sieb zum Zielzeitpunkt wieder steril und einsatzbereit ist."""
        if ziel_minute < self.steri_bis_minute:
            return False
        return self.verfuegbar


class Einmalartikel(Ressource):
    """Erbt von Ressource und verwaltet Bestände und Meldebestände für Verbrauchsmaterialien."""
    def __init__(self, name: str, bestand: int, meldebestand: int):
        super().__init__(name)
        self.bestand: int = bestand
        self.meldebestand: int = meldebestand

    def konsumiere(self, menge: int) -> None:
        """Prüft das Lager, reduziert den Bestand und warnt bei Unterschreitung des Meldebestands."""
        if self.bestand < menge:
            raise ValueError(f"Kritischer Fehler: Nicht genügend Material von '{self.name}' vorhanden!")
        
        self.bestand -= menge
        
        # Automatischer Nachbestell-Trigger
        if self.bestand <= self.meldebestand:
            print(f"[WARNUNG] Meldebestand für '{self.name}' unterschritten! Aktueller Bestand: {self.bestand}")