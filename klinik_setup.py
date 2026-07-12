"""
Modul: klinik_setup (klinik_setup.py)

Baut eine Beispiel-Klinik für ORTHOPÄDISCHE Operationen auf: 3 OP-Säle,
mehrere Operateure, Anästhesisten, OP-Pflegekräfte, Geräte, chirurgische
Siebe, Verbrauchsmaterial und die dazugehörigen OP-Typen.
"""

from manager import OPManager
from ressource import Ressource, Instrument, Einmalartikel, RessourcenPool
from op import OPTyp


def baue_orthopaedie_klinik() -> OPManager:
    """Erstellt einen fertig befüllten OPManager für eine orthopädische Klinik.

    Aufbau:
      - Saal_1_Endoprothetik: Operateur Endoprothetik + Team, Knie-/Hüft-TEP
      - Saal_2_Wirbelsaeule:  Operateur Wirbelsäule + Team, Spondylodese
      - Saal_3_Ambulant:      Operateur Schulter/Fuß + Team, Schulter-/Sprunggelenk-OPs
    """
    manager = OPManager()

    # OP-Säle
    manager.saal_hinzufuegen("Saal_1_Endoprothetik", kapazitaet=480)  # 08:00-16:00
    manager.saal_hinzufuegen("Saal_2_Wirbelsaeule", kapazitaet=480)   # 08:00-16:00
    manager.saal_hinzufuegen("Saal_3_Ambulant", kapazitaet=360)       # 08:00-14:00

    # Personal: reine Funktionsbezeichnung
    personal = {
        "Operateur Endoprothetik": 3,
        "Operateur Wirbelsäule": 2,
        "Operateur Schulter/Fuß": 2,
        "Anästhesist": 5,
        "OP-Pflege": 7
    }
    for name, anzahl in personal.items():
        if anzahl == 1:
            manager.ressource_registrieren(Ressource(name=name))
        else:
            manager.ressource_registrieren(RessourcenPool(name=name, anzahl=anzahl))


    # Geräte
    manager.ressource_registrieren(RessourcenPool(name="C-Bogen", anzahl=2))
    geraete = ["C-Bogen", "Navigationssystem", "Arthroskopie-Turm"]
    for name in geraete:
        manager.ressource_registrieren(Ressource(name=name))
    
    # Chirurgische Siebe (Instrument = Ressource + Sterilisationszeit)
    siebe = ["Knie-TEP-Sieb", "Hüft-TEP-Sieb", "Wirbelsäulen-Sieb",
             "Schulter-Arthroskopie-Sieb", "Sprunggelenk-Sieb"]
    for name in siebe:
        manager.ressource_registrieren(Instrument(name=name))

    # Einmalartikel / Verbrauchsmaterial (mit Lager & Meldebestand)
    manager.ressource_registrieren(Einmalartikel(name="Knochenzement Palacos", bestand=20, meldebestand=5))
    manager.ressource_registrieren(Einmalartikel(name="Nahtmaterial Vicryl 3-0", bestand=50, meldebestand=10))
    manager.ressource_registrieren(Einmalartikel(name="Schrauben-Set Wirbelsäule", bestand=6, meldebestand=2))
    manager.ressource_registrieren(Einmalartikel(name="Fadenanker Schulter", bestand=15, meldebestand=4))

    # OP-Typen ("Rezepte": Dauer + benötigte Ressourcen)
    manager.op_typ_definieren(OPTyp(
        op_name="Knie-TEP",
        standard_dauer=120,
        benoetigte_ressourcen={
            "Operateur Endoprothetik": 1,
            "Anästhesist": 1,
            "OP-Pflege": 2,
            "C-Bogen": 1,
            "Knie-TEP-Sieb": 1,
            "Knochenzement Palacos": 2,
            "Nahtmaterial Vicryl 3-0": 4,
        }
    ))
    manager.op_typ_definieren(OPTyp(
        op_name="Hüft-TEP",
        standard_dauer=100,
        benoetigte_ressourcen={
            "Operateur Endoprothetik": 1,
            "Anästhesist": 1,
            "OP-Pflege": 1,
            "C-Bogen": 1,
            "Hüft-TEP-Sieb": 1,
            "Knochenzement Palacos": 2,
            "Nahtmaterial Vicryl 3-0": 4,
        }
    ))
    manager.op_typ_definieren(OPTyp(
        op_name="Wirbelsaeulen-Spondylodese",
        standard_dauer=180,
        benoetigte_ressourcen={
            "Operateur Wirbelsäule": 1,
            "Anästhesist": 1,
            "OP-Pflege": 1,
            "Navigationssystem": 1,
            "Wirbelsäulen-Sieb": 1,
            "Schrauben-Set Wirbelsäule": 1,
            "Nahtmaterial Vicryl 3-0": 5,
        }
    ))
    manager.op_typ_definieren(OPTyp(
        op_name="Schulter-Arthroskopie",
        standard_dauer=60,
        benoetigte_ressourcen={
            "Operateur Schulter/Fuß": 1,
            "Anästhesist": 1,
            "OP-Pflege": 1,
            "Arthroskopie-Turm": 1,
            "Schulter-Arthroskopie-Sieb": 1,
            "Fadenanker Schulter": 2,
            "Nahtmaterial Vicryl 3-0": 2,
        }
    ))
    manager.op_typ_definieren(OPTyp(
        op_name="Sprunggelenk-Arthrodese",
        standard_dauer=90,
        benoetigte_ressourcen={
            "Operateur Schulter/Fuß": 1,
            "Anästhesist": 1,
            "OP-Pflege": 1,
            "C-Bogen": 1,
            "Sprunggelenk-Sieb": 1,
            "Nahtmaterial Vicryl 3-0": 3,
        }
    ))

    return manager