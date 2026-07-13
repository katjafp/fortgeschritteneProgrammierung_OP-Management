"""
Datei: app.py
Streamlit-Oberfläche für das digitale OP-Planungs- & Ressourcenmanagement.
"""
import datetime
import streamlit as st 
from op import minute_zu_uhrzeit, uhrzeit_zu_minute
from klinik_setup import baue_orthopaedie_klinik

if "manager" not in st.session_state:
    st.session_state.manager = baue_orthopaedie_klinik()

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
                st.write(f"- {op.op_name}: {minute_zu_uhrzeit(op.start_minute)}–{minute_zu_uhrzeit(op.end_minute)} Uhr")
        else:
            st.write("_Noch keine OPs geplant._")

st.header("Lagerübersicht (Einmalartikel)")

for name, artikel in manager.lager.items():
    with st.container(border=True):
        col1, col2 = st.columns(2)
        col1.metric(name, f"{artikel.bestand} Stück")
        if artikel.bestand <= artikel.meldebestand:
            col2.warning("Meldebestand unterschritten – Nachbestellung nötig!")
        else:
            col2.success("Bestand ausreichend")

st.header("Neue OP buchen")

with st.form("op_buchen_formular"):
    op_name = st.text_input("Bezeichnung dieser Buchung (z.B. Patientenname/Fall)")
    op_typ_name = st.selectbox("OP-Typ", options=list(manager.op_typen.keys()))
    saal_id = st.selectbox("Saal", options=list(manager.saele.keys()))
    uhrzeit = st.time_input("Startzeit", value=datetime.time(8, 0), step=600)  # step=600s = 10 Min.

    abschicken = st.form_submit_button("OP einplanen")

    if abschicken:
        start_minute = uhrzeit_zu_minute(uhrzeit)
        if not op_name:
            st.error("Bitte eine Bezeichnung für die Buchung eingeben.")
        elif start_minute < 0:
            st.error("Startzeit darf nicht vor Schichtbeginn (08:00) liegen.")
        else:
            try:
                manager.plane_operation(
                    op_name=op_name,
                    op_typ_name=op_typ_name,
                    saal_id=saal_id,
                    start_minute=start_minute
                )
                st.success(f"'{op_name}' erfolgreich in {saal_id} eingeplant!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

st.header("OP verschieben / Dauer anpassen")

# Alle aktuell geplanten OPs über alle Säle hinweg sammeln, damit man sie auswählen kann
alle_ops = []
for saal_id, saal in manager.saele.items():
    for op in saal.geplante_ops:
        alle_ops.append((saal_id, op))

if not alle_ops:
    st.info("Noch keine OPs geplant, die angepasst werden könnten.")
else:
    anzeige_namen = [f"{op.op_name} ({saal_id}, aktuell {minute_zu_uhrzeit(op.start_minute)}-{minute_zu_uhrzeit(op.end_minute)} Uhr)" 
                      for saal_id, op in alle_ops]
    auswahl_index = st.selectbox(
        "Welche OP anpassen?", 
        options=range(len(alle_ops)), 
        format_func=lambda i: anzeige_namen[i]
    )
    gewaehlter_saal_id, gewaehlte_op = alle_ops[auswahl_index]
    aktuelle_dauer = gewaehlte_op.end_minute - gewaehlte_op.start_minute

    neue_dauer = st.number_input(
        "Neue Dauer (Minuten)", 
        min_value=1, 
        value=aktuelle_dauer, 
        step=5
    )

    if st.button("Anpassung übernehmen"):
        try:
            manager.verschiebe_op(gewaehlter_saal_id, gewaehlte_op.op_name, int(neue_dauer))
            st.success(f"'{gewaehlte_op.op_name}' erfolgreich angepasst!")
            st.rerun()
        except ValueError as e:
            st.error(str(e))