import base64
import json
import math
from pathlib import Path

import streamlit as st

# ─── Configuration ────────────────────────────────────────────────────────────

TEAMS = [
    "🔥 Orange",
    "🍎 Red",
    "🌿 Green",
    "💎 Blue",
]

GROUPS: dict[str, list[dict]] = {
    "Group 1": [
        {"name": "Constance", "team": "🍎 Red"},
        {"name": "Shayan", "team": "🔥 Orange"},
        {"name": "Paula", "team": "🌿 Green"},
        {"name": "Daniel H", "team": "💎 Blue"},
    ],
    "Group 2": [
        {"name": "Ruben", "team": "🍎 Red"},
        {"name": "Wallis", "team": "🔥 Orange"},
        {"name": "Lena", "team": "🌿 Green"},
        {"name": "Sara", "team": "💎 Blue"},
    ],
    "Group 3": [
        {"name": "Katy", "team": "🍎 Red"},
        {"name": "Claire", "team": "🔥 Orange"},
        {"name": "Stef", "team": "🌿 Green"},
        {"name": "Iana", "team": "💎 Blue"},
    ],
    "Group 4": [
        {"name": "Melanie", "team": "🍎 Red"},
        {"name": "Vilem", "team": "🔥 Orange"},
        {"name": "Adam", "team": "🌿 Green"},
        {"name": "Michael R", "team": "💎 Blue"},
    ],
    "Group 5": [
        {"name": "Robbert", "team": "🍎 Red"},
        {"name": "Lucas", "team": "🔥 Orange"},
        {"name": "Roxane", "team": "🌿 Green"},
        {"name": "Nahin", "team": "💎 Blue"},
    ],
    "Group 6": [
        {"name": "Toby", "team": "🍎 Red"},
        {"name": "Paul", "team": "🔥 Orange"},
        {"name": "Emanuele", "team": "🌿 Green"},
        {"name": "Jessica", "team": "💎 Blue"},
    ],
}

EVENTS = [
    "Precision Balance",
    "Parafilm Resistance",
    "Plate Pouring",
    "Standard Curve",
    "Inventory Hunt",
    "Autoclave Load",
]

EVENT_ICON_FILES = {
    "Precision Balance": "balance.png",
    "Parafilm Resistance": "parafilm.png",
    "Plate Pouring": "plates.png",
    "Standard Curve": "standard.png",
    "Inventory Hunt": "inventory.png",
    "Autoclave Load": "autoclave.png",
}

# type="int" → number_input; omitted → text_input
EVENT_RESULT_FIELDS: dict[str, list[dict]] = {
    "Precision Balance": [
        {"key": "weight_g", "label": "Weight (g)"},
        {"key": "volume_mL", "label": "Volume (mL)"},
    ],
    "Parafilm Resistance": [
        {"key": "length_cm", "label": "Length (cm)"},
    ],
    "Plate Pouring": [
        {"key": "plate1_g", "label": "Plate 1 (g)"},
        {"key": "plate2_g", "label": "Plate 2 (g)"},
        {"key": "plate3_g", "label": "Plate 3 (g)"},
    ],
    "Standard Curve": [
        {"key": "r_squared", "label": "R²"},
    ],
    "Inventory Hunt": [
        {
            "key": "items_correct",
            "label": "Items correct",
            "type": "int",
            "min": 0,
            "max": 3,
        },
        {"key": "total_scanned", "label": "Total scanned", "type": "int", "min": 0},
        {"key": "time_minsec", "label": "Time"},
    ],
    "Autoclave Load": [
        {"key": "time_minsec", "label": "Time"},
        {"key": "quality", "label": "Quality", "type": "int", "min": 0, "max": 3},
    ],
}

PLACE_POINTS = {1: 4, 2: 3, 3: 2, 4: 1}
RANK_MEDALS = ["🥇", "🥈", "🥉", "4️⃣"]

ASSETS_DIR = Path(__file__).parent
SCORES_FILE = ASSETS_DIR / "scores.json"

