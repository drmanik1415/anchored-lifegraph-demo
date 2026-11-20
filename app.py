"""Anchored LifeGraph: entirely fictional UAE family records; public demo only."""
import sqlite3
import streamlit as st

st.set_page_config(page_title="Anchored | LifeGraph Demo", page_icon="🌳", layout="wide")

@st.cache_resource
def placeholder():
    return True

def make_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript("""
    CREATE TABLE people (id TEXT PRIMARY KEY, name TEXT NOT NULL, relationship TEXT NOT NULL, notes TEXT NOT NULL);
    CREATE TABLE events (id TEXT PRIMARY KEY, title TEXT NOT NULL, event_date TEXT NOT NULL, place TEXT NOT NULL, source TEXT NOT NULL);
    CREATE TABLE event_people (event_id TEXT REFERENCES events(id), person_id TEXT REFERENCES people(id));
    CREATE TABLE facts (id TEXT PRIMARY KEY, person_id TEXT REFERENCES people(id), fact TEXT NOT NULL, source TEXT NOT NULL, permitted INTEGER NOT NULL);
    CREATE TABLE audit (id INTEGER PRIMARY KEY, action TEXT, result TEXT, at TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    conn.executemany("INSERT INTO people VALUES (?,?,?,?)", [
        ("aisha", "Aisha", "self", "Memory owner (fictional)"),
        ("mohammed", "Mohammed", "son", "Trusted family contact"),
        ("maryam", "Maryam", "daughter", "Enjoys gardening"),
        ("fatima", "Fatima", "granddaughter", "Enjoys drawing"),
        ("khalid", "Khalid", "friend", "Longtime family friend")
    ])
    conn.executemany("INSERT INTO events VALUES (?,?,?,?,?)", [
        ("v1", "Fatima visits Aisha", "2026-11-20", "Aisha's home", "Fictional approved family calendar"),
        ("v2", "Garden afternoon", "2026-11-21", "Neighbourhood garden", "Fictional approved family calendar"),
        ("v3", "Family gathering", "2026-12-02", "Community centre", "Fictional approved family calendar")
    ])
    conn.executemany("INSERT INTO event_people VALUES (?,?)", [
        ("v1", "fatima"), ("v1", "aisha"),
        ("v2", "maryam"), ("v2", "aisha"),
        ("v3", "mohammed"), ("v3", "aisha")
    ])
    conn.executemany("INSERT INTO facts VALUES (?,?,?,?,?)", [
        ("f1", "fatima", "Fatima enjoys drawing", "Fictional family-provided record", 1),
        ("f2", "aisha", "Aisha prefers brief written reminders", "Fictional user preference", 1),
        ("f3", "aisha", "RESTRICTED DEMO DETAIL", "Restricted fictional record", 0)
    ])
    conn.commit()
    return conn

def audit(conn, action, result):
    conn.execute("INSERT INTO audit(action,result) VALUES (?,?)", (action, result))
    conn.commit()

def search(conn, name, requester):
    if requester != "Aisha (record owner)":
        audit(conn, "search request", "DENIED")
        return {"status": "denied", "message": "Access denied for this simulated requester."}
    name = name.strip().lower()
    if not name:
        return {"status": "missing", "message": "Enter a person's name."}
    row = conn.execute("SELECT id,name,relationship,notes FROM people WHERE lower(name)=?", (name,)).fetchone()
    if not row:
        audit(conn, "search: " + name, "NOT FOUND")
        return {"status": "missing", "message": "No verified record found. Anchored will not invent a memory."}
    pid, person, relationship, notes = row
    facts = conn.execute("SELECT fact,source FROM facts WHERE person_id=? AND permitted=1", (pid,)).fetchall()
    events = conn.execute("""SELECT e.title,e.event_date,e.place,e.source FROM events e JOIN event_people ep ON ep.event_id=e.id WHERE ep.person_id=? ORDER BY e.event_date""", (pid,)).fetchall()
    audit(conn, "search: " + name, "FOUND")
    return {"status": "found", "person": person, "relationship": relationship, "notes": notes, "facts": facts, "events": events}

if "db" not in st.session_state:
    st.session_state.db = make_db()
conn = st.session_state.db

st.title("🌳 Anchored | LifeGraph")
st.caption("Fictional UAE family memory tree · Evidence-based retrieval · Simulated permissions · No medical advice")
st.info("Public prototype: all names and events are fictional. Authorization is simulated, not a real identity-verification system.")

with st.sidebar:
    st.subheader("Demonstration controls")
    requester = st.selectbox("Requester", ["Aisha (record owner)", "Unapproved caregiver"])
    st.caption("Changing requester simulates an access-control decision; it does not authenticate anyone.")
    st.markdown("**Suggested tests**")
    st.write("Fatima → approved family record")
    st.write("Unknown → no fabricated memory")
    st.write("Unapproved caregiver → denied")

left, right = st.columns([1.1, 1])
with left:
    st.subheader("Family memory tree")
    dot = '''digraph Family {
      graph [bgcolor="transparent", rankdir=TB, nodesep=0.5, ranksep=0.6];
      node [shape=box, style="rounded,filled", fontname="Arial", fillcolor="#e0f2fe", color="#64748b"];
      Aisha [shape=oval, fillcolor="#ccfbf1", penwidth=2];
      Aisha -> Mohammed [label="son"];
      Aisha -> Maryam [label="daughter"];
      Aisha -> Fatima [label="granddaughter"];
      Aisha -> Khalid [label="friend"];
    }'''
    st.graphviz_chart(dot, use_container_width=True)
    st.caption("Relationships are illustrative and manually entered—not AI-inferred.")

with right:
    st.subheader("Verified memory retrieval")
    query = st.text_input("Person's name", value="Fatima")
    if st.button("Retrieve approved memory", type="primary"):
        result = search(conn, query, requester)
        if result["status"] == "denied":
            st.error(result["message"])
        elif result["status"] != "found":
            st.warning(result["message"])
        else:
            st.success(f"{result['person']} — {result['relationship']} of Aisha")
            st.write(result["notes"])
            for fact, source in result["facts"]:
                st.write(f"**Fact:** {fact}")
                st.caption(f"Source: {source}")
            for title, date, place, source in result["events"]:
                st.write(f"**Event:** {title} — {date} at {place}")
                st.caption(f"Source: {source}")
    st.subheader("Fictional calendar")
    records = conn.execute("SELECT title,event_date,place FROM events ORDER BY event_date").fetchall()
    st.dataframe([{"Event": t, "Date": d, "Place": p} for t,d,p in records], hide_index=True, use_container_width=True)

st.divider()
a, b = st.columns([1, 1])
with a:
    st.subheader("Permission boundary")
    if st.button("Attempt to open restricted record"):
        audit(conn, "restricted fact", "DENIED")
        st.error("Access denied. The restricted record was not revealed.")
with b:
    st.subheader("Evidence and audit trail")
    with st.expander("Show recent decisions"):
        logs = conn.execute("SELECT action,result,at FROM audit ORDER BY id DESC LIMIT 20").fetchall()
        st.dataframe([{"Action": a, "Result": r, "Timestamp": t} for a,r,t in logs], hide_index=True, use_container_width=True)

st.caption("Anchored is an early research demo: no clinical validation, disease prediction, live monitoring, or autonomous agents are claimed.")
