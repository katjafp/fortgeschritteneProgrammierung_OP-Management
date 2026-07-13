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
        self.saele: dict[str, OPSaal] = {}              
        self.ressourcen_pool: dict[str, Ressource] = {}  
        self.lager: dict[str, Einmalartikel] = {}       
        self.op_typen: dict[str, OPTyp] = {}            

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
        if isinstance(ressource, Einmalartikel): #prüft ob Ressource einem Einmalartikel entspricht
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
        if op_typ.op_name in self.op_typen:
            raise ValueError(f"Fehler: Ein OP-Typ mit dem Namen '{op_typ.op_name}' ist bereits definiert!")
        self.op_typen[op_typ.op_name] = op_typ


    #Planung einer Operation
    def plane_operation(self, op_name: str, op_typ_name: str, saal_id: str, start_minute: int) -> None:
        """
        Prüft die Verfügbarkeit von Saal und Ressourcen und bucht die OP in den Zeitstrahl ein.

        op_name: eindeutiger Bezeichner der konkreten Buchung (z.B. "Knie-OP Patient Müller")
        op_typ_name: Name des Rezepts im Katalog (z.B. "Knie-Endoprothese")

        Ablauf: Erst wird alles geprüft (Saal, Personal/Geräte, Lagerbestand),
        erst wenn alles passt, wird wirklich etwas verändert.
        """
        print(f"\n[Buchung] Starte Planung für '{op_name}' ({op_typ_name}) in {saal_id} ab Minute {start_minute}")

        self._validiere_buchungseingaben(op_name, start_minute)
        rezept = self._hole_rezept(op_typ_name)
        saal = self._hole_saal(saal_id)
        dauer = rezept.standard_dauer
        neue_op = OP(op_name, saal_id, start_minute, dauer)

        self._pruefe_ressourcen_verfuegbarkeit(rezept, start_minute, dauer)
        self._buche_saal_und_ressourcen(saal, neue_op, rezept, start_minute, dauer, op_name)

        print(f"'{op_name}' wurde für {saal_id} (Minute {start_minute} bis {start_minute + dauer}) fest gebucht!")
    #1
    def _validiere_buchungseingaben(self, op_name: str, start_minute: int) -> None:
        if not op_name or not op_name.strip():
            raise ValueError("Fehler: Der Name darf nicht leer sein. - Bitte um Eingabe.")

        for saal in self.saele.values():
            if any(o.op_name == op_name for o in saal.geplante_ops):
                raise ValueError(f"Fehler: Der Name '{op_name}' ist bereits vergeben. Bitte eindeutigen Namen wählen.")

        if not isinstance(start_minute, int) or isinstance(start_minute, bool):
            raise ValueError(f"Fehler: Startminute muss eine ganze Zahl sein (erhalten: {start_minute!r}).")

        if start_minute < 0:
            raise ValueError(f"Fehler: Startminute muss 0 oder positiv sein (erhalten: {start_minute}).")
    #2
    def _hole_rezept(self, op_typ_name: str) -> OPTyp:
        if op_typ_name not in self.op_typen:
            raise ValueError(f"Fehler: Der OP-Typ '{op_typ_name}' ist nicht im System definiert!")
        return self.op_typen[op_typ_name]
    #3
    def _hole_saal(self, saal_id: str) -> OPSaal:
        if saal_id not in self.saele:
            raise ValueError(f"Fehler: Der OP-Saal '{saal_id}' existiert nicht!")
        return self.saele[saal_id]
    #4
    def _pruefe_ressourcen_verfuegbarkeit(self, rezept: OPTyp, start_minute: int, dauer: int) -> None:
        for ressourcen_name, benoetigte_menge in rezept.benoetigte_ressourcen.items():
            if not isinstance(benoetigte_menge, int) or isinstance(benoetigte_menge, bool) or benoetigte_menge <= 0:
                raise ValueError(
                    f"Fehler: Benötigte Menge für '{ressourcen_name}' im OP-Typ '{rezept.op_name}' muss eine positive ganze Zahl sein (erhalten: {benoetigte_menge})."
                )

            if ressourcen_name in self.lager:
                artikel = self.lager[ressourcen_name]
                if artikel.bestand < benoetigte_menge:
                    raise ValueError(f"Nicht genügend Material von '{ressourcen_name}' vorhanden!")

            elif ressourcen_name in self.ressourcen_pool:
                ressource = self.ressourcen_pool[ressourcen_name]
                if not ressource.ist_verfuegbar(start_minute, start_minute + dauer, benoetigte_menge):
                    raise ValueError(f"Die Ressource '{ressourcen_name}' ist aktuell belegt!")
            else:
                raise ValueError(f"Die geforderte Ressource '{ressourcen_name}' existiert nicht!")
    #5
    def _buche_saal_und_ressourcen(self, saal: OPSaal, neue_op: OP, rezept: OPTyp, start_minute: int, dauer: int, op_name: str) -> None:
        """Trägt die OP verbindlich ein. Bei jedem Fehler wird alles vollständig zurückgerollt."""
        saal.op_hinzufuegen(neue_op) 
        verbrauchtes_material: list[tuple[Einmalartikel, int]] = []
        try:
            for ressourcen_name, benoetigte_menge in rezept.benoetigte_ressourcen.items():
                if ressourcen_name in self.lager:
                    self.lager[ressourcen_name].konsumiere(benoetigte_menge)
                    verbrauchtes_material.append((self.lager[ressourcen_name], benoetigte_menge))
                else:
                    ressource = self.ressourcen_pool[ressourcen_name]
                    ressource.blockieren(op_name, start_minute, start_minute + dauer, benoetigte_menge)
                    neue_op.geblockte_ressourcen.append((ressource, benoetigte_menge))
        except Exception:
            saal.geplante_ops.remove(neue_op)
            for ressource, menge in neue_op.geblockte_ressourcen:
                ressource.freigeben(op_name)
            for artikel, menge in verbrauchtes_material:
                artikel.bestand += menge
            raise

    #OP verschieben        
    def verschiebe_op(self, saal_id: str, op_name: str, neue_dauer: int) -> None:
        """
        Passt die Dauer einer OP an (kürzer/länger) und verschiebt alle 
        nachfolgenden OPs im selben Saal automatisch mit. 
        
        Erst wird geprüft, ob die Änderung überhaupt möglich ist 
        (Saalschluss, Ressourcen-Kollisionen). Erst wenn alles passt, wird 
        die Änderung wirklich übernommen. Geht etwas nicht, bleibt der 
        ursprüngliche Zustand komplett erhalten.
        """
        self._validiere_verschiebung_eingaben(neue_dauer)
        saal = self._hole_saal(saal_id)
        op = self._finde_op_in_saal(saal, op_name)

        ergebnis = self._berechne_verschiebung(op, saal, neue_dauer)
        if ergebnis is None:
            print(f"[Hinweis] '{op_name}' bleibt unverändert bei {neue_dauer} Minuten.")
            return
        verschiebung, neue_zeiten, neue_end_minute = ergebnis

        self._pruefe_saal_schliesszeit(saal, neue_zeiten)
        self._pruefe_und_reserviere_ressourcen(neue_zeiten)
        self._uebernehme_neue_zeiten(saal, op, neue_zeiten, verschiebung, neue_end_minute, op_name)

    #1
    def _validiere_verschiebung_eingaben(self, neue_dauer: int) -> None:
        if not isinstance(neue_dauer, int):
            raise ValueError(f"Fehler: Neue Dauer muss eine ganze Zahl sein (erhalten: {neue_dauer!r}).")
        if neue_dauer <= 0:
            raise ValueError(f"Fehler: Neue Dauer muss positiv sein (erhalten: {neue_dauer}).")
    #2
    def _finde_op_in_saal(self, saal: OPSaal, op_name: str) -> OP:
        op = next((o for o in saal.geplante_ops if o.op_name == op_name), None)
        if op is None:
            raise ValueError(f"Fehler: OP '{op_name}' ist in '{saal.saal_id}' nicht geplant!")
        return op
    #3
    def _berechne_verschiebung(self, op: OP, saal: OPSaal, neue_dauer: int):
        """Berechnet die neuen Zeiten für die OP + alle Folge-OPs. 
        Gibt None zurück, falls sich effektiv nichts ändert."""
        alte_end_minute = op.end_minute
        neue_end_minute = op.start_minute + neue_dauer
        verschiebung = neue_end_minute - alte_end_minute

        if verschiebung == 0: #keine Verschiebung
            return None

        folge_ops = [o for o in saal.geplante_ops if o.start_minute >= alte_end_minute]
        neue_zeiten = [(op, op.start_minute, neue_end_minute)]
        for folge_op in folge_ops:
            neue_zeiten.append((folge_op, folge_op.start_minute + verschiebung, folge_op.end_minute + verschiebung))

        return verschiebung, neue_zeiten, neue_end_minute
    #4
    def _pruefe_saal_schliesszeit(self, saal: OPSaal, neue_zeiten: list) -> None:
        letzte_neue_end_minute = neue_zeiten[-1][2] #letztes Element, 3.Element (Ende)
        if letzte_neue_end_minute + saal.reinigung > saal.kapazitaet_minute:
            raise ValueError(f"Verschiebung nicht möglich: {saal.saal_id} würde über die Schließzeit hinaus belegt!")
    #5
    def _pruefe_und_reserviere_ressourcen(self, neue_zeiten: list) -> None:
        """Testet, ob alle Ressourcen zu den neuen Zeiten verfügbar wären.
        Gibt zuerst alle alten Buchungen frei (damit die OP sich nicht selbst blockiert),
        prüft dann – und rollt bei Konflikt die alten Zeiten wieder zurück."""
        for o, _, _ in neue_zeiten:
            for ressource, menge in o.geblockte_ressourcen:
                ressource.freigeben(o.op_name)

        konflikt = None
        for o, neuer_start, neuer_ende in neue_zeiten: #über OPs
            for ressource, menge in o.geblockte_ressourcen:  #Ressourcen der OP
                if not ressource.ist_verfuegbar(neuer_start, neuer_ende, menge):
                    konflikt = f"Verschiebung nicht möglich: Ressource für '{o.op_name}' ist zur neuen Zeit ({neuer_start}-{neuer_ende}) belegt!"
                    break
            if konflikt:
                break

        if konflikt: #buchen der Ressourcen zu alten Zeiten - Verschiebung nicht möglich 
            for o, _, _ in neue_zeiten:
                for ressource, menge in o.geblockte_ressourcen:
                    ressource.blockieren(o.op_name, o.start_minute, o.end_minute, menge)
            raise ValueError(konflikt)
    #6
    def _uebernehme_neue_zeiten(self, saal: OPSaal, op: OP, neue_zeiten: list, verschiebung: int, neue_end_minute: int, op_name: str) -> None:
        if verschiebung < 0:
            richtung = "kürzer"
        else:
            richtung = "länger"
        print(f"\n[Anpassung] '{op_name}' wird um {abs(verschiebung)} Min. {richtung} (neues Ende: {neue_end_minute}).")

        for o, neuer_start, neuer_ende in neue_zeiten:
            o.start_minute = neuer_start
            o.end_minute = neuer_ende
            for ressource, menge in o.geblockte_ressourcen:
                ressource.blockieren(o.op_name, neuer_start, neuer_ende, menge)
            if o is not op: #Verschiebung anschließender Operationen
                print(f"  -> '{o.op_name}' verschoben auf {neuer_start}-{neuer_ende}")

        saal.geplante_ops.sort(key=lambda x: x.start_minute)
        print(f"Neue Restzeit in {saal.saal_id}: {saal.berechne_restzeit()} Minuten.")
   

    def zeige_verfuegbare_ressourcen(self, minute: int) -> None:
        """Gibt aus, welches Personal/Geräte/Instrumente zu einer bestimmten Minute frei sind."""
        print(f"\n[Status] Verfügbare Ressourcen zur Minute {minute}:")

        for name, ressource in self.ressourcen_pool.items():
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