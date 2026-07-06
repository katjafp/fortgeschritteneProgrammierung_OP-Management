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
    def lager_material_ein(self, name: str, menge: int) -> None:
        """Erhöht den Bestand eines Einmalartikels im Lager, z.B. bei Anlieferung."""
        if name not in self.lager:
            raise ValueError(f"Fehler: Der Artikel '{name}' ist nicht im Lager registriert!")
        
        artikel = self.lager[name]
        artikel.bestand += menge
        print(f"[LAGER] {menge} Stück '{name}' eingelagert. Neuer Bestand: {artikel.bestand}")

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
                if hasattr(ressource, "starte_sterilisation"):
                    ressource.starte_sterilisation(start_minute + dauer)
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
        Passt die Dauer einer OP an (kürzer ODER länger) und verschiebt alle 
        nachfolgenden OPs im selben Saal automatisch mit. 
        
        Vorgehen: Erst wird geprüft, ob die Änderung überhaupt möglich ist 
        (Saalschluss, Ressourcen-Kollisionen). Erst wenn alles passt, wird 
        die Änderung wirklich übernommen. Geht etwas nicht, bleibt der 
        ursprüngliche Zustand komplett erhalten (Exception statt Teil-Änderung).
        """
        if neue_dauer <= 0:
            raise ValueError(f"Fehler: Neue Dauer muss positiv sein (erhalten: {neue_dauer}).")

        if saal_id not in self.saele:
            raise ValueError(f"Fehler: Der OP-Saal '{saal_id}' existiert nicht!")
        saal = self.saele[saal_id]

        op = next((o for o in saal.geplante_ops if o.op_name == op_name), None)
        if op is None:
            raise ValueError(f"Fehler: OP '{op_name}' ist in '{saal_id}' nicht geplant!")

        alte_end_minute = op.end_minute
        neue_end_minute = op.start_minute + neue_dauer
        verschiebung = neue_end_minute - alte_end_minute

        if verschiebung == 0:
            print(f"[HINWEIS] '{op_name}' bleibt unverändert bei {neue_dauer} Minuten.")
            return

        # Alle nachfolgenden OPs im selben Saal werden um denselben Betrag mitverschoben
        folge_ops = [o for o in saal.geplante_ops if o.start_minute >= alte_end_minute]

        # Neue Zeiten für alle betroffenen OPs im Voraus berechnen
        neue_zeiten = [(op, op.start_minute, neue_end_minute)]
        for folge_op in folge_ops:
            neue_zeiten.append((folge_op, folge_op.start_minute + verschiebung, folge_op.end_minute + verschiebung))

        # Prüfung 1: Überschreitet die letzte betroffene OP die Schließzeit des Saals?
        letzte_neue_end_minute = neue_zeiten[-1][2]
        if letzte_neue_end_minute + saal.reinigung > saal.kapazitaet_minute:
            raise ValueError(f"Verschiebung nicht möglich: {saal_id} würde über die Schließzeit hinaus belegt!")

        # Prüfung 2: Sind alle Ressourcen zu den NEUEN Zeiten noch verfügbar?
        # Dazu geben wir die betroffenen Ressourcen testweise frei und prüfen dann.
        for o, _, _ in neue_zeiten:
            for ressource in o.geblockte_ressourcen:
                ressource.freigeben(o.op_name)

        konflikt = None
        for o, neuer_start, neuer_ende in neue_zeiten:
            for ressource in o.geblockte_ressourcen:
                if hasattr(ressource, "pruefe_einsatzzeit"):
                    frei = ressource.pruefe_einsatzzeit(neuer_start)
                else:
                    frei = ressource.ist_verfuegbar(neuer_start, neuer_ende)
                if not frei:
                    konflikt = f"Verschiebung nicht möglich: Ressource für '{o.op_name}' ist zur neuen Zeit ({neuer_start}-{neuer_ende}) belegt!"
                    break
            if konflikt:
                break

        if konflikt:
            # Nichts geht mehr: alte Zeiten der Ressourcen wiederherstellen und abbrechen
            for o, _, _ in neue_zeiten:
                for ressource in o.geblockte_ressourcen:
                    ressource.blockieren(o.op_name, o.start_minute, o.end_minute)
            raise ValueError(konflikt)

        # Alles passt: Änderung endgültig übernehmen
        richtung = "kürzer" if verschiebung < 0 else "länger"
        print(f"\n[ANPASSUNG] '{op_name}' wird um {abs(verschiebung)} Min. {richtung} (neues Ende: {neue_end_minute}).")

        for o, neuer_start, neuer_ende in neue_zeiten:
            o.start_minute = neuer_start
            o.end_minute = neuer_ende
            for ressource in o.geblockte_ressourcen:
                ressource.blockieren(o.op_name, neuer_start, neuer_ende)
                if hasattr(ressource, "starte_sterilisation"):
                    ressource.starte_sterilisation(neuer_ende)
            if o is not op:
                print(f"  -> '{o.op_name}' verschoben auf {neuer_start}-{neuer_ende}")

        saal.geplante_ops.sort(key=lambda x: x.start_minute)
        print(f"Neue Restzeit in {saal_id}: {saal.berechne_restzeit()} Minuten.")

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