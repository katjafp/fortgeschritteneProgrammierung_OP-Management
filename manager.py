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
        Kernprozess:
        1. Holt das Rezept (OPTyp).
        2. Prüft zeitliche Verfügbarkeit im Saal (über berechne_restzeit / op_hinzufuegen).
        3. Prüft und verbraucht/blockiert Personal, Instrumente und Material.
        4. Trägt die OP final im Saal ein.
        """

        pass

    def verschiebe_op(self, saal_id: str, op_name: str, verschiebung_minuten: int) -> None:
        """
        dynamische Zeitverschiebung:
        Verschiebt eine OP bei Verspätungen und passt alle nachfolgenden OPs 
        im selben Saal automatisch an.
        """
        # Grundgerüst für den späteren Verschiebungs-Algorithmus
        pass