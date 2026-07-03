"""
Skript: main (main.py)

Testzentrum für das digitale OP- und Ressourcenmanagement.
Hier wird der Klinikalltag simuliert durch das Anlegen von Test-Ressourcen, OP-Sälen. 
Prüfung des Zusammenspiels der Module um Fehler schnell zu identifizieren und vermeiden.
"""

from manager import OPManager
from ressource import Ressource, Instrument, Einmalartikel
from op import OPTyp


def run_tests():
    print("Starte Kliniksimulation & Systemtests")

    # 1. Manager erstellen
    op_manager = OPManager()

    # 2. OP-Säle registrieren
    op_manager.saal_hinzufuegen(saal_id="Zentral-OP_Saal_1", kapazitaet=480)
    op_manager.saal_hinzufuegen(saal_id="Ambulant_Saal_2", kapazitaet=360)

    # 3. Ressourcen anlegen
    arzt_1 = Ressource(name="Dr. Müller (Anästhesie)")
    roentgen = Ressource(name="Mobiles Röntgengerät C-Bogen")
    op_manager.ressource_registrieren(arzt_1)
    op_manager.ressource_registrieren(roentgen)

    knie_sieb = Instrument(name="Chirurgisches Knie-TEP-Sieb basic")
    op_manager.ressource_registrieren(knie_sieb)

    faeden = Einmalartikel(name="Nahtmaterial Vicryl 3-0", bestand=50, meldebestand=10)
    op_manager.ressource_registrieren(faeden)

    # 4. OP-Typ definieren
    knie_op_rezept = OPTyp(
        op_name="Knie-Endoprothese",
        standard_dauer=90,
        benoetigte_ressourcen={"Nahtmaterial Vicryl 3-0": 3}
    )
    op_manager.op_typ_definieren(knie_op_rezept)

    # 5. Zwei OPs planen (gleicher Typ, unterschiedliche Buchungen)
    op_manager.plane_operation(
        op_name="Knie-OP Fall 1",
        op_typ_name="Knie-Endoprothese",
        saal_id="Zentral-OP_Saal_1",
        start_minute=0
    )

    op_manager.plane_operation(
        op_name="Knie-OP Fall 2",
        op_typ_name="Knie-Endoprothese",
        saal_id="Zentral-OP_Saal_1",
        start_minute=110
    )

    # 6. Restzeit & freie Fenster prüfen
    saal = op_manager.saele["Zentral-OP_Saal_1"]
    print(f"Verbleibende reine OP-Zeit in {saal.saal_id}: {saal.berechne_restzeit()} Minuten.")
    print("Freie Zeitfenster:", saal.finde_freie_fenster())
    print("Nutzbar für 90-Min-OP:", saal.berechne_restzeit(min_dauer=90))

    # 7. Monitoring-Methoden testen
    op_manager.zeige_verfuegbare_ressourcen(minute=0)
    op_manager.zeige_ops_von_bis(start=0, ende=300)
    op_manager.zeige_aktuelle_ops(aktuelle_minute=30)

    # 8. Verschiebung testen (OP wird kürzer)
    op_manager.verschiebe_op("Zentral-OP_Saal_1", "Knie-OP Fall 1", neue_dauer=60)
    op_manager.zeige_ops_von_bis(0, 300)

    print("Systemtest erfolgreich")


if __name__ == "__main__":
    run_tests()