OLYMPIC_RECORDS = [
    {
        "event": "Precision Balance",
        "holder": "Gino",
        "result": "Δ Weight: 0.0327 g | Δ Volume: 0.77 mL",
    },
    {"event": "Parafilm Resistance", "holder": "Gino", "result": "Length (cm): 25.8"},
    {
        "event": "Plate Pouring",
        "holder": "Noé",
        "result": "Standard Deviation: 0.708 g",
    },
    {"event": "Standard Curve", "holder": "Daniel D", "result": "R²: 0.9827"},
    {
        "event": "Inventory Hunt",
        "holder": "Nicolo",
        "result": "Correct items: 3/3 | Time 0:32",
    },
    {
        "event": "Autoclave Load",
        "holder": "Michelle",
        "result": "Time: 1:04 | Quality 3/3",
    },
]

# ─── Scoring ──────────────────────────────────────────────────────────────────


def _parse_minsec(s: str) -> float:
    parts = str(s).strip().split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    raise ValueError(f"Cannot parse time: {s!r}")


def _score_parafilm(raw: dict) -> dict:
    out = {}
    for name, r in raw.items():
        try:
            out[name] = float(r.get("length_cm") or 0)
        except (ValueError, TypeError):
            out[name] = 0.0
    return out  # higher is better


def _score_balance(raw: dict) -> dict:
    out = {}
    for name, r in raw.items():
        try:
            w = float(r.get("weight_g") or 0)
            v = float(r.get("volume_mL") or 0)
            out[name] = abs(w - 1.1111) + abs(v - 20.0)
        except (ValueError, TypeError):
            out[name] = float("inf")
    return out  # lower is better


def _score_plate_pouring(raw: dict) -> dict:
    out = {}
    for name, r in raw.items():
        try:
            plates = [float(r.get(f"plate{i}_g") or 0) for i in range(1, 4)]
            mean = sum(plates) / 3
            out[name] = math.sqrt(
                sum((p - mean) ** 2 for p in plates) / 2
            )  # sample std dev
        except (ValueError, TypeError):
            out[name] = float("inf")
    return out  # lower is better


def _score_autoclave(raw: dict) -> dict:
    out = {}
    for name, r in raw.items():
        try:
            secs = _parse_minsec(r.get("time_minsec") or "99:99")
            quality = min(3, max(0, int(r.get("quality") or 0)))
            out[name] = secs + (3 - quality) * 20
        except (ValueError, TypeError):
            out[name] = float("inf")
    return out  # lower is better


def _score_inventory(raw: dict) -> dict:
    out = {}
    for name, r in raw.items():
        try:
            correct = min(3, max(0, int(r.get("items_correct") or 0)))
            scanned = max(0, int(r.get("total_scanned") or 0))
            secs = _parse_minsec(r.get("time_minsec") or "2:30")
            out[name] = (
                correct * 2
                - max(0, scanned - 3)
                + max(0, math.floor((150 - secs) / 30))
            )
        except (ValueError, TypeError):
            out[name] = 0.0
    return out  # higher is better


def _score_standard_curve(raw: dict) -> dict:
    out = {}
    for name, r in raw.items():
        try:
            out[name] = float(r.get("r_squared") or 0)
        except (ValueError, TypeError):
            out[name] = 0.0
    return out  # higher is better


_SCORE_FN = {
    "Precision Balance": _score_balance,
    "Parafilm Resistance": _score_parafilm,
    "Plate Pouring": _score_plate_pouring,
    "Standard Curve": _score_standard_curve,
    "Inventory Hunt": _score_inventory,
    "Autoclave Load": _score_autoclave,
}

_HIGHER_IS_BETTER: dict[str, bool] = {
    "Precision Balance": False,
    "Parafilm Resistance": True,
    "Plate Pouring": False,
    "Standard Curve": True,
    "Inventory Hunt": True,
    "Autoclave Load": False,
}


def calculate_placements(event: str, raw: dict[str, dict]) -> dict[str, int]:
    fn = _SCORE_FN.get(event)
    if not fn:
        return {}
    scores_map = fn(raw)
    valid = {n: s for n, s in scores_map.items() if s != float("inf")}
    if not valid:
        return {}
    higher = _HIGHER_IS_BETTER[event]
    ranked = sorted(valid, key=lambda n: valid[n], reverse=higher)
    return {name: i + 1 for i, name in enumerate(ranked)}


# ─── Data helpers ─────────────────────────────────────────────────────────────


