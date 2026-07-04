"""
Datei: app.py
Streamlit-Oberfläche für das digitale OP-Planungs- & Ressourcenmanagement.
"""

import streamlit as st
from manager import OPManager
from ressource import Ressource, Instrument, Einmalartikel
from op import OPTyp

st.set_page_config(page_title="OP-Planung", layout="wide")


def initialisiere_system() -> OPManager:
    """Baut den Manager EINMAL auf und befüllt ihn mit Testdaten (Klinik-Setup)."""
    manager = OPManager()

    manager.saal_hinzufuegen("Zentral-OP_Saal_1", kapazitaet=480)
    manager.saal_hinzufuegen("Ambulant_Saal_2", kapazitaet=360)

    manager.ressource_registrieren(Ressource(name="Dr. Müller (Anästhesie)"))
    manager.ressource_registrieren(Ressource(name="Mobiles Röntgengerät C-Bogen"))
    manager.ressource_registrieren(Instrument(name="Chirurgisches Knie-TEP-Sieb basic"))
    manager.ressource_registrieren(Einmalartikel(name="Nahtmaterial Vicryl 3-0", bestand=50, meldebestand=10))

    manager.op_typ_definieren(OPTyp(
        op_name="Knie-Endoprothese",
        standard_dauer=90,
        benoetigte_ressourcen={"Nahtmaterial Vicryl 3-0": 3}
    ))
    return manager


# Nur beim ALLERERSTEN Rerun aufbauen - danach bleibt der Manager erhalten
if "manager" not in st.session_state:
    st.session_state.manager = initialisiere_system()

manager = st.session_state.manager

st.title("Digitales OP-Planungs- & Ressourcenmanagement")

st.header("Übersicht: OP-Säle")

for saal_id, saal in manager.saele.items():
    with st.container(border=True):
        st.subheader(saal_id)
        col1, col2 = st.columns(2)
        col1.metric("Kapazität (Min.)", saal.kapazitaet_minute)
        col2.metric("Freie Zeit (Min.)", saal.berechne_restzeit())

        if saal.geplante_ops:
            st.write("**Geplante OPs:**")
            for op in saal.geplante_ops:
                st.write(f"- {op.op_name}: Minute {op.start_minute}–{op.end_minute}")
        else:
            st.write("_Noch keine OPs geplant._")

st.header("Neue OP buchen")

with st.form("op_buchen_formular"):
    op_name = st.text_input("Bezeichnung dieser Buchung (z.B. Patientenname/Fall)")
    op_typ_name = st.selectbox("OP-Typ", options=list(manager.op_typen.keys()))
    saal_id = st.selectbox("Saal", options=list(manager.saele.keys()))
    start_minute = st.number_input("Startminute (0 = Schichtbeginn)", min_value=0, step=10)

    abschicken = st.form_submit_button("OP einplanen")

    if abschicken:
        if not op_name:
            st.error("Bitte eine Bezeichnung für die Buchung eingeben.")
        else:
            try:
                manager.plane_operation(
                    op_name=op_name,
                    op_typ_name=op_typ_name,
                    saal_id=saal_id,
                    start_minute=int(start_minute)
                )
                st.success(f"'{op_name}' erfolgreich in {saal_id} eingeplant!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))