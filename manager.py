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

    def plane_operation(self, op_name: str, saal_id: str, start_minute: int) -> None:
        """
        Prüft die Verfügbarkeit von Saal und Ressourcen und bucht die OP in den Zeitstrahl ein, wenn
        alle Ressouircen verfügbar sind.
        
        Kernprozess:
        1. Holt das Rezept (OPTyp).
        2. Prüft zeitliche Verfügbarkeit im Saal (über berechne_restzeit / op_hinzufuegen).
        3. Prüft und verbraucht/blockiert Personal, Instrumente und Material.
        4. Trägt die OP final im Saal ein.
        """
        print(f"\n[BUCHUNG] Starte Planung für OP '{op_name}' in {saal_id} ab Minute {start_minute}")

        # OP Rezept holen (OPTyp)
        if op_name not in self.op_typen:
            raise ValueError(f"Fehler: Der OP-Typ '{op_name}' ist nicht im System definiert!")
        rezept = self.op_typen[op_name]
        dauer = rezept.standard_dauer

        # prüfen ob Saal existiert
        if saal_id not in self.saele:
            raise ValueError(f"Fehler: Der OP-Saal '{saal_id}' existiert nicht!")
        saal = self.saele[saal_id]

        # Neue OP-Instanz anlegen
        neue_op = OP(op_name, saal_id, start_minute, dauer)

        # Ressourcen-Verfügbarkeit prüfen & blockieren
        temporaer_geblockt = []
        
        # definierte benötigte Ressourcen durchgehen 
        for ressourcen_name, benoetigte_menge in rezept.benoetigte_ressourcen.items():
            
            # Fall A: Einmalartikel (Material aus dem Lager)
            if ressourcen_name in self.lager:
                artikel = self.lager[ressourcen_name]
                # Material abziehen (wirft automatisch einen Fehler, falls Lager leer)
                artikel.konsumiere(benoetigte_menge)
            
            # Fall B: Ressource (Arzt, Gerät, Instrumenten-Sieb)
            elif ressourcen_name in self.ressourcen_pool:
                ressource = self.ressourcen_pool[ressourcen_name]
                
                # Prüfen, ob Ressource zu dieser Minute frei ist
                if hasattr(ressource, "pruefe_einsatzzeit"):
                    ist_frei = ressource.pruefe_einsatzzeit(start_minute)
                else:
                    ist_frei = ressource.ist_verfuegbar(start_minute, start_minute + dauer)

                if not ist_frei:
                    # falls etwas belegt ist
                    for r in temporaer_geblockt:
                        r.freigeben()
                    raise ValueError(f"Buchungs-Konflikt: Die Ressource '{ressourcen_name}' ist aktuell belegt!")
                
                # Wenn frei, temporär blockieren
                ressource.blockieren(op_name)
                temporaer_geblockt.append(ressource)
                neue_op.geblockte_ressourcen.append(ressource)
            
            else:
                raise ValueError(f"Fehler: Die geforderte Ressource '{ressourcen_name}' existiert nicht!")

        # Zeitfenster im Saal prüfen und OP final eintragen
        try:
            saal.op_hinzufuegen(neue_op)
            print(f"OP '{op_name}' wurde für {saal_id} (Minute {start_minute} bis {start_minute + dauer}) fest gebucht!")
        except ValueError as e:
            # Falls  Saal voll ist, Ressourcen wieder freigeben!
            for r in temporaer_geblockt:
                r.freigeben()
            raise e


        pass

    def verschiebe_op(self, saal_id: str, op_name: str, verschiebung_minuten: int) -> None:
        """
        dynamische Zeitverschiebung:
        Verschiebt eine OP bei Verspätungen und passt alle nachfolgenden OPs 
        im selben Saal automatisch an.
        """
        # Grundgerüst für den späteren Verschiebungs-Algorithmus
        pass