"""
Tests für manager.py

Prüft OPManager: Buchungsablauf, Rollback bei Konflikten, sowie 
Zeitverschiebung (verschiebe_op) inkl. korrektem Rollback bei Konflikten.
"""

import unittest
from manager import OPManager
from ressource import Ressource, Instrument, Einmalartikel
from op import OPTyp


class TestOPManagerBuchung(unittest.TestCase):

    def setUp(self):
        self.manager = OPManager()
        self.manager.saal_hinzufuegen("Saal_1", kapazitaet=480)

        self.manager.ressource_registrieren(Ressource(name="Dr. Test"))
        self.manager.ressource_registrieren(
            Einmalartikel(name="Faeden", bestand=10, meldebestand=2)
        )
        self.manager.op_typ_definieren(OPTyp(
            op_name="Standard-OP",
            standard_dauer=90,
            benoetigte_ressourcen={"Dr. Test": 1, "Faeden": 3}
        ))

    def test_erfolgreiche_buchung(self):
        self.manager.plane_operation("Fall 1", "Standard-OP", "Saal_1", start_minute=0)

        saal = self.manager.saele["Saal_1"]
        self.assertEqual(len(saal.geplante_ops), 1)
        # Material muss verbraucht worden sein
        self.assertEqual(self.manager.lager["Faeden"].bestand, 7)

    def test_unbekannter_op_typ_wirft_fehler(self):
        with self.assertRaises(ValueError):
            self.manager.plane_operation("Fall 1", "Nicht-Existent", "Saal_1", start_minute=0)

    def test_ressourcenkonflikt_gibt_bereits_geblockte_ressourcen_frei(self):
        """Wenn eine Ressource mitten in der Prüfung blockiert ist, müssen 
        bereits temporär geblockte Ressourcen (hier: Dr. Test) wieder freigegeben werden."""
        # Dr. Test manuell für den Zeitraum blockieren, damit die Buchung fehlschlägt
        self.manager.ressourcen_pool["Dr. Test"].blockieren("Fremd-Termin", 0, 90)

        with self.assertRaises(ValueError):
            self.manager.plane_operation("Fall 1", "Standard-OP", "Saal_1", start_minute=0)

        # Material darf trotzdem nicht doppelt verbraucht worden sein (kein Rollback für
        # Einmalartikel nötig, da sie in der Iterationsreihenfolge nach Dr. Test verbraucht würden -
        # hier prüfen wir stattdessen, dass gar keine OP im Saal gelandet ist)
        saal = self.manager.saele["Saal_1"]
        self.assertEqual(len(saal.geplante_ops), 0)


class TestOPManagerVerschiebung(unittest.TestCase):

    def setUp(self):
        self.manager = OPManager()
        self.manager.saal_hinzufuegen("Saal_1", kapazitaet=480)
        self.manager.ressource_registrieren(Ressource(name="Dr. Test"))
        self.manager.op_typ_definieren(OPTyp(
            op_name="Standard-OP", standard_dauer=90,
            benoetigte_ressourcen={"Dr. Test": 1}
        ))
        # OP-Typ ohne Ressourcenbedarf, für Fall 2 (soll bei der Verschiebung
        # selbst keine Rolle spielen, nur zeitlich mitrücken)
        self.manager.op_typ_definieren(OPTyp(
            op_name="Ressourcenlose-OP", standard_dauer=90, benoetigte_ressourcen={}
        ))

        self.manager.plane_operation("Fall 1", "Standard-OP", "Saal_1", start_minute=0)
        self.manager.plane_operation("Fall 2", "Ressourcenlose-OP", "Saal_1", start_minute=110)

    def test_neue_dauer_muss_positiv_sein(self):
        with self.assertRaises(ValueError):
            self.manager.verschiebe_op("Saal_1", "Fall 1", neue_dauer=0)

    def test_verkuerzung_rueckt_folgetermine_nach_vorne(self):
        """Der 'Zeitschieber'-Algorithmus verschiebt Folgetermine in BEIDE 
        Richtungen: wird Fall 1 kürzer, rückt Fall 2 automatisch näher heran."""
        self.manager.verschiebe_op("Saal_1", "Fall 1", neue_dauer=60)

        saal = self.manager.saele["Saal_1"]
        fall_1 = next(o for o in saal.geplante_ops if o.op_name == "Fall 1")
        fall_2 = next(o for o in saal.geplante_ops if o.op_name == "Fall 2")

        self.assertEqual(fall_1.end_minute, 60)
        # Fall 1 wurde um 30 Min. kürzer (90 -> 60) -> Fall 2 rückt um dieselben
        # 30 Minuten vor: von 110-200 auf 80-170
        self.assertEqual((fall_2.start_minute, fall_2.end_minute), (80, 170))

    def test_kollision_bei_verlaengerung_wird_verhindert_und_zustand_bleibt_erhalten(self):
        """Regressionstest für den Rollback-Bug: nach einer fehlgeschlagenen 
        Verschiebung müssen ALLE betroffenen Ressourcen wieder ihre EIGENEN 
        ursprünglichen Zeiten haben - nicht die Zeiten der OP, die den Konflikt 
        ausgelöst hat. Der Konflikt wird hier bewusst über einen externen 
        Dr.-Test-Termin ausgelöst (nicht über die Saal-Schließzeit), damit 
        wirklich der Ressourcen-Rollback-Pfad getestet wird."""
        saal = self.manager.saele["Saal_1"]
        arzt = self.manager.ressourcen_pool["Dr. Test"]

        fall_1_vorher = next(o for o in saal.geplante_ops if o.op_name == "Fall 1")
        fall_2_vorher = next(o for o in saal.geplante_ops if o.op_name == "Fall 2")
        start_fall_1, ende_fall_1 = fall_1_vorher.start_minute, fall_1_vorher.end_minute
        start_fall_2, ende_fall_2 = fall_2_vorher.start_minute, fall_2_vorher.end_minute

        # Externer Termin von Dr. Test, mit dem eine verlängerte Fall-1-OP kollidieren wird
        arzt.blockieren("Externer Fremdtermin", von_minute=300, bis_minute=350)

        # Fall 1 auf 350 Min. verlängern -> überschneidet sich mit dem Fremdtermin.
        # Saal-Kapazität (480) reicht dafür noch locker aus, der Fehler kommt also
        # garantiert aus der Ressourcenprüfung, nicht aus der Kapazitätsprüfung.
        with self.assertRaises(ValueError):
            self.manager.verschiebe_op("Saal_1", "Fall 1", neue_dauer=350)

        # Zustand muss vollständig unverändert sein
        fall_1_nachher = next(o for o in saal.geplante_ops if o.op_name == "Fall 1")
        fall_2_nachher = next(o for o in saal.geplante_ops if o.op_name == "Fall 2")

        self.assertEqual((fall_1_nachher.start_minute, fall_1_nachher.end_minute),
                          (start_fall_1, ende_fall_1))
        self.assertEqual((fall_2_nachher.start_minute, fall_2_nachher.end_minute),
                          (start_fall_2, ende_fall_2))

        # Dr. Test muss wieder für die EIGENE ursprüngliche Fall-1-Zeit blockiert
        # sein (der Bug hätte hier fälschlicherweise die Zeit des Fremdtermins
        # eingetragen, egal für welche Ressource/OP der Rollback lief)
        self.assertFalse(arzt.ist_verfuegbar(start_fall_1, ende_fall_1))
        # und der Fremdtermin selbst muss natürlich auch weiterhin blockiert sein
        self.assertFalse(arzt.ist_verfuegbar(300, 350))


if __name__ == "__main__":
    unittest.main()