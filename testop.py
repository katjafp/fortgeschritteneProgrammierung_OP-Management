"""
Skript: test_op (tests/test_op.py)

Testzentrum für op.py. Prüft Schritt für Schritt OPSaal: Kollisionserkennung, 
Reinigungszeit zwischen zwei OPs, Kapazitätsgrenze und Berechnung freier 
Zeitfenster.
"""

from op import OP, OPSaal


def run_tests():
    print("Starte Tests für op.py")

    # 1. OP ohne Konflikte muss erfolgreich hinzugefügt werden
    saal = OPSaal(saal_id="Saal_1", kapazitaet_minute=480, reinigung=20)
    op = OP(op_name="Fall 1", saal_id="Saal_1", start_minute=0, dauer=90)
    saal.op_hinzufuegen(op)
    print(f"\n[TEST 1] OP 'Fall 1' (0-90) hinzugefügt. Anzahl geplanter OPs: {len(saal.geplante_ops)} (erwartet: 1)")
    assert len(saal.geplante_ops) == 1

    # 2. Überschneidung zweier OPs muss abgelehnt werden
    saal = OPSaal(saal_id="Saal_1", kapazitaet_minute=480, reinigung=20)
    op_a = OP(op_name="Fall 1", saal_id="Saal_1", start_minute=0, dauer=90)
    saal.op_hinzufuegen(op_a)
    op_b = OP(op_name="Fall 2", saal_id="Saal_1", start_minute=60, dauer=90)
    print(f"\n[TEST 2] Fall 1 belegt 0-90. Versuche Fall 2 bei 60-150 (überlappt) -> erwarte Fehler")
    try:
        saal.op_hinzufuegen(op_b)
        fehler_kam = False
    except ValueError as e:
        fehler_kam = True
        print(f"Erhaltene Fehlermeldung: '{e}'")
    assert fehler_kam == True

    # 3. Reinigungszeit zwischen zwei OPs muss eingehalten werden
    saal = OPSaal(saal_id="Saal_1", kapazitaet_minute=480, reinigung=20)
    op_a = OP(op_name="Fall 1", saal_id="Saal_1", start_minute=0, dauer=90)
    saal.op_hinzufuegen(op_a)
    op_b = OP(op_name="Fall 2", saal_id="Saal_1", start_minute=90, dauer=60)
    print(f"\n[TEST 3] Fall 1 endet bei Minute 90. Fall 2 startet direkt bei 90 (ohne 20 Min. Reinigung) -> erwarte Fehler")
    try:
        saal.op_hinzufuegen(op_b)
        fehler_kam = False
    except ValueError:
        fehler_kam = True
    print(f"Fehler wie erwartet ausgelöst: {fehler_kam}")
    assert fehler_kam == True

    op_c = OP(op_name="Fall 3", saal_id="Saal_1", start_minute=110, dauer=60)
    print(f"Fall 3 startet bei Minute 110 (90 + 20 Reinigung) -> sollte klappen")
    saal.op_hinzufuegen(op_c)
    assert op_c in saal.geplante_ops
    print(f"         Erfolgreich hinzugefügt.")

    # 4. Überschreitung der Saal-Schließzeit muss abgelehnt werden
    saal = OPSaal(saal_id="Saal_1", kapazitaet_minute=480, reinigung=20)
    op = OP(op_name="Zu lang", saal_id="Saal_1", start_minute=0, dauer=500)
    print(f"\n[TEST 4] Saal-Kapazität: 480 Min. Versuche 500-Minuten-OP hinzuzufügen -> erwarte Fehler")
    try:
        saal.op_hinzufuegen(op)
        fehler_kam = False
    except ValueError as e:
        fehler_kam = True
        print(f"Erhaltene Fehlermeldung: '{e}'")
    assert fehler_kam == True

    # 5. Freie Zeitfenster müssen korrekt berechnet werden
    saal = OPSaal(saal_id="Saal_1", kapazitaet_minute=480, reinigung=20)
    op = OP(op_name="Fall 1", saal_id="Saal_1", start_minute=100, dauer=90)
    saal.op_hinzufuegen(op)
    fenster = saal.finde_freie_fenster()
    print(f"\n[TEST 5] Fall 1 gebucht 100-190. Gefundene freie Fenster: {fenster}")
    print(f"         Erwartet: Lücke 0-100 (davor) und 210-480 (danach, inkl. 20 Min. Reinigung)")
    assert fenster[0] == {"von": 0, "bis": 100, "dauer": 100}
    assert fenster[1] == {"von": 210, "bis": 480, "dauer": 270}

    print("\nAlle Tests für op.py erfolgreich")

if __name__ == "__main__":
    run_tests()