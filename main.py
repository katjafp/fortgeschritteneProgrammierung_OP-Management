"""
Skript: main (main.py)

Testzentrum für das digitale OP- und Ressourcenmanagement.
Hier wird der Klinikalltag simuliert durch das Anlegen von Test-Ressourcen, OP-Sälen. 
Prüfung des Zusammenspiels der Module um Fehler schnell zu identifizieren und vermeiden.
"""

from ressource import Ressource, Instrument, Einmalartikel
from op import OPTyp, OP, OPSaal
from manager import OPManager

def run_tests():
    print("Starte Kliniksimulation & Systemtests")

    # 1. Instanziierung des Haupt-Managers
    manager = OPManager()

    # 2. Test: OP-Säle registrieren
    print("\nOP-Säle registrieren")
    manager.saal_hinzufuegen(saal_id="Zentral-OP_Saal_1", kapazitaet=480) # 8-Stunden-Schicht
    manager.saal_hinzufuegen(saal_id="Ambulant_Saal_2", kapazitaet=360)   # 6-Stunden-Schicht

    # 3. Test: Ressourcen-Pool befüllen (Mensch & Material)
    print("\nRessourcenpool")
    
    # Personal & Geräte
    arzt_1 = Ressource(name="Dr. Müller (Anästhesie)")
    roentgen = Ressource(name="Mobiles Röntgengerät C-Bogen")
    manager.ressource_registrieren(arzt_1)
    manager.ressource_registrieren(roentgen)
    
    # Instrumenten-Siebe (mit Steri-Logik)
    knie_sieb = Instrument(name="Chirurgisches Knie-TEP-Sieb basic")
    manager.ressource_registrieren(knie_sieb)
    
    # Einmalartikel (mit Lager- und Meldebestand)
    faeden = Einmalartikel(name="Nahtmaterial Vicryl 3-0", bestand=50, meldebestand=10)
    manager.ressource_registrieren(faeden)
    
    print(f"Test-Ressourcen erfolgreich an den Manager übergeben.")

    # 4. Test: Ein OP-Rezept (OPTyp) definieren
    print("\nOP-Typ definieren")
    # Eine Knie-OP dauert 90 Minuten und braucht z.B. 3 Fäden
    knie_op_rezept = OPTyp(
        op_name="Knie-Endoprothese", 
        standard_dauer=90, 
        benoetigte_ressourcen={"Nahtmaterial Vicryl 3-0": 3}
    )
    manager.op_typ_definieren(knie_op_rezept)
    print(f"OP-Rezept für '{knie_op_rezept.op_name}' im System hinterlegt.")

    # 5. Test: Einmalartikel-Verbrauch & Warnung triggern
    print("\nLagerbestands- & Warnungs-Check")
    print(f"Aktueller Bestand vor Entnahme: {faeden.bestand} Stück")
    
    # Simulation große Materialentnahme um zu sehen ob die Warnung anspringt
    print("Simuliere Entnahme von 42 Fäden...")
    faeden.konsumiere(42) # Rest müsste 8 sein -> Meldebestand 10 unterschritten!

    print("Systemtest erfolgreich")

if __name__ == "__main__":
    run_tests()