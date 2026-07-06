"""
Tests für ressource.py

Prüft die Basislogik der Ressourcenverwaltung (Verfügbarkeit, Blockieren, 
Freigeben) sowie die Besonderheiten von Instrument (Sterilisationszeit) 
und Einmalartikel (Lagerbestand, Meldebestand).

Ausführen mit: python -m unittest discover tests -v
(die -v-Option zeigt zusätzlich Testname + Kurzbeschreibung an)
"""

import unittest
from ressource import Ressource, Instrument, Einmalartikel


class TestRessource(unittest.TestCase):

    def test_neu_angelegte_ressource_ist_frei(self):
        """Eine frisch angelegte Ressource hat noch keine Buchungen -> überall frei."""
        arzt = Ressource(name="Dr. Test")
        ergebnis = arzt.ist_verfuegbar(0, 90)
        print(f"\n  Neuer Arzt, keine Buchungen -> frei zwischen 0-90? {ergebnis} (erwartet: True)")
        self.assertTrue(ergebnis)

    def test_blockieren_erzeugt_konflikt_bei_ueberschneidung(self):
        """Eine Buchung 0-90 muss bei Überschneidung einen Konflikt zeigen, bei direktem Anschluss aber nicht."""
        arzt = Ressource(name="Dr. Test")
        arzt.blockieren("OP A", von_minute=0, bis_minute=90)

        ueberschneidung = arzt.ist_verfuegbar(60, 120)
        print(f"\n  Arzt gebucht 0-90. Frei bei 60-120 (überlappt)? {ueberschneidung} (erwartet: False)")
        self.assertFalse(ueberschneidung)

        direkt_danach = arzt.ist_verfuegbar(90, 150)
        print(f"  Frei bei 90-150 (direkt danach, kein Overlap)? {direkt_danach} (erwartet: True)")
        self.assertTrue(direkt_danach)

    def test_freigeben_macht_ressource_wieder_verfuegbar(self):
        """Nach freigeben() muss die Ressource wieder für den ehemaligen Zeitraum verfügbar sein."""
        arzt = Ressource(name="Dr. Test")
        arzt.blockieren("OP A", von_minute=0, bis_minute=90)
        arzt.freigeben("OP A")

        ergebnis = arzt.ist_verfuegbar(0, 90)
        print(f"\n  Arzt gebucht 0-90, dann freigegeben. Frei bei 0-90? {ergebnis} (erwartet: True)")
        self.assertTrue(ergebnis)


class TestInstrument(unittest.TestCase):

    def test_blockieren_haengt_sterilisationsdauer_an(self):
        """Nach einer OP muss ein Sieb automatisch 60 Min. Sterilisationszeit blockiert haben."""
        sieb = Instrument(name="Knie-Sieb")
        sieb.blockieren("OP A", von_minute=0, bis_minute=90)

        waehrend_steri = sieb.ist_verfuegbar(90, 120)
        print(f"\n  Sieb gebucht 0-90 (OP-Ende). Frei bei 90-120 (Sterilisationszeit)? {waehrend_steri} (erwartet: False)")
        self.assertFalse(waehrend_steri)

        nach_steri = sieb.ist_verfuegbar(150, 200)
        print(f"  Frei bei 150-200 (nach 60 Min. Sterilisation)? {nach_steri} (erwartet: True)")
        self.assertTrue(nach_steri)

    def test_vorausplanung_zukuenftiger_op_moeglich(self):
        """Ein Sieb kann schon im Voraus für eine spätere OP reserviert werden, 
        solange die Sterilisationszeit dazwischen passt."""
        sieb = Instrument(name="Knie-Sieb")
        sieb.blockieren("OP A", von_minute=0, bis_minute=90)

        vorbuchung_moeglich = sieb.ist_verfuegbar(150, 240)
        print(f"\n  Sieb frei für Vorbuchung OP B bei 150-240 (nach Sterilisation von OP A)? {vorbuchung_moeglich} (erwartet: True)")
        self.assertTrue(vorbuchung_moeglich)

        sieb.blockieren("OP B", von_minute=150, bis_minute=240)
        jetzt_belegt = sieb.ist_verfuegbar(150, 200)
        print(f"  Nach Buchung von OP B: frei bei 150-200? {jetzt_belegt} (erwartet: False)")
        self.assertFalse(jetzt_belegt)


class TestEinmalartikel(unittest.TestCase):

    def test_konsumiere_reduziert_bestand(self):
        """Der Bestand muss nach konsumiere() um genau die verbrauchte Menge sinken."""
        faeden = Einmalartikel(name="Nahtmaterial", bestand=50, meldebestand=10)
        faeden.konsumiere(5)
        print(f"\n  Bestand vor Verbrauch: 50, nach Verbrauch von 5: {faeden.bestand} (erwartet: 45)")
        self.assertEqual(faeden.bestand, 45)

    def test_konsumiere_wirft_fehler_bei_zu_wenig_bestand(self):
        """Reicht der Bestand nicht aus, muss ein ValueError kommen UND der Bestand darf sich nicht ändern."""
        faeden = Einmalartikel(name="Nahtmaterial", bestand=2, meldebestand=10)
        print(f"\n  Bestand: 2, Verbrauch von 5 angefordert (zu wenig) -> erwarte ValueError")
        with self.assertRaises(ValueError) as fehler:
            faeden.konsumiere(5)
        print(f"  Erhaltene Fehlermeldung: '{fehler.exception}'")
        print(f"  Bestand nach fehlgeschlagenem Verbrauch: {faeden.bestand} (erwartet: unverändert 2)")
        self.assertEqual(faeden.bestand, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)