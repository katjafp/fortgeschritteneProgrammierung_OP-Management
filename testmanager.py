"""
Skript: test_manager (tests/test_manager.py)

Testzentrum für manager.py. Prüft Schritt für Schritt OPManager: Buchungsablauf, 
Rollback bei Ressourcenkonflikten sowie Zeitverschiebung (verschiebe_op) 
inkl. korrektem Rollback bei Konflikten.
"""

from manager import OPManager
from ressource import Ressource, Einmalartikel
from op import OPTyp


def run_tests():
    print("Starte Tests für manager.py")

    # 1. Erfolgreiche Buchung muss OP eintragen und Material verbrauchen
    manager = OPManager()
    manager.saal_hinzufuegen("Saal_1", kapazitaet=480)
    manager.ressource_registrieren(Ressource(name="Dr. Test"))
    manager.ressource_registrieren(Einmalartikel(name="Faeden", bestand=10, meldebestand=2))
    manager.op_typ_definieren(OPTyp(
        op_name="Standard-OP", standard_dauer=90,
        benoetigte_ressourcen={"Dr. Test": 1, "Faeden": 3}
    ))
    manager.plane_operation("Fall 1", "Standard-OP", "Saal_1", start_minute=0)
    saal = manager.saele["Saal_1"]
    print(f"\n[TEST 1] Anzahl geplanter OPs im Saal: {len(saal.geplante_ops)} (erwartet: 1)")
    print(f"Bestand Fäden nach Buchung: {manager.lager['Faeden'].bestand} (erwartet: 7, da 3 von 10 verbraucht)")
    assert len(saal.geplante_ops) == 1
    assert manager.lager["Faeden"].bestand == 7

    # 2. Unbekannter OP-Typ muss Fehler auslösen, bevor irgendetwas gebucht wird
    manager = OPManager()
    manager.saal_hinzufuegen("Saal_1", kapazitaet=480)
    manager.ressource_registrieren(Ressource(name="Dr. Test"))
    manager.op_typ_definieren(OPTyp(
        op_name="Standard-OP", standard_dauer=90, benoetigte_ressourcen={"Dr. Test": 1}
    ))
    print(f"\n[TEST 2] Versuche Buchung mit unbekanntem OP-Typ 'Nicht-Existent' -> erwarte Fehler")
    try:
        manager.plane_operation("Fall 1", "Nicht-Existent", "Saal_1", start_minute=0)
        fehler_kam = False
    except ValueError as e:
        fehler_kam = True
        print(f"Erhaltene Fehlermeldung: '{e}'")
    assert fehler_kam == True

    # 3. Ressourcenkonflikt darf am Ende keine OP im Saal landen lassen
    manager = OPManager()
    manager.saal_hinzufuegen("Saal_1", kapazitaet=480)
    manager.ressource_registrieren(Ressource(name="Dr. Test"))
    manager.ressource_registrieren(Einmalartikel(name="Faeden", bestand=10, meldebestand=2))
    manager.op_typ_definieren(OPTyp(
        op_name="Standard-OP", standard_dauer=90,
        benoetigte_ressourcen={"Dr. Test": 1, "Faeden": 3}
    ))
    manager.ressourcen_pool["Dr. Test"].blockieren("Fremd-Termin", 0, 90)
    print(f"\n[TEST 3] Dr. Test ist durch 'Fremd-Termin' bereits 0-90 belegt. Versuche trotzdem Fall 1 zu buchen -> erwarte Fehler")
    try:
        manager.plane_operation("Fall 1", "Standard-OP", "Saal_1", start_minute=0)
        fehler_kam = False
    except ValueError as e:
        fehler_kam = True
        print(f" Erhaltene Fehlermeldung: '{e}'")
    saal = manager.saele["Saal_1"]
    print(f" Anzahl geplanter OPs im Saal nach fehlgeschlagener Buchung: {len(saal.geplante_ops)} (erwartet: 0)")
    assert fehler_kam == True
    assert len(saal.geplante_ops) == 0

    # Gemeinsames Setup für die Verschiebungs-Tests (Fall 1 mit Dr. Test, Fall 2 ohne Ressourcen)
    manager = OPManager()
    manager.saal_hinzufuegen("Saal_1", kapazitaet=480)
    manager.ressource_registrieren(Ressource(name="Dr. Test"))
    manager.op_typ_definieren(OPTyp(
        op_name="Standard-OP", standard_dauer=90, benoetigte_ressourcen={"Dr. Test": 1}
    ))
    manager.op_typ_definieren(OPTyp(
        op_name="Ressourcenlose-OP", standard_dauer=90, benoetigte_ressourcen={}
    ))
    manager.plane_operation("Fall 1", "Standard-OP", "Saal_1", start_minute=0)
    manager.plane_operation("Fall 2", "Ressourcenlose-OP", "Saal_1", start_minute=110)
    saal = manager.saele["Saal_1"]
    arzt = manager.ressourcen_pool["Dr. Test"]

    # 4. Neue Dauer von 0 oder weniger muss abgelehnt werden
    print(f"\n[TEST 4] Versuche Fall 1 auf 0 Minuten zu setzen -> erwarte Fehler")
    try:
        manager.verschiebe_op("Saal_1", "Fall 1", neue_dauer=0)
        fehler_kam = False
    except ValueError as e:
        fehler_kam = True
        print(f"Erhaltene Fehlermeldung: '{e}'")
    assert fehler_kam == True

    # 5. Verkürzung muss Folgetermine automatisch nach vorne rücken
    print(f"\n[TEST 5] Vorher: Fall 1 = 0-90, Fall 2 = 110-200. Verkürze Fall 1 auf 60 Min.")
    manager.verschiebe_op("Saal_1", "Fall 1", neue_dauer=60)
    fall_1 = next(o for o in saal.geplante_ops if o.op_name == "Fall 1")
    fall_2 = next(o for o in saal.geplante_ops if o.op_name == "Fall 2")
    print(f"         Nachher: Fall 1 = {fall_1.start_minute}-{fall_1.end_minute} (erwartet: 0-60)")
    print(f"         Nachher: Fall 2 = {fall_2.start_minute}-{fall_2.end_minute} (erwartet: 80-170)")
    assert fall_1.end_minute == 60
    assert (fall_2.start_minute, fall_2.end_minute) == (80, 170)

    # 6. Regressionstest: fehlgeschlagene Verschiebung muss Ressourcen korrekt zurücksetzen
    start_fall_1, ende_fall_1 = fall_1.start_minute, fall_1.end_minute
    start_fall_2, ende_fall_2 = fall_2.start_minute, fall_2.end_minute
    arzt.blockieren("Externer Fremdtermin", von_minute=300, bis_minute=350)
    print(f"\n[TEST 6] Dr. Test hat externen Fremdtermin 300-350. Verlängere Fall 1 auf 350 Min. -> muss kollidieren")
    try:
        manager.verschiebe_op("Saal_1", "Fall 1", neue_dauer=350)
        fehler_kam = False
    except ValueError as e:
        fehler_kam = True
        print(f"Erhaltene Fehlermeldung: '{e}'")
    assert fehler_kam == True

    fall_1_nachher = next(o for o in saal.geplante_ops if o.op_name == "Fall 1")
    fall_2_nachher = next(o for o in saal.geplante_ops if o.op_name == "Fall 2")
    print(f"Fall 1 nach fehlgeschlagenem Versuch: {fall_1_nachher.start_minute}-{fall_1_nachher.end_minute} (erwartet unverändert: {start_fall_1}-{ende_fall_1})")
    print(f"Fall 2 nach fehlgeschlagenem Versuch: {fall_2_nachher.start_minute}-{fall_2_nachher.end_minute} (erwartet unverändert: {start_fall_2}-{ende_fall_2})")
    assert (fall_1_nachher.start_minute, fall_1_nachher.end_minute) == (start_fall_1, ende_fall_1)
    assert (fall_2_nachher.start_minute, fall_2_nachher.end_minute) == (start_fall_2, ende_fall_2)

    dr_test_frei_bei_fall_1_zeit = arzt.ist_verfuegbar(start_fall_1, ende_fall_1)
    dr_test_frei_bei_fremdtermin = arzt.ist_verfuegbar(300, 350)
    print(f"Dr. Test frei bei ursprünglicher Fall-1-Zeit ({start_fall_1}-{ende_fall_1})? {dr_test_frei_bei_fall_1_zeit} (erwartet: False)")
    print(f"Dr. Test frei beim Fremdtermin (300-350)? {dr_test_frei_bei_fremdtermin} (erwartet: False)")
    assert dr_test_frei_bei_fall_1_zeit == False
    assert dr_test_frei_bei_fremdtermin == False

    print("\nAlle Tests für manager.py erfolgreich")


if __name__ == "__main__":
    run_tests()