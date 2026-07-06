"""
Tests für ressource.py

Prüft die Basislogik der Ressourcenverwaltung (Verfügbarkeit, Blockieren, 
Freigeben) sowie die Besonderheiten von Instrument (Sterilisationszeit) 
und Einmalartikel (Lagerbestand, Meldebestand).
"""

import unittest
from ressource import Ressource, Instrument, Einmalartikel


class TestRessource(unittest.TestCase):

    def test_neu_angelegte_ressource_ist_frei(self):
        arzt = Ressource(name="Dr. Test")
        self.assertTrue(arzt.ist_verfuegbar(0, 90))

    def test_blockieren_erzeugt_konflikt_bei_ueberschneidung(self):
        arzt = Ressource(name="Dr. Test")
        arzt.blockieren("OP A", von_minute=0, bis_minute=90)

        # überlappt teilweise -> nicht verfügbar
        self.assertFalse(arzt.ist_verfuegbar(60, 120))
        # direkt angrenzend (kein Overlap) -> verfügbar
        self.assertTrue(arzt.ist_verfuegbar(90, 150))

    def test_freigeben_macht_ressource_wieder_verfuegbar(self):
        arzt = Ressource(name="Dr. Test")
        arzt.blockieren("OP A", von_minute=0, bis_minute=90)
        arzt.freigeben("OP A")

        self.assertTrue(arzt.ist_verfuegbar(0, 90))


class TestInstrument(unittest.TestCase):

    def test_blockieren_haengt_sterilisationsdauer_an(self):
        sieb = Instrument(name="Knie-Sieb")
        sieb.blockieren("OP A", von_minute=0, bis_minute=90)

        # 90-150 ist Sterilisationszeit -> NICHT frei
        self.assertFalse(sieb.ist_verfuegbar(90, 120))
        # ab Minute 150 (90 + 60 Sterilisation) wieder frei
        self.assertTrue(sieb.ist_verfuegbar(150, 200))

    def test_vorausplanung_zukuenftiger_op_moeglich(self):
        """Ein Sieb kann bereits im Voraus für eine spätere OP reserviert werden,
        solange die Sterilisationszeit der ersten OP nicht überschnitten wird."""
        sieb = Instrument(name="Knie-Sieb")
        sieb.blockieren("OP A", von_minute=0, bis_minute=90)

        # Vorbuchung direkt nach Ende der Sterilisation -> erlaubt
        self.assertTrue(sieb.ist_verfuegbar(150, 240))
        sieb.blockieren("OP B", von_minute=150, bis_minute=240)
        self.assertFalse(sieb.ist_verfuegbar(150, 200))


class TestEinmalartikel(unittest.TestCase):

    def test_konsumiere_reduziert_bestand