def _gist_config() -> dict | None:
    if "github" not in st.secrets:
        return None
    gh = st.secrets["github"]
    return {
        "token": gh["token"],
        "gist_id": gh["gist_id"],
        "filename": gh.get("filename", "scores.json"),
    }


def _gist_load() -> str:
    import requests

    cfg = _gist_config()
    r = requests.get(
        f"https://api.github.com/gists/{cfg['gist_id']}",
        headers={
            "Authorization": f"Bearer {cfg['token']}",
            "Accept": "application/vnd.github+json",
        },
        timeout=10,
    )
    r.raise_for_status()
    f = r.json().get("files", {}).get(cfg["filename"])
    return f.get("content", "") if f else ""


def _gist_save(content: str) -> None:
    import requests

    cfg = _gist_config()
    r = requests.patch(
        f"https://api.github.com/gists/{cfg['gist_id']}",
        headers={
            "Authorization": f"Bearer {cfg['token']}",
            "Accept": "application/vnd.github+json",
        },
        json={"files": {cfg["filename"]: {"content": content}}},
        timeout=10,
    )
    r.raise_for_status()


def load_scores() -> dict:
    if _gist_config() is not None:
        raw = _gist_load().strip()
        data = json.loads(raw) if raw else {}
    elif SCORES_FILE.exists():
        with open(SCORES_FILE) as f:
            data = json.load(f)
    else:
        return {}
    cleaned = {}
    for event, ev_data in data.items():
        if not isinstance(ev_data, dict):
            continue
        # Discard old flat-format events (keys "1"–"4")
        if any(str(k).isdigit() for k in ev_data):
            continue
        # Discard old-format Inventory Hunt groups (no is_finalist key → pre-bracket format)
        if event == "Inventory Hunt":
            ev_data = {
                g: gd
                for g, gd in ev_data.items()
                if isinstance(gd, dict)
                and any(isinstance(d, dict) and "is_finalist" in d for d in gd.values())
            }
            if not ev_data:
                continue
        cleaned[event] = ev_data
    return cleaned


def save_scores(scores: dict) -> None:
    payload = json.dumps(scores, indent=2)
    if _gist_config() is not None:
        _gist_save(payload)
        return
    with open(SCORES_FILE, "w") as f:
        f.write(payload)


def get_standings(scores: dict):
    totals = {t: 0 for t in TEAMS}
    wins = {t: 0 for t in TEAMS}
    for groups in scores.values():
        if not isinstance(groups, dict):
            continue
        for persons in groups.values():
            if not isinstance(persons, dict):
                continue
            for data in persons.values():
                if not isinstance(data, dict):
                    continue
                team = data.get("team")
                place = data.get("place")
                if team in totals and isinstance(place, int):
                    totals[team] += PLACE_POINTS.get(place, 0)
                    if place == 1:
                        wins[team] += 1
    ranked = sorted(TEAMS, key=lambda t: (-totals[t], -wins[t]))
    return ranked, totals, wins


def _event_team_points(event: str, scores: dict) -> dict[str, int]:
    pts = {t: 0 for t in TEAMS}
    for persons in scores.get(event, {}).values():
        if not isinstance(persons, dict):
            continue
        for data in persons.values():
            if not isinstance(data, dict):
                continue
            team = data.get("team")
            place = data.get("place")
            if team in pts and isinstance(place, int):
                pts[team] += PLACE_POINTS.get(place, 0)
    return pts


# ─── Asset helpers ────────────────────────────────────────────────────────────


@st.cache_data
def _b64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _event_html(event: str, size: int = 24) -> str:
    fname = EVENT_ICON_FILES.get(event)
    icon = ""
    if fname:
        path = ASSETS_DIR / fname
        if path.exists():
            ext = path.suffix.lstrip(".")
            icon = (
                f'<img src="data:image/{ext};base64,{_b64(path)}" '
                f'height="{size}" style="vertical-align:middle;margin-right:6px;">'
            )
    return f'{icon}<span style="vertical-align:middle">{event}</span>'


