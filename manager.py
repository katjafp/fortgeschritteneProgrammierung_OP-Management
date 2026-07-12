"""
Modul: manager (manager.py)

Hier ist die Steuerungseinheit für das gesamte digitale OP- & Ressourcenmanagement.
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
        if saal_id in self.saele:
            raise ValueError(f"Fehler: Ein Saal mit der ID '{saal_id}' ist bereits registriert!")
        self.saele[saal_id] = OPSaal(saal_id, kapazitaet)
        print(f"[System] Saal '{saal_id}' erfolgreich mit {kapazitaet} Min. Schichtzeit registriert.")

    def ressource_registrieren(self, ressource: Ressource) -> None:
        """Fügt Personal oder Geräte dem Ressourcen Pool hinzu oder sortiert Einmalartikel ins Lager ein."""
        name = ressource.name
        if name in self.lager or name in self.ressourcen_pool:
            raise ValueError(f"Fehler: Der Name '{name}' ist bereits als Ressource registriert!")
        if isinstance(ressource, Einmalartikel):
            self.lager[name] = ressource
        else:
            self.ressourcen_pool[name] = ressource
            
    def lager_material_ein(self, name: str, menge: int) -> None:
        """Erhöht den Bestand eines Einmalartikels im Lager, z.B. bei Anlieferung."""
        if menge <= 0:
            raise ValueError(f"Fehler: Nachlieferungsmenge muss positiv sein (erhalten: {menge}).")

        if name not in self.lager:
            raise ValueError(f"Fehler: Der Artikel '{name}' ist nicht im Lager registriert!")
        
        artikel = self.lager[name]
        artikel.bestand += menge
        print(f"[Lager] {menge} Stück '{name}' eingelagert. Neuer Bestand: {artikel.bestand}")

    def op_typ_definieren(self, op_typ: OPTyp) -> None:
        """Hinterlegt ein neues OP-Rezept (z.B. Knie-TEP) im System."""
        self.op_typen[op_typ.op_name] = op_typ

    def plane_operation(self, op_name: str, op_typ_name: str, saal_id: str, start_minute: int) -> None:
        """
        Prüft die Verfügbarkeit von Saal und Ressourcen und bucht die OP in den Zeitstrahl ein.

        op_name: eindeutiger Bezeichner der konkreten Buchung (z.B. "Knie-OP Patient Müller")
        op_typ_name: Name des Rezepts im Katalog (z.B. "Knie-Endoprothese")

        Ablauf: Erst wird alles geprüft (Saal, Personal/Geräte, Lagerbestand),
        erst wenn alles passt, wird wirklich etwas verändert.
        """
        print(f"\n[Buchung] Starte Planung für '{op_name}' ({op_typ_name}) in {saal_id} ab Minute {start_minute}")
        #verhindert leere Eingaben & Leerzeichen 
        if not op_name or not op_name.strip():
            raise ValueError("Fehler: Der Name darf nicht leer sein. - Bitte um Eingabe.")
        #verhindert von Doppelbuchungen
        for saal in self.saele.values():
            if any(o.op_name == op_name for o in saal.geplante_ops):
                raise ValueError(f"Fehler: Der Name '{op_name}' ist bereits vergeben. Bitte eindeutigen Namen wählen.")
            
        if not isinstance(start_minute, int) or isinstance(start_minute, bool):
            raise ValueError(f"Fehler: Startminute muss eine ganze Zahl sein (erhalten: {start_minute!r}).")        #verhindert negative Eingaben
        
        if start_minute < 0:
            raise ValueError(f"Fehler: Startminute muss 0 oder positiv sein (erhalten: {start_minute}).")

        if op_typ_name not in self.op_typen:
            raise ValueError(f"Fehler: Der OP-Typ '{op_typ_name}' ist nicht im System definiert!")
        rezept = self.op_typen[op_typ_name]
        dauer = rezept.standard_dauer
        
        #verhindert Eingabe nicht vorhandener Saal
        if saal_id not in self.saele:
            raise ValueError(f"Fehler: Der OP-Saal '{saal_id}' existiert nicht!")
        saal = self.saele[saal_id]

        neue_op = OP(op_name, saal_id, start_minute, dauer)

        # Prüfung - vorhandene Ressourcen 
        for ressourcen_name, benoetigte_menge in rezept.benoetigte_ressourcen.items():
            if not isinstance(benoetigte_menge, int) or isinstance(benoetigte_menge, bool) or benoetigte_menge <= 0:
                raise ValueError(
                    f"Fehler: Benötigte Menge für '{ressourcen_name}' im OP-Typ '{op_typ_name}' muss eine positive ganze Zahl sein (erhalten: {benoetigte_menge})."
                )

            if ressourcen_name in self.lager:
                artikel = self.lager[ressourcen_name]
                if artikel.bestand < benoetigte_menge:
                    raise ValueError(f"Kritischer Fehler: Nicht genügend Material von '{ressourcen_name}' vorhanden!")

            elif ressourcen_name in self.ressourcen_pool:
                ressource = self.ressourcen_pool[ressourcen_name]
                if not ressource.ist_verfuegbar(start_minute, start_minute + dauer):
                    raise ValueError(f"Buchungs-Konflikt: Die Ressource '{ressourcen_name}' ist aktuell belegt!")

            else:
                raise ValueError(f"Fehler: Die geforderte Ressource '{ressourcen_name}' existiert nicht!")

        # Prüft zusätzlich Saal-Zeitfenster und bucht die OP verbindlich in den Saal ein
        saal.op_hinzufuegen(neue_op)
        
        # geprüft + Saal blockiert ->Ressourcen werden blockiert
        verbrauchtes_material: list[tuple[Einmalartikel, int]] = []
        try:
            for ressourcen_name, benoetigte_menge in rezept.benoetigte_ressourcen.items():
                if ressourcen_name in self.lager:
                    self.lager[ressourcen_name].konsumiere(benoetigte_menge)
                    verbrauchtes_material.append((self.lager[ressourcen_name], benoetigte_menge))
                else:
                    ressource = self.ressourcen_pool[ressourcen_name]
                    ressource.blockieren(op_name, start_minute, start_minute + dauer)
                    neue_op.geblockte_ressourcen.append(ressource)
        except Exception:
            # Rollback: Saal-Eintrag entfernen
            saal.geplante_ops.remove(neue_op)
            # Rollback: bereits blockierte Ressourcen wieder freigeben
            for ressource in neue_op.geblockte_ressourcen:
                ressource.freigeben(op_name)
            # Rollback: bereits verbrauchtes Material zurückbuchen
            for artikel, menge in verbrauchtes_material:
                artikel.bestand += menge
            raise

        print(f"'{op_name}' wurde für {saal_id} (Minute {start_minute} bis {start_minute + dauer}) fest gebucht!")
        
    def plane_mehrere_operationen(self, buchungen: list[tuple[str, str, str, int]]) -> list[dict]:
        """
        Bucht mehrere OPs nacheinander über plane_operation(). Ein fehlgeschlagener
        Einzelversuch bricht nicht die gesamte Stapelverarbeitung ab: jede Buchung
        wird unabhängig versucht, das Ergebnis wird gesammelt und zurückgegeben.
        """
        ergebnisse: list[dict] = []
        for op_name, op_typ_name, saal_id, start_minute in buchungen:
            try:
                self.plane_operation(op_name, op_typ_name, saal_id, start_minute=start_minute)
                ergebnisse.append({"op_name": op_name, "erfolgreich": True})
            except ValueError as e:
                ergebnisse.append({"op_name": op_name, "erfolgreich": False, "fehler": str(e)})
        return ergebnisse

    def verschiebe_op(self, saal_id: str, op_name: str, neue_dauer: int) -> None:
        """
        Passt die Dauer einer OP an (kürzer/länger) und verschiebt alle 
        nachfolgenden OPs im selben Saal automatisch mit. 
        
        Erst wird geprüft, ob die Änderung überhaupt möglich ist 
        (Saalschluss, Ressourcen-Kollisionen). Erst wenn alles passt, wird 
        die Änderung wirklich übernommen. Geht etwas nicht, bleibt der 
        ursprüngliche Zustand komplett erhalten.
        """
        if not isinstance(neue_dauer, int):
            raise ValueError(f"Fehler: Neue Dauer muss eine ganze Zahl sein (erhalten: {neue_dauer!r}).")

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
            print(f"[Hinweis] '{op_name}' bleibt unverändert bei {neue_dauer} Minuten.")
            return

        # Alle nachfolgenden OPs im selben Saal werden um denselben Betrag mitverschoben
        folge_ops = [o for o in saal.geplante_ops if o.start_minute >= alte_end_minute]

        # Neue Zeiten für alle betroffenen OPs im Voraus berechnen
        neue_zeiten = [(op, op.start_minute, neue_end_minute)]
        for folge_op in folge_ops:
            neue_zeiten.append((folge_op, folge_op.start_minute + verschiebung, folge_op.end_minute + verschiebung))

        # Prüfung: Überschreitet die letzte betroffene OP die Schließzeit des Saals?
        letzte_neue_end_minute = neue_zeiten[-1][2]
        if letzte_neue_end_minute + saal.reinigung > saal.kapazitaet_minute:
            raise ValueError(f"Verschiebung nicht möglich: {saal_id} würde über die Schließzeit hinaus belegt!")

        # Prüfung: Sind alle Ressourcen zu den neuen Zeiten noch verfügbar?
        for o, _, _ in neue_zeiten:
            for ressource in o.geblockte_ressourcen:
                ressource.freigeben(o.op_name)

        konflikt = None
        for o, neuer_start, neuer_ende in neue_zeiten:
            for ressource in o.geblockte_ressourcen:
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
        print(f"\n[Anpassung] '{op_name}' wird um {abs(verschiebung)} Min. {richtung} (neues Ende: {neue_end_minute}).")

        for o, neuer_start, neuer_ende in neue_zeiten:
            o.start_minute = neuer_start
            o.end_minute = neuer_ende
            for ressource in o.geblockte_ressourcen:
                ressource.blockieren(o.op_name, neuer_start, neuer_ende)
            if o is not op:
                print(f"  -> '{o.op_name}' verschoben auf {neuer_start}-{neuer_ende}")

        saal.geplante_ops.sort(key=lambda x: x.start_minute)
        print(f"Neue Restzeit in {saal_id}: {saal.berechne_restzeit()} Minuten.")

    def zeige_verfuegbare_ressourcen(self, minute: int) -> None:
        """Gibt aus, welches Personal/Geräte/Instrumente zu einer bestimmten Minute frei sind."""
        print(f"\n[Status] Verfügbare Ressourcen zur Minute {minute}:")

        for name, ressource in self.ressourcen_pool.items():
            # 1-Minuten-Fenster reicht, um zu prüfen, ob die Ressource gerade frei ist
            frei = ressource.ist_verfuegbar(minute, minute + 1)
            status = "frei" if frei else "belegt"
            print(f"  - {name}: {status}")
    
    def zeige_ops_von_bis(self, start: int, ende: int) -> None:
        """Zeigt alle geplanten OPs, die (teilweise) im Zeitfenster [start, ende] liegen."""
        print(f"\n[Status] OPs zwischen Minute {start} und {ende}:")
        gefunden = False

        for saal in self.saele.values():
            for op in saal.geplante_ops:
                # Überschneidung: OP beginnt vor Fensterende und endet nach Fensterbeginn
                if op.start_minute < ende and op.end_minute > start:
                    print(f"  - {op.op_name} in {saal.saal_id}: {op.start_minute}-{op.end_minute}")
                    gefunden = True

        if not gefunden:
            print("  Keine OPs in diesem Zeitraum.")
    
    def zeige_aktuelle_ops(self, aktuelle_minute: int) -> None:
        """Zeigt alle OPs, die genau zur angegebenen Minute laufen."""
        self.zeige_ops_von_bis(aktuelle_minute, aktuelle_minute + 1)