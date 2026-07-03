"""
Modul: manager (manager.py)

Hier ist die zentrale Steuerungseinheit für das gesamte digitale OP- und Ressourcenmanagement.
OPManager verknüpft die Ressourcen (ressource.py) mit der Raum- & Zeitplanung (op.py).
Gleichzeitig werden Ressourcen-Pools verwaltet. 
Ebenfalls ist eine Zeitverschiebung der Operationen möglich. 
"""

from ressource import Ressource, Einmalartikel
from op import OPSaal, OP, OPTyp

class OPManager:
    """Die oberste Steuereinheit für das gesamte digitale OP- und Ressourcenmanagement."""
    def __init__(self):
        self.saele: dict[str, OPSaal] = {}              # Raumplanung: {saal_id: OPSaal-Objekt}
        self.ressourcen_pool: dict[str, Ressource] = {}  # Personal und Geräte: {name: Ressource-Objekt}
        self.lager: dict[str, Einmalartikel] = {}       # Materialwirtschaft: {name: Einmalartikel-Objekt}
        self.op_typen: dict[str, OPTyp] = {}            # Die "Rezepte" für OPs: {op_name: OPTyp-Objekt}

    def saal_hinzufuegen(self, saal_id: str, kapazitaet: int = 480) -> None:
        """Registriert einen neuen OP-Saal im System."""
        self.saele[saal_id] = OPSaal(saal_id, kapazitaet)
        print(f"[SYSTEM] Saal '{saal_id}' erfolgreich mit {kapazitaet} Min. Schichtzeit registriert.")

    def ressource_registrieren(self, ressource: Ressource) -> None:
        """Fügt Personal oder Geräte dem Ressourcen Pool hinzu oder sortiert Einmalartikel ins Lager ein."""
        if isinstance(ressource, Einmalartikel):
            self.lager[ressource.name] = ressource
        else:
            self.ressourcen_pool[ressource.name] = ressource

    def op_typ_definieren(self, op_typ: OPTyp) -> None:
        """Hinterlegt ein neues OP-Rezept (z.B. Knie-TEP) im System."""
        self.op_typen[op_typ.op_name] = op_typ

    def plane_operation(self, op_name: str, op_typ_name: str, saal_id: str, start_minute: int) -> None:
        """
        Prüft die Verfügbarkeit von Saal und Ressourcen und bucht die OP in den Zeitstrahl ein.

        op_name: eindeutiger Bezeichner DIESER konkreten Buchung (z.B. "Knie-OP Patient Müller")
        op_typ_name: Name des Rezepts im Katalog (z.B. "Knie-Endoprothese")
        """
        print(f"\n[BUCHUNG] Starte Planung für '{op_name}' ({op_typ_name}) in {saal_id} ab Minute {start_minute}")

        # OP-Rezept anhand des TYP-Namens holen
        if op_typ_name not in self.op_typen:
            raise ValueError(f"Fehler: Der OP-Typ '{op_typ_name}' ist nicht im System definiert!")
        rezept = self.op_typen[op_typ_name]
        dauer = rezept.standard_dauer

        if saal_id not in self.saele:
            raise ValueError(f"Fehler: Der OP-Saal '{saal_id}' existiert nicht!")
        saal = self.saele[saal_id]

        # Neue OP-Instanz anlegen — sie bekommt den eindeutigen Buchungs-Namen
        neue_op = OP(op_name, saal_id, start_minute, dauer)

        temporaer_geblockt = []

        for ressourcen_name, benoetigte_menge in rezept.benoetigte_ressourcen.items():
            if ressourcen_name in self.lager:
                artikel = self.lager[ressourcen_name]
                artikel.konsumiere(benoetigte_menge)

            elif ressourcen_name in self.ressourcen_pool:
                ressource = self.ressourcen_pool[ressourcen_name]

                if hasattr(ressource, "pruefe_einsatzzeit"):
                    ist_frei = ressource.pruefe_einsatzzeit(start_minute)
                else:
                    ist_frei = ressource.ist_verfuegbar(start_minute, start_minute + dauer)

                if not ist_frei:
                    for r in temporaer_geblockt:
                        r.freigeben(op_name)
                    raise ValueError(f"Buchungs-Konflikt: Die Ressource '{ressourcen_name}' ist aktuell belegt!")

                ressource.blockieren(op_name, start_minute, start_minute + dauer)
                temporaer_geblockt.append(ressource)
                neue_op.geblockte_ressourcen.append(ressource)

            else:
                raise ValueError(f"Fehler: Die geforderte Ressource '{ressourcen_name}' existiert nicht!")

        try:
            saal.op_hinzufuegen(neue_op)
            print(f"'{op_name}' wurde für {saal_id} (Minute {start_minute} bis {start_minute + dauer}) fest gebucht!")
        except ValueError as e:
            for r in temporaer_geblockt:
                r.freigeben(op_name)
            raise e

    def verschiebe_op(self, saal_id: str, op_name: str, neue_dauer: int) -> None:
        """
        Passt die Dauer einer OP an (aktuell: nur Verkürzung) und rückt alle 
        nachfolgenden OPs im selben Saal automatisch um die gewonnene Zeit vor.
        """
        if saal_id not in self.saele:
            raise ValueError(f"Fehler: Der OP-Saal '{saal_id}' existiert nicht!")
        saal = self.saele[saal_id]

        # 1. Die betroffene OP finden
        op = next((o for o in saal.geplante_ops if o.op_name == op_name), None)
        if op is None:
            raise ValueError(f"Fehler: OP '{op_name}' ist in '{saal_id}' nicht geplant!")

        alte_end_minute = op.end_minute
        neue_end_minute = op.start_minute + neue_dauer
        verschiebung = neue_end_minute - alte_end_minute  # negativ = Zeitgewinn

        if verschiebung >= 0:
            raise NotImplementedError("Verlängerung wird im nächsten Schritt ergänzt.")

        print(f"\n[ANPASSUNG] '{op_name}' wird um {abs(verschiebung)} Min. kürzer (neues Ende: {neue_end_minute}).")

        # 2. Die OP selbst aktualisieren
        op.end_minute = neue_end_minute
        self._aktualisiere_ressourcen_zeitfenster(op)

        # 3. Alle nachfolgenden OPs im Saal nach vorne rücken
        for folge_op in saal.geplante_ops:
            if folge_op.start_minute >= alte_end_minute:
                folge_op.start_minute += verschiebung
                folge_op.end_minute += verschiebung
                self._aktualisiere_ressourcen_zeitfenster(folge_op)
                print(f"  -> '{folge_op.op_name}' verschoben auf {folge_op.start_minute}-{folge_op.end_minute}")

        saal.geplante_ops.sort(key=lambda o: o.start_minute)
        print(f"Neue Restzeit in {saal_id}: {saal.berechne_restzeit()} Minuten.")


    def _aktualisiere_ressourcen_zeitfenster(self, op: OP) -> None:
        """Hilfsmethode: Aktualisiert für eine OP den Kalender-Eintrag jeder geblockten 
        Ressource auf die (neue) Start-/Endzeit der OP."""
        for ressource in op.geblockte_ressourcen:
            ressource.freigeben(op.op_name)
            ressource.blockieren(op.op_name, op.start_minute, op.end_minute)
            if hasattr(ressource, "starte_sterilisation"):
                ressource.starte_sterilisation(op.end_minute)

    def zeige_verfuegbare_ressourcen(self, minute: int) -> None:
        """Gibt aus, welches Personal/Geräte/Instrumente zu einer bestimmten Minute frei sind."""
        print(f"\n[STATUS] Verfügbare Ressourcen zur Minute {minute}:")

        for name, ressource in self.ressourcen_pool.items():
            # Instrumente haben eine eigene Prüfmethode (wegen Sterilisation)
            if hasattr(ressource, "pruefe_einsatzzeit"):
                frei = ressource.pruefe_einsatzzeit(minute)
            else:
                # Für "normale" Ressourcen (Arzt, Gerät) reicht ein 1-Minuten-Fenster
                frei = ressource.ist_verfuegbar(minute, minute + 1)

            status = "frei" if frei else "belegt"
            print(f"  - {name}: {status}")
    
    def zeige_ops_von_bis(self, start: int, ende: int) -> None:
        """Zeigt alle geplanten OPs, die (teilweise) im Zeitfenster [start, ende] liegen."""
        print(f"\n[STATUS] OPs zwischen Minute {start} und {ende}:")
        gefunden = False

        for saal in self.saele.values():
            for op in saal.geplante_ops:
                # Überschneidung: OP beginnt vor Fensterende UND endet nach Fensterbeginn
                if op.start_minute < ende and op.end_minute > start:
                    print(f"  - {op.op_name} in {saal.saal_id}: {op.start_minute}-{op.end_minute}")
                    gefunden = True

        if not gefunden:
            print("  Keine OPs in diesem Zeitraum.")
    
    def zeige_aktuelle_ops(self, aktuelle_minute: int) -> None:
        """Zeigt alle OPs, die genau zur angegebenen Minute laufen."""
        self.zeige_ops_von_bis(aktuelle_minute, aktuelle_minute + 1)