"""
Skript: main (main.py)

Testzentrum für das digitale OP- und Ressourcenmanagement.
Hier wird der Klinikalltag simuliert durch das Anlegen von Test-Ressourcen, OP-Sälen. 
Prüfung des Zusammenspiels der Module um Fehler schnell zu identifizieren und vermeiden.
"""

import manager
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
    
    print("Simuliere Entnahme von Fäden...")
    faeden.konsumiere(5) 

    manager.plane_operation(
        op_name="Knie-Endoprothese", 
        saal_id="Zentral-OP_Saal_1", 
        start_minute=0
    )

    # Test: Was passiert mit Restzeit im Saal?
    saal = manager.saele["Zentral-OP_Saal_1"]
    print(f"Verbleibende reine OP-Zeit in {saal.saal_id}: {saal.berechne_restzeit()} Minuten.")
    print("Systemtest erfolgreich")

if __name__ == "__main__":
    run_tests()

# --- SCHNELLTEST FÜR CLASS RESSOURCE ---

# 1. Wir erstellen die Ressource "Dr. Müller"
dr_mueller = Ressource("Dr. Müller")

print(f"Test 1: Ist Dr. Müller am Anfang frei?")
# Wir fragen: Hat er von Minute 0 bis 90 Zeit?
print(f"Verfügbar (0-90): {dr_mueller.ist_verfuegbar(0, 90)}")  # Erwartet: True

print(f"\nTest 2: Wir buchen eine Knie-OP (Minute 0 bis 90)")
dr_mueller.blockieren("Knie-OP", 0, 90)
# Wir schauen uns an, was in seiner Liste gelandet ist
print(f"Einträge im Kalender: {dr_mueller.geplante_ops}")

print(f"\nTest 3: Erneute Abfragen")
# Anfrage A: Hat er Zeit für eine OP, die sich überschneidet (z.B. Minute 60 bis 120)?
print(f"Verfügbar (60-120): {dr_mueller.ist_verfuegbar(60, 120)}")  # Erwartet: False (Konflikt!)

# Anfrage B: Hat er Zeit für eine OP danach (z.B. Minute 120 bis 180)?
print(f"Verfügbar (120-180): {dr_mueller.ist_verfuegbar(120, 180)}")  # Erwartet: True (Frei!)

print(f"\nTest 4: Wir geben die Knie-OP wieder frei")
dr_mueller.freigeben("Knie-OP")
print(f"Einträge im Kalender nach Freigabe: {dr_mueller.geplante_ops}") # Erwartet: [] (wieder leer)