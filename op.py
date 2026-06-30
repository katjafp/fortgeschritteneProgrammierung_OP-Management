from ressource import Ressource
"""
Modul: op_wesen (op.py

Dieses Modul verwaltet die zeitliche und räumliche Struktur der OP-Planung.
Es enthält die Definitionen für OP-Arten (OPTyp), konkret geplante 
Operationen (OP) sowie die OP-Säle (OPSaal), inklusive Berechnung von 
freien, zusammenhängenden Zeitfenstern unter Berücksichtigung 
der Reinigungszeiten.
"""
class OPTyp:
    """Definiert eine OP-Art mit ihrer Standard-Dauer und den benötigten Ressourcen."""
    def __init__(self, op_name: str, standard_dauer: int, benoetigte_ressourcen: dict[str, int]):
        self.op_name: str = op_name
        self.standard_dauer: int = standard_dauer
        self.benoetigte_ressourcen: dict[str, int] = benoetigte_ressourcen


class OP:
    """Repräsentiert eine konkret geplante Operation auf dem Zeitstrahl."""
    def __init__(self, op_name: str, saal_id: str, start_minute: int, dauer: int):
        self.op_name: str = op_name
        self.saal_id: str = saal_id
        self.start_minute: int = start_minute
        self.end_minute: int = start_minute + dauer
        self.geblockte_ressourcen: list[Ressource] = []


class OPSaal:
    """Verwaltet einen OP-Saal, dessen Auslastung und die zeitliche Reihenfolge."""
    def __init__(self, saal_id: str, kapazitaet_minute: int = 480, reinigung: int = 20):
        self.saal_id: str = saal_id
        self.kapazitaet_minute: int = kapazitaet_minute  # z.B. 480 Minuten (08:00 - 16:00)
        self.geplante_ops: list[OP] = []
        self.reinigung: int = reinigung  # Reinigungszeit nach jeder OP

    

    def berechne_restzeit(self) -> list[dict[str, int]]:
        """
        Analysiert den Zeitstrahl und findet alle Zeitfenster, in dennen 
        neue Operationen geplant werden könnten, unter Berücksichtigung der Reinigungszeit.
        """

        if not self.geplante_ops:
            # Wenn der Saal komplett leer ist, können wir die vollen 480 Minuten nutzen
            return self.kapazitaet_minute

        belegte_zeit = 0
        for op in self.geplante_ops:
            op_dauer = op.end_minute - op.start_minute
            # Jede OP blockiert den Saal für ihre Dauer + die Reinigung danach
            belegte_zeit += (op_dauer + self.reinigung)

        # Die verbleibende reine OP-Zeit ist die Gesamtkapazität minus die belegte Zeit
        restzeit = self.kapazitaet_minute - belegte_zeit
        
        # Da wir nach der allerletzten OP des Tages keine neue OP mehr planen, 
        # steht uns die Reinigungszeit dieser letzten OP eigentlich wieder als Puffer zur Verfügung.
        # Aber um sicherzugehen, dass wir nicht überziehen, ist 'restzeit' der sicherste Wert.
        return max(0, restzeit)

        """Berechnet die Summe aller echt NUTZBAREN Operations-Minuten in den Lücken."""
        fenster = self.finde_freie_zeitfenster()
        # Wir summieren nur die Zeit auf, die man wirklich mit Operieren verbringen kann
        return sum(f["nutzbare_op_zeit"] for f in fenster)

    def op_hinzufuegen(self, neue_op: OP) -> None:
        """Prüft, ob eine neue OP zeitlich exakt in eine der freien Lücken passt."""
        neue_op_dauer_mit_reinigung = (neue_op.end_minute - neue_op.start_minute) + self.reinigung
        
        # überprüft, ob OP in Zeit bis Saal-Ende passt
        if neue_op.end_minute + self.reinigung > self.kapazitaet_minute:
            raise ValueError(f"Fehler: OP überschreitet die Schließzeit von {self.saal_id}!")

        # Überschneidungsprüfung mit bereits geplanten OPs
        for op in self.geplante_ops:
            op_ende_mit_reinigung = op.end_minute + self.reinigung
            if not (neue_op.end_minute + self.reinigung <= op.start_minute or neue_op.start_minute >= op_ende_mit_reinigung):
                raise ValueError(f"Zeitkonflikt in {self.saal_id}: Zeitraum überschneidet sich!")
        
        self.geplante_ops.append(neue_op)
        self.geplante_ops.sort(key=lambda x: x.start_minute)