"""
Skript: test_ressource (tests/test_ressource.py)

Testzentrum für ressource.py. Prüft Schritt für Schritt die Basislogik der 
Ressourcenverwaltung (Verfügbarkeit, Blockieren, Freigeben) sowie die 
Besonderheiten von Instrument (Sterilisationszeit) und Einmalartikel 
(Lagerbestand, Meldebestand).
"""

from ressource import Ressource, Instrument, Einmalartikel


def run_tests():
    print("Starte Tests für ressource.py")

    # 1. Neu angelegte Ressource ist überall frei
    arzt = Ressource(name="Dr. Test")
    ergebnis = arzt.ist_verfuegbar(0, 90)
    print(f"\n[TEST 1] Neuer Arzt, keine Buchungen -> frei zwischen 0-90? {ergebnis} (erwartet: True)")
    assert ergebnis == True

    # 2. Blockieren erzeugt Konflikt bei Überschneidung, aber nicht bei direktem Anschluss
    arzt = Ressource(name="Dr. Test")
    arzt.blockieren("OP A", von_minute=0, bis_minute=90)
    ueberschneidung = arzt.ist_verfuegbar(60, 120)
    direkt_danach = arzt.ist_verfuegbar(90, 150)
    print(f"\n[TEST 2] Arzt gebucht 0-90. Frei bei 60-120 (überlappt)? {ueberschneidung} (erwartet: False)")
    print(f"Frei bei 90-150 (direkt danach, kein Overlap)? {direkt_danach} (erwartet: True)")
    assert ueberschneidung == False
    assert direkt_danach == True

    # 3. freigeben() macht Ressource wieder verfügbar
    arzt = Ressource(name="Dr. Test")
    arzt.blockieren("OP A", von_minute=0, bis_minute=90)
    arzt.freigeben("OP A")
    ergebnis = arzt.ist_verfuegbar(0, 90)
    print(f"\n[TEST 3] Arzt gebucht 0-90, dann freigegeben. Frei bei 0-90? {ergebnis} (erwartet: True)")
    assert ergebnis == True

    # 4. Instrument haengt automatisch Sterilisationsdauer an
    sieb = Instrument(name="Knie-Sieb")
    sieb.blockieren("OP A", von_minute=0, bis_minute=90)
    waehrend_steri = sieb.ist_verfuegbar(90, 120)
    nach_steri = sieb.ist_verfuegbar(150, 200)
    print(f"\n[TEST 4] Sieb gebucht 0-90. Frei bei 90-120 (Sterilisationszeit)? {waehrend_steri} (erwartet: False)")
    print(f"Frei bei 150-200 (nach 60 Min. Sterilisation)? {nach_steri} (erwartet: True)")
    assert waehrend_steri == False
    assert nach_steri == True

    # 5. Vorausplanung einer zukünftigen OP mit demselben Sieb
    sieb = Instrument(name="Knie-Sieb")
    sieb.blockieren("OP A", von_minute=0, bis_minute=90)
    vorbuchung_moeglich = sieb.ist_verfuegbar(150, 240)
    sieb.blockieren("OP B", von_minute=150, bis_minute=240)
    jetzt_belegt = sieb.ist_verfuegbar(150, 200)
    print(f"\n[TEST 5] Sieb frei für Vorbuchung OP B bei 150-240? {vorbuchung_moeglich} (erwartet: True)")
    print(f"Nach Buchung von OP B: frei bei 150-200? {jetzt_belegt} (erwartet: False)")
    assert vorbuchung_moeglich == True
    assert jetzt_belegt == False

    # 6. konsumiere() reduziert den Bestand
    faeden = Einmalartikel(name="Nahtmaterial", bestand=50, meldebestand=10)
    faeden.konsumiere(5)
    print(f"\n[TEST 6] Bestand vor Verbrauch: 50, nach Verbrauch von 5: {faeden.bestand} (erwartet: 45)")
    assert faeden.bestand == 45

    # 7. konsumiere() wirft Fehler bei zu wenig Bestand, Bestand bleibt unverändert
    faeden = Einmalartikel(name="Nahtmaterial", bestand=2, meldebestand=10)
    print(f"\n[TEST 7] Bestand: 2, Verbrauch von 5 angefordert (zu wenig) -> erwarte ValueError")
    try:
        faeden.konsumiere(5)
        fehler_kam = False
    except ValueError as e:
        fehler_kam = True
        print(f"Erhaltene Fehlermeldung: '{e}'")
    print(f"Bestand nach fehlgeschlagenem Verbrauch: {faeden.bestand} (erwartet: unverändert 2)")
    assert fehler_kam == True
    assert faeden.bestand == 2

    print("\nAlle Tests für ressource.py erfolgreich")


if __name__ == "__main__":
    run_tests()