def _bg_css() -> str:
    path = ASSETS_DIR / "gradient-dark.jpg"
    b64 = _b64(path)
    return f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("data:image/jpeg;base64,{b64}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}
[data-testid="stHeader"] {{ background: transparent; }}
</style>
"""


def _lb_css() -> str:
    return """
<style>
.lb-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-top: 0.5rem;
}
.lb-box {
    background-color: #1a2a4a;
    border: 1px solid #2d4a7a;
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    color: white;
}
.lb-box h3 {
    margin: 0 0 0.8rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: white;
}
.lb-table {
    width: 100%;
    border-collapse: collapse;
}
.lb-table th {
    text-align: left;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 0.25rem 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.25);
    color: rgba(255,255,255,0.65);
}
.lb-table td {
    padding: 0.35rem 0.5rem;
    font-size: 0.9rem;
    color: white;
    vertical-align: middle;
}
.lb-table tbody tr:not(:last-child) td {
    border-bottom: 1px solid rgba(255,255,255,0.08);
}
.lb-metrics {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
}
.lb-metric-label { font-size: 0.8rem; color: rgba(255,255,255,0.65); }
.lb-metric-value { font-size: 1.5rem; font-weight: 700; color: white; }
.lb-metric-delta { font-size: 0.78rem; color: rgba(255,255,255,0.55); }
.lb-empty { color: rgba(255,255,255,0.5); font-size: 0.85rem; margin: 0; }
.lb-table-lg th { font-size: 1rem; padding: 0.4rem 0.6rem; }
.lb-table-lg td { font-size: 1.2rem; padding: 0.75rem 0.6rem; }
</style>
"""


# ─── Leaderboard page ─────────────────────────────────────────────────────────


def page_leaderboard(scores: dict) -> None:
    st.title("🏅 Lab Olympics 2026")

    # total_slots = len(EVENTS) * len(GROUPS)
    # done_slots = sum(
    #     1
    #     for groups in scores.values()
    #     if isinstance(groups, dict)
    #     for persons in groups.values()
    #     if isinstance(persons, dict) and persons
    # )
    # st.caption(f"{done_slots} / {total_slots} group slots completed")

    ranked, totals, wins = get_standings(scores)

    # ── Standings (combined points + rank) ────────────────────────────────────
    standings_rows = "".join(
        f"<tr><td>{RANK_MEDALS[i]}</td><td>{team}</td>"
        f"<td><strong>{totals[team]}</strong></td><td>{wins[team]}</td></tr>"
        for i, team in enumerate(ranked)
    )

    # ── Olympic Records ────────────────────────────────────────────────────────
    records_rows = "".join(
        f"<tr><td>{_event_html(r['event'], 18)}</td>"
        f"<td>{r['holder']}</td><td>{r['result']}</td></tr>"
        for r in OLYMPIC_RECORDS
    )

    # ── Event Results: per-event team point totals ─────────────────────────────
    team_headers = "".join(f"<th>{t}</th>" for t in TEAMS)
    event_rows = ""
    for event in EVENTS:
        pts = _event_team_points(event, scores)
        n_groups = len(scores.get(event, {}))
        event_rows += "<tr><td>{}</td>{}<td>{}/6</td></tr>".format(
            _event_html(event, 20),
            "".join(f"<td>{pts[t]}</td>" for t in TEAMS),
            n_groups,
        )

    # ── Best Results: best individual per event across all groups ──────────────
    best_entries = []
    for event in EVENTS:
        groups = scores.get(event, {})
        if not groups:
            continue

        # Inventory Hunt uses bracket data — finalists ranked by final scores
        if event == "Inventory Hunt":
            finalist_raw: dict[str, dict] = {}
            finalist_team: dict[str, str] = {}
            for persons in groups.values():
                if not isinstance(persons, dict):
                    continue
                for name, data in persons.items():
                    if (
                        isinstance(data, dict)
                        and data.get("is_finalist")
                        and data.get("final_time_minsec")
                    ):
                        finalist_raw[name] = {
                            "items_correct": str(data.get("final_items_correct", 0)),
                            "total_scanned": str(data.get("final_total_scanned", 0)),
                            "time_minsec": data.get("final_time_minsec", ""),
                        }
                        finalist_team[name] = data.get("team", "")
            if finalist_raw:
                try:
                    placements = calculate_placements(event, finalist_raw)
                    first = [n for n, p in placements.items() if p == 1]
                    if first:
                        best_name = first[0]
                        d = finalist_raw[best_name]
                        result_str = (
                            f"Correct items: {d['items_correct']}/{d['total_scanned']} | "
                            f"Time: {d['time_minsec']}"
                        )
                        best_entries.append(
                            (event, best_name, finalist_team[best_name], result_str)
                        )
                except Exception:
                    pass
            continue

        all_raw: dict[str, dict] = {}
        name_to_team: dict[str, str] = {}
        for persons in groups.values():
            if not isinstance(persons, dict):
                continue
            for name, data in persons.items():
                if isinstance(data, dict):
                    all_raw[name] = {
                        k: v for k, v in data.items() if k not in ("place", "team")
                    }
                    name_to_team[name] = data.get("team", "")
        if not all_raw:
            continue
        try:
            placements = calculate_placements(event, all_raw)
            first = [n for n, p in placements.items() if p == 1]
            if first:
                best_name = first[0]
                d = all_raw[best_name]
                if event == "Inventory Hunt":
                    result_str = (
                        f"Correct items: {d.get('items_correct', '')}/{d.get('total_scanned', '')} | "
                        f"Time: {d.get('time_minsec', '')}"
                    )
                elif event == "Precision Balance":
                    try:
                        w_off = float(d.get("weight_g") or 0) - 1.1111
                        v_off = float(d.get("volume_mL") or 0) - 20.0
                        result_str = (
                            f"Δ Weight: {w_off:+.4f} g | Δ Volume: {v_off:+.2f} mL"
                        )
                    except (ValueError, TypeError):
                        result_str = ""
                elif event == "Plate Pouring":
                    try:
                        plates = [float(d.get(f"plate{i}_g") or 0) for i in range(1, 4)]
                        mean = sum(plates) / 3
                        std = math.sqrt(sum((p - mean) ** 2 for p in plates) / 2)
                        result_str = f"Standard Deviation: {std:.3f} g"
                    except (ValueError, TypeError):
                        result_str = ""
                elif event == "Autoclave Load":
                    result_str = (
                        f"Time: {d.get('time_minsec', '')} | "
                        f"Quality: {d.get('quality', '')}/3"
                    )
                else:
                    fields_ev = EVENT_RESULT_FIELDS.get(event) or []
                    result_str = " | ".join(
                        f"{f['label']}: {d.get(f['key'], '')}"
                        for f in fields_ev
                        if d.get(f["key"])
                    )
                best_entries.append(
                    (event, best_name, name_to_team[best_name], result_str)
                )
        except Exception:
            continue

    if best_entries:
        best_rows = "".join(
            f"<tr><td>{_event_html(ev, 20)}</td><td>{name}</td><td>{team}</td><td>{result}</td></tr>"
            for ev, name, team, result in best_entries
        )
        best_content = (
            "<table class='lb-table'>"
            "<thead><tr><th>Event</th><th>Player</th><th>Team</th><th>Result</th></tr></thead>"
            f"<tbody>{best_rows}</tbody></table>"
        )
    else:
        best_content = "<p class='lb-empty'>No results recorded yet.</p>"

    st.html(
        _lb_css()
        + f"""
