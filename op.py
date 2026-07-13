"""
Modul: op_wesen (op.py)

Dieses Modul verwaltet die zeitliche und räumliche Struktur der OP-Planung.
Es enthält die Definitionen für OP-Arten (OPTyp), konkret geplante 
Operationen (OP) sowie die OP-Säle (OPSaal), inklusive Berechnung von 
freien, zusammenhängenden Zeitfenstern unter Berücksichtigung 
der Reinigungszeiten.
"""

from ressource import Ressource

def minute_zu_uhrzeit(minute: int, schichtbeginn: str = "08:00") -> str:
    """Wandelt eine Minute in eine lesbare Uhrzeit um."""
    start_stunde, start_minute_offset = map(int, schichtbeginn.split(":"))
    gesamt_minuten = start_stunde * 60 + start_minute_offset + minute
    stunde = (gesamt_minuten // 60) % 24
    rest_minute = gesamt_minuten % 60
    return f"{stunde:02d}:{rest_minute:02d}"

def uhrzeit_zu_minute(uhrzeit: "datetime.time", schichtbeginn: str = "08:00") -> int:
    """Wandelt eine Uhrzeit (datetime.time) in eine Minute relativ zum Schichtbeginn um."""
    start_stunde, start_minute_offset = map(int, schichtbeginn.split(":"))
    gesamt_minuten_uhrzeit = uhrzeit.hour * 60 + uhrzeit.minute
    gesamt_minuten_schichtbeginn = start_stunde * 60 + start_minute_offset
    return gesamt_minuten_uhrzeit - gesamt_minuten_schichtbeginn

class OP:
    """Repräsentiert eine konkret geplante Operation auf dem Zeitstrahl."""
    def __init__(self, op_name: str, saal_id: str, start_minute: int, dauer: int):
        self.op_name: str = op_name
        self.saal_id: str = saal_id
        self.start_minute: int = start_minute
        self.end_minute: int = start_minute + dauer
        self.geblockte_ressourcen: list[tuple[Ressource, int]] = []

class OPTyp:
    """Definiert eine OP-Art mit ihrer Standard-Dauer und den benötigten Ressourcen."""
    def __init__(self, op_name: str, standard_dauer: int, benoetigte_ressourcen: dict[str, int]):
        if standard_dauer <= 0:
            raise ValueError(f"Fehler: Standard-Dauer muss positiv sein (erhalten: {standard_dauer}).")
        self.op_name: str = op_name
        self.standard_dauer: int = standard_dauer
        self.benoetigte_ressourcen: dict[str, int] = benoetigte_ressourcen

class OPSaal:
    """Verwaltet einen OP-Saal, dessen Auslastung und die zeitliche Reihenfolge."""
    def __init__(self, saal_id: str, kapazitaet_minute: int = 480, reinigung: int = 20):
        if kapazitaet_minute <= 0:
            raise ValueError(f"Fehler: Kapazität muss positiv sein (erhalten: {kapazitaet_minute}).")
        if reinigung < 0:
            raise ValueError(f"Fehler: Reinigungszeit darf nicht negativ sein (erhalten: {reinigung}).")
        self.saal_id: str = saal_id
        self.kapazitaet_minute: int = kapazitaet_minute  # z.B. 480 Minuten (08:00 - 16:00)
        self.geplante_ops: list[OP] = []
        self.reinigung: int = reinigung  # Reinigungszeit nach jeder OP

    def finde_freie_fenster(self) -> list[dict]:
        """Ermittelt alle zusammenhängenden freien Zeitfenster im Saal 
        unter Berücksichtigung der Reinigungszeit nach jeder OP."""
        fenster = []
        cursor = 0  

        for op in self.geplante_ops: 
            if op.start_minute > cursor:
                fenster.append({
                    "von": cursor,
                    "bis": op.start_minute,
                    "dauer": op.start_minute - cursor
                })
            cursor = op.end_minute + self.reinigung

        if cursor < self.kapazitaet_minute:
            fenster.append({
                "von": cursor,
                "bis": self.kapazitaet_minute,
                "dauer": self.kapazitaet_minute - cursor
            })
        return fenster

    def berechne_restzeit(self) -> int:
        """
        Berechnet die verbleibenden freien Minuten im Saal.
        Mit min_dauer werden realistische Zeitfenster identifiziert in die 
        tatsächlich eine OP geplant werden kann.
        """
        fenster = self.finde_freie_fenster()
        return sum(f["dauer"] for f in fenster)

    def op_hinzufuegen(self, neue_op: OP) -> None:
        """Prüft, ob eine neue OP zeitlich exakt in eine der freien Lücken passt."""        
        fenster = self.finde_freie_fenster()
        passt = any(
            f["von"] <= neue_op.start_minute and neue_op.end_minute + self.reinigung <= f["bis"]
            for f in fenster
        )
        if not passt:
            raise ValueError(f"Zeitkonflikt in {self.saal_id}: OP passt in keine freie Lücke!")

        self.geplante_ops.append(neue_op)
        self.geplante_ops.sort(key=lambda x: x.start_minute)