"""
Skript: main (main.py)

Testzentrum für das digitale OP- und Ressourcenmanagement.
"""

from klinik_setup import baue_orthopaedie_klinik
from op import minute_zu_uhrzeit


def zeige_tagesplan(manager) -> None:
    """Gibt für jeden Saal die Restzeit und alle geplanten OPs mit Uhrzeit aus."""
    for saal_id, saal in manager.saele.items():
        print(f"\n--- {saal_id} (Restzeit: {saal.berechne_restzeit()} Min.) ---")
        if not saal.geplante_ops:
            print("  Keine OPs geplant.")
            continue
        for op in saal.geplante_ops:
            von = minute_zu_uhrzeit(op.start_minute)
            bis = minute_zu_uhrzeit(op.end_minute)
            print(f"  {von}-{bis} Uhr: {op.op_name}")

def main() -> None:
    # Klinik-Setup (Säle, Personal, Geräte, Siebe, Lager, OP-Typen)
    manager = baue_orthopaedie_klinik()
    print(f"Säle:               {list(manager.saele.keys())}")
    print(f"Personal & Geräte:  {list(manager.ressourcen_pool.keys())}")
    print(f"Lager:              {list(manager.lager.keys())}")
    print(f"OP-Typen-Katalog:   {list(manager.op_typen.keys())}")

    # Tagesplanung: 5 OPs über 3 Säle
    geplante_buchungen = [
        ("Müller, Knie li.", "Knie-TEP", "Saal_1_Endoprothetik", 0),
        ("Schmidt, Hüfte re.", "Hüft-TEP", "Saal_1_Endoprothetik", 140),
        ("Becker, LWS-Instabilität", "Wirbelsaeulen-Spondylodese", "Saal_2_Wirbelsaeule", 0),
        ("Fischer, Schulter li.", "Schulter-Arthroskopie", "Saal_3_Ambulant", 0),
        ("Wagner, Sprunggelenk", "Sprunggelenk-Arthrodese", "Saal_3_Ambulant", 80),
    ]
    ergebnisse = []
    for op_name, op_typ_name, saal_id, start_minute in geplante_buchungen:
        try:
            manager.plane_operation(op_name, op_typ_name, saal_id, start_minute=start_minute)
            ergebnisse.append({"op_name": op_name, "erfolgreich": True})
        except ValueError as e:
            ergebnisse.append({"op_name": op_name, "erfolgreich": False, "fehler": str(e)})
    fehlgeschlagen = [e for e in ergebnisse if not e["erfolgreich"]]


    if fehlgeschlagen:
        print(f"\n{len(fehlgeschlagen)} von {len(ergebnisse)} Buchungen fehlgeschlagen:")
        for e in fehlgeschlagen:
            print(f"  - '{e['op_name']}': {e['fehler']}")    
    # Ressourcenkonflikt provozieren
    print("Versuch: eine 2. Knie-OP in Saal 1, während der Operateur Endoprothetik bereits operiert")
    try:
        manager.plane_operation("Krause, Knie re.", "Knie-TEP", "Saal_1_Endoprothetik", start_minute=0)
    except ValueError as e:
        print(f"Erwarteter Fehler: {e}")
    print("-> Keine Ressource bleibt hängen, kein Teil-Zustand im Saal (Rollback).")

    # Live-Statur um 9:30
    manager.zeige_verfuegbare_ressourcen(90)
    manager.zeige_aktuelle_ops(90)

    #Komplikation - Knie-TEP dauert 30 Min. länger als geplant
    print("Vorher: Müller 0-120, Schmidt 140-240 (Saal 1)")
    manager.verschiebe_op("Saal_1_Endoprothetik", "Müller, Knie li.", neue_dauer=150)
    zeige_tagesplan(manager)

    #Verschiebung, die nicht mehr möglich ist
    print("Versuch: die Wirbelsäulen-OP künstlich auf 470 Minuten verlängern...")
    try:
        manager.verschiebe_op("Saal_2_Wirbelsaeule", "Becker, LWS-Instabilität", neue_dauer=470)
    except ValueError as e:
        print(f"Erwarteter Fehler: {e}")
    print("-> Ursprünglicher Zeitplan bleibt vollständig erhalten (kein Teil-Zustand).")

    #Meldebestand-Warnung provozieren
    print("Zusätzlicher Verbrauch von 3x 'Knochenzement Palacos' (Nachlieferung simulieren)...")
    manager.lager["Knochenzement Palacos"].konsumiere(3)

    #Tagesabschluss - finaler Zeitplan aller Säle
    zeige_tagesplan(manager)


if __name__ == "__main__":
    main()