<div class="lb-grid">
  <div class="lb-box">
    <h3>Standings</h3>
    <table class="lb-table lb-table-lg">
      <thead><tr><th>Rank</th><th>Team</th><th>Points</th><th>Wins</th></tr></thead>
      <tbody>{standings_rows}</tbody>
    </table>
  </div>
  <div class="lb-box">
    <h3>🏆 Olympic Records</h3>
    <table class="lb-table">
      <thead><tr><th>Event</th><th>Holder</th><th>Result</th></tr></thead>
      <tbody>{records_rows}</tbody>
    </table>
  </div>
  <div class="lb-box">
    <h3>Event Results</h3>
    <table class="lb-table">
      <thead><tr><th>Event</th>{team_headers}<th>Groups</th></tr></thead>
      <tbody>{event_rows}</tbody>
    </table>
  </div>
  <div class="lb-box">
    <h3>🌟 Best Results</h3>
    {best_content}
  </div>
</div>"""
    )


# ─── Inventory Hunt bracket UI ────────────────────────────────────────────────


def _page_referee_inventory(
    scores: dict, event: str, group: str, participants: list, existing_group: dict
) -> None:
    inv_fields = EVENT_RESULT_FIELDS["Inventory Hunt"]
    names = [p["name"] for p in participants]
    p_by_name = {p["name"]: p for p in participants}
    finalists_key = f"inv_{group}_finalists"

    st.subheader(f"{event} — {group}")

    # ── Already saved: show summary + clear ───────────────────────────────────
    if existing_group:
        saved = sorted(
            [
                (n, d)
                for n, d in existing_group.items()
                if isinstance(d, dict) and "place" in d
            ],
            key=lambda x: x[1]["place"],
        )
        for name, data in saved:
            place = data.get("place", "?")
            medal = (
                RANK_MEDALS[place - 1]
                if isinstance(place, int) and 1 <= place <= 4
                else "?"
            )
            if data.get("is_finalist"):
                result = f"Final — {data.get('final_items_correct', '')}/{data.get('final_total_scanned', '')} items, {data.get('final_time_minsec', '')}"
            else:
                result = f"Semi — {data.get('semi_items_correct', '')}/{data.get('semi_total_scanned', '')} items, {data.get('semi_time_minsec', '')}"
            st.markdown(f"{medal} **{name}** ({data.get('team', '')}) — {result}")
        st.divider()
        if st.button("Clear results", type="secondary"):
            st.session_state.pop(finalists_key, None)
            scores.get(event, {}).pop(group, None)
            if not scores.get(event):
                scores.pop(event, None)
            save_scores(scores)
            st.info(f"Cleared {event} — {group}.")
            st.rerun()
        return

    col_w = [2] + [1] * len(inv_fields)
    in_final_stage = finalists_key in st.session_state

    # ── Semifinal inputs ───────────────────────────────────────────────────────
    for i, pair in enumerate([participants[:2], participants[2:]]):
        st.markdown(f"**Semifinal {i + 1}**")
        hdr = st.columns(col_w)
        hdr[0].markdown("**Participant**")
        for j, f in enumerate(inv_fields):
            hdr[1 + j].markdown(f"**{f['label']}**")
        for p in pair:
            row = st.columns(col_w)
            row[0].markdown(f"{p['name']} {p['team']}")
            for j, f in enumerate(inv_fields):
                wkey = f"inv_semi_{group}_{p['name']}_{f['key']}"
                if f.get("type") == "int":
                    row[1 + j].number_input(
                        f["label"],
                        label_visibility="collapsed",
                        min_value=f.get("min", 0),
                        max_value=f.get("max", 999),
                        key=wkey,
                        disabled=in_final_stage,
                    )
                else:
                    row[1 + j].text_input(
                        f["label"],
                        label_visibility="collapsed",
                        placeholder=f["label"],
                        key=wkey,
                        disabled=in_final_stage,
                    )

    st.divider()

    if not in_final_stage:
        # ── Submit semis button ────────────────────────────────────────────────
        semi_time_filled = all(
            str(
                st.session_state.get(f"inv_semi_{group}_{p['name']}_{f['key']}", "")
            ).strip()
            != ""
            for p in participants
            for f in inv_fields
            if f.get("type") != "int"
        )
        if st.button("Submit semis →", type="primary", disabled=not semi_time_filled):
            semi_raw = {
                p["name"]: {
                    f["key"]: str(
                        st.session_state.get(
                            f"inv_semi_{group}_{p['name']}_{f['key']}", ""
                        )
                    )
                    for f in inv_fields
                }
                for p in participants
            }
            semi_scores = _score_inventory(semi_raw)
            winner1 = max(
                [participants[0]["name"], participants[1]["name"]],
                key=lambda n: semi_scores.get(n, 0),
            )
            winner2 = max(
                [participants[2]["name"], participants[3]["name"]],
                key=lambda n: semi_scores.get(n, 0),
            )
            st.session_state[finalists_key] = [winner1, winner2]
            st.rerun()
        return

    # ── Final stage ────────────────────────────────────────────────────────────
    finalists = st.session_state[finalists_key]
    st.markdown(f"**Final** — {finalists[0]} vs {finalists[1]}")

    hdr = st.columns(col_w)
    hdr[0].markdown("**Participant**")
    for j, f in enumerate(inv_fields):
        hdr[1 + j].markdown(f"**{f['label']}**")

    for fn in finalists:
        p = p_by_name[fn]
        row = st.columns(col_w)
        row[0].markdown(f"{fn} {p['team']}")
        for j, f in enumerate(inv_fields):
            wkey = f"inv_final_{group}_{fn}_{f['key']}"
            if f.get("type") == "int":
                row[1 + j].number_input(
                    f["label"],
                    label_visibility="collapsed",
                    min_value=f.get("min", 0),
                    max_value=f.get("max", 999),
                    key=wkey,
                )
            else:
                row[1 + j].text_input(
                    f["label"],
                    label_visibility="collapsed",
                    placeholder=f["label"],
                    key=wkey,
                )

    st.divider()

    final_time_filled = all(
        str(st.session_state.get(f"inv_final_{group}_{fn}_{f['key']}", "")).strip()
        != ""
        for fn in finalists
        for f in inv_fields
        if f.get("type") != "int"
    )

    sc1, sc2 = st.columns(2)
    with sc1:
        if st.button(
            "Save final results",
            type="primary",
            use_container_width=True,
            disabled=not final_time_filled,
        ):
            semi_raw = {
                p["name"]: {
                    f["key"]: str(
                        st.session_state.get(
                            f"inv_semi_{group}_{p['name']}_{f['key']}", ""
                        )
                    )
                    for f in inv_fields
                }
                for p in participants
            }
            final_raw = {
                fn: {
                    f["key"]: str(
                        st.session_state.get(f"inv_final_{group}_{fn}_{f['key']}", "")
                    )
                    for f in inv_fields
                }
                for fn in finalists
            }
            semi_scores = _score_inventory(semi_raw)
            final_scores = _score_inventory(final_raw)
            non_finalists = [n for n in names if n not in finalists]
            non_finalists_ranked = sorted(
                non_finalists, key=lambda n: semi_scores.get(n, 0), reverse=True
            )
            finalists_ranked = sorted(
                finalists, key=lambda n: final_scores.get(n, 0), reverse=True
            )
            places = {
                finalists_ranked[0]: 1,
                finalists_ranked[1]: 2,
                non_finalists_ranked[0]: 3,
                non_finalists_ranked[1]: 4,
            }
            group_data = {}
            for p in participants:
                n = p["name"]
                is_f = n in finalists
                entry = {
                    **{f"semi_{f['key']}": semi_raw[n][f["key"]] for f in inv_fields},
                    "place": places.get(n),
                    "team": p["team"],
                    "is_finalist": is_f,
                }
                if is_f:
                    entry.update(
                        {
                            f"final_{f['key']}": final_raw[n][f["key"]]
                            for f in inv_fields
                        }
                    )
                group_data[n] = entry
            scores.setdefault(event, {})[group] = group_data
            save_scores(scores)
            st.session_state.pop(finalists_key, None)
            for p in participants:
                for f in inv_fields:
                    st.session_state.pop(
                        f"inv_semi_{group}_{p['name']}_{f['key']}", None
                    )
                    st.session_state.pop(
                        f"inv_final_{group}_{p['name']}_{f['key']}", None
                    )
            st.success(f"Saved {event} — {group}!")
            st.rerun()

    with sc2:
        if st.button("← Redo semis", type="secondary", use_container_width=True):
            st.session_state.pop(finalists_key, None)
            st.rerun()


# ─── Referee page ─────────────────────────────────────────────────────────────


def page_referee(scores: dict) -> None:
    st.title("📋 Referee Panel")

    col_ev, col_gr = st.columns(2)
    event = col_ev.selectbox("Event", EVENTS)
    group = col_gr.selectbox("Group", list(GROUPS.keys()))

    participants = GROUPS[group]
    existing_group = scores.get(event, {}).get(group, {})

    if event == "Inventory Hunt":
        _page_referee_inventory(scores, event, group, participants, existing_group)
        return

    fields = EVENT_RESULT_FIELDS.get(event) or []

    # Initialise session state from saved data whenever event/group changes
    state_ctx = f"{event}||{group}"
    if st.session_state.get("_ref_ctx") != state_ctx:
        st.session_state["_ref_ctx"] = state_ctx
        for p in participants:
            for f in fields:
                wkey = f"ref_{event}_{group}_{p['name']}_{f['key']}"
                saved = existing_group.get(p["name"], {}).get(f["key"], "")
                st.session_state[wkey] = (
                    int(saved)
                    if (f.get("type") == "int" and saved != "")
                    else (0 if f.get("type") == "int" else str(saved))
                )

    # Read current widget values for live placement preview
    raw_inputs: dict[str, dict] = {}
    for p in participants:
        row = {
            f["key"]: str(
                st.session_state.get(f"ref_{event}_{group}_{p['name']}_{f['key']}", "")
            )
            for f in fields
        }
        if any(v for v in row.values()):
            raw_inputs[p["name"]] = row

    live_places: dict[str, int] = {}
    if raw_inputs:
        try:
            live_places = calculate_placements(event, raw_inputs)
        except Exception:
            pass

    # ── Input table ───────────────────────────────────────────────────────────
    st.subheader(f"{event} — {group}")

    col_w = [1, 2] + [1] * len(fields)
    hdr = st.columns(col_w)
    hdr[0].markdown("**Place**")
    hdr[1].markdown("**Participant**")
    for j, f in enumerate(fields):
        hdr[2 + j].markdown(f"**{f['label']}**")

    st.divider()

    for p in participants:
        name = p["name"]
        place = live_places.get(name)
        medal = RANK_MEDALS[place - 1] if place else "—"
        row = st.columns(col_w)
        row[0].markdown(medal)
        row[1].markdown(f"{name} {p['team']}")
        for j, f in enumerate(fields):
            wkey = f"ref_{event}_{group}_{name}_{f['key']}"
            if f.get("type") == "int":
                row[2 + j].number_input(
                    f["label"],
                    label_visibility="collapsed",
                    min_value=f.get("min", 0),
                    max_value=f.get("max", 999),
                    key=wkey,
                )
            else:
                row[2 + j].text_input(
                    f["label"],
                    label_visibility="collapsed",
                    placeholder=f["label"],
                    key=wkey,
                )

    st.divider()

    # ── Save / Clear ──────────────────────────────────────────────────────────
    # Disable save until every text field (non-int) has a non-empty value
    all_filled = all(
        str(
            st.session_state.get(f"ref_{event}_{group}_{p['name']}_{f['key']}", "")
        ).strip()
        != ""
        for p in participants
        for f in fields
        if f.get("type") != "int"
    )

    sc1, sc2 = st.columns(2)
    with sc1:
        if st.button(
            "Save results",
            type="primary",
            use_container_width=True,
            disabled=not all_filled,
        ):
            final_raw = {
                p["name"]: {
                    f["key"]: st.session_state.get(
                        f"ref_{event}_{group}_{p['name']}_{f['key']}", ""
                    )
                    for f in fields
                }
                for p in participants
            }
            placements = calculate_placements(
                event,
                {n: {k: str(v) for k, v in r.items()} for n, r in final_raw.items()},
            )
            scores.setdefault(event, {})[group] = {
                p["name"]: {
                    **{f["key"]: final_raw[p["name"]][f["key"]] for f in fields},
                    "place": placements.get(p["name"]),
                    "team": p["team"],
                }
                for p in participants
            }
            save_scores(scores)
            # Clear inputs after saving — delete widget keys so they reset to defaults
            for p in participants:
                for f in fields:
                    wkey = f"ref_{event}_{group}_{p['name']}_{f['key']}"
                    st.session_state.pop(wkey, None)
            st.success(f"Saved {event} — {group}!")
            st.rerun()

    with sc2:
        if existing_group and st.button(
            "Clear results", type="secondary", use_container_width=True
        ):
            st.session_state["_ref_ctx"] = None  # force re-init on next render
            scores.get(event, {}).pop(group, None)
            if not scores.get(event):
                scores.pop(event, None)
            save_scores(scores)
            st.info(f"Cleared {event} — {group}.")
            st.rerun()


# ─── App entry point ──────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Lab Olympics",
    page_icon="🏅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(_bg_css(), unsafe_allow_html=True)

scores = load_scores()

tab_lb, tab_ref = st.tabs(["🏆 Leaderboard", "📋 Referee"])

with tab_lb:
    page_leaderboard(scores)

with tab_ref:
    page_referee(scores)
