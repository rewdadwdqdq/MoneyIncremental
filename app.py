import json
import random
import sqlite3
import time
import uuid
from datetime import date, datetime, timedelta

import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ============================================================
# MONEY SIMULATOR - Streamlit + SQLite
# Local single-server prototype. Player progress is saved in
# game_data.db beside this file.
# ============================================================

st.set_page_config(
    page_title="Money Simulator",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = "game_data.db"
SAVE_VERSION = 1
MAX_EQUIPPED = 3

WORLDS = [
    {"name": "Starter Island", "emoji": "🌴", "cost": 0, "egg_cost": 100, "theme": "starter"},
    {"name": "Desert Dunes", "emoji": "🏜️", "cost": 5_000, "egg_cost": 1_000, "theme": "desert"},
    {"name": "Volcano Valley", "emoji": "🌋", "cost": 100_000, "egg_cost": 15_000, "theme": "volcano"},
    {"name": "Frozen Peaks", "emoji": "❄️", "cost": 5_000_000, "egg_cost": 500_000, "theme": "ice"},
    {"name": "Galaxy Zone", "emoji": "🌌", "cost": 250_000_000, "egg_cost": 25_000_000, "theme": "galaxy"},
    {"name": "Cloud Kingdom", "emoji": "☁️", "cost": 10_000_000_000, "egg_cost": 1_000_000_000, "theme": "cloud"},
]

PETS = {
    "Starter Island": [
        ("Puppy", "Common", 1.15, 48),
        ("Kitten", "Common", 1.20, 25),
        ("Bunny", "Uncommon", 1.45, 16),
        ("Parrot", "Rare", 2.0, 8),
        ("Golden Golem", "Legendary", 4.0, 2.5),
        ("Island Phoenix", "Mythical", 8.0, 0.5),
    ],
    "Desert Dunes": [
        ("Fennec Fox", "Common", 1.5, 45),
        ("Scarab", "Uncommon", 1.9, 25),
        ("Sand Serpent", "Rare", 3.0, 18),
        ("Mummy Cat", "Legendary", 6.0, 10),
        ("Sun Dragon", "Mythical", 12.0, 2),
    ],
    "Volcano Valley": [
        ("Ember Cub", "Common", 2.0, 42),
        ("Magma Turtle", "Uncommon", 2.8, 27),
        ("Lava Hound", "Rare", 4.5, 19),
        ("Inferno Phoenix", "Legendary", 10.0, 10),
        ("Core Titan", "Mythical", 20.0, 2),
    ],
    "Frozen Peaks": [
        ("Snow Fox", "Common", 3.0, 42),
        ("Ice Penguin", "Uncommon", 4.0, 27),
        ("Frost Wolf", "Rare", 7.0, 19),
        ("Glacier Dragon", "Legendary", 15.0, 10),
        ("Aurora Spirit", "Mythical", 30.0, 2),
    ],
    "Galaxy Zone": [
        ("Moon Slime", "Common", 5.0, 42),
        ("Star Cat", "Uncommon", 7.0, 27),
        ("Comet Fox", "Rare", 12.0, 19),
        ("Nebula Dragon", "Legendary", 25.0, 10),
        ("Cosmic Giant", "Mythical", 50.0, 2),
    ],
    "Cloud Kingdom": [
        ("Cloud Puff", "Common", 8.0, 42),
        ("Sky Bunny", "Uncommon", 12.0, 27),
        ("Storm Eagle", "Rare", 20.0, 19),
        ("Heaven Dragon", "Legendary", 45.0, 10),
        ("Celestial", "Mythical", 100.0, 2),
    ],
}

RARITY_EMOJI = {
    "Common": "⚪", "Uncommon": "🟢", "Rare": "🔵",
    "Legendary": "🟠", "Mythical": "🟣", "Secret": "🌈",
}

QUESTS = [
    {"id": "clicks", "title": "Warm Up", "description": "Click 25 times", "target": 25, "reward": 250, "stat": "clicks"},
    {"id": "eggs", "title": "Pet Collector", "description": "Hatch 3 eggs", "target": 3, "reward": 500, "stat": "eggs_hatched"},
    {"id": "earned", "title": "First Fortune", "description": "Earn $5,000 in total", "target": 5000, "reward": 750, "stat": "total_earned"},
    {"id": "upgrades", "title": "Getting Stronger", "description": "Buy 3 upgrades", "target": 3, "reward": 600, "stat": "upgrades_bought"},
]

ACHIEVEMENTS = [
    {"id": "first_click", "title": "First Click", "description": "Make your first click", "stat": "clicks", "target": 1, "reward": 100},
    {"id": "click_100", "title": "Click Machine", "description": "Click 100 times", "stat": "clicks", "target": 100, "reward": 1000},
    {"id": "first_pet", "title": "New Friend", "description": "Hatch your first pet", "stat": "eggs_hatched", "target": 1, "reward": 250},
    {"id": "pet_10", "title": "Pet Party", "description": "Own 10 pets", "stat": "pets_hatched_total", "target": 10, "reward": 5000},
    {"id": "rich_10k", "title": "Pocket Money", "description": "Earn $10,000 total", "stat": "total_earned", "target": 10000, "reward": 2000},
    {"id": "rebirth_1", "title": "Fresh Start", "description": "Complete your first rebirth", "stat": "rebirths", "target": 1, "reward": 5000},
]

def new_player():
    return {
        "save_version": SAVE_VERSION,
        "money": 0.0,
        "gems": 0,
        "click_power": 1,
        "auto_power": 0,
        "multiplier": 1.0,
        "rebirths": 0,
        "current_world": "Starter Island",
        "unlocked_worlds": ["Starter Island"],
        "pets": [],
        "equipped": [],
        "stats": {
            "clicks": 0, "eggs_hatched": 0, "pets_hatched_total": 0,
            "total_earned": 0.0, "upgrades_bought": 0, "rebirths": 0,
        },
        "claimed_quests": [],
        "claimed_achievements": [],
        "daily_last_claim": "",
        "daily_streak": 0,
        "last_tick": time.time(),
    }

def connect_db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS players (
            username TEXT PRIMARY KEY,
            save_data TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    connection.commit()
    return connection

def load_player(username):
    connection = connect_db()
    row = connection.execute(
        "SELECT save_data FROM players WHERE username = ?", (username,)
    ).fetchone()
    connection.close()
    if row:
        try:
            data = json.loads(row[0])
            defaults = new_player()
            for key, value in defaults.items():
                if key not in data:
                    data[key] = value
            for key, value in defaults["stats"].items():
                data["stats"].setdefault(key, value)
            return data
        except (json.JSONDecodeError, TypeError):
            pass
    return new_player()

def save_player(username, data):
    connection = connect_db()
    connection.execute(
        """INSERT INTO players (username, save_data, updated_at)
           VALUES (?, ?, ?)
           ON CONFLICT(username) DO UPDATE SET
           save_data=excluded.save_data, updated_at=excluded.updated_at""",
        (username, json.dumps(data), datetime.now().isoformat(timespec="seconds")),
    )
    connection.commit()
    connection.close()

def fmt(value):
    value = float(value)
    suffixes = ["", "K", "M", "B", "T", "Qa", "Qi"]
    index = 0
    while abs(value) >= 1000 and index < len(suffixes) - 1:
        value /= 1000
        index += 1
    return f"${value:,.2f}{suffixes[index]}" if index else f"${value:,.0f}"

def pet_bonus(data):
    bonus = 1.0
    pet_lookup = {pet["id"]: pet for pet in data["pets"]}
    for pet_id in data["equipped"]:
        pet = pet_lookup.get(pet_id)
        if pet:
            bonus += pet["multiplier"] - 1
    return bonus

def total_multiplier(data):
    return data["multiplier"] * (1 + data["rebirths"] * 0.25) * pet_bonus(data)

def add_money(data, amount):
    if amount <= 0:
        return
    data["money"] += amount
    data["stats"]["total_earned"] += amount

def update_passive_income(data):
    now = time.time()
    last = data.get("last_tick", now)
    elapsed = max(0, min(now - last, 60))
    if data["auto_power"] > 0:
        add_money(data, elapsed * data["auto_power"] * total_multiplier(data))
    data["last_tick"] = now

def draw_pet(world):
    choices = PETS[world]
    names = [item[0] for item in choices]
    weights = [item[3] for item in choices]
    selected = random.choices(choices, weights=weights, k=1)[0]
    return {
        "id": uuid.uuid4().hex[:10],
        "name": selected[0],
        "rarity": selected[1],
        "multiplier": selected[2],
        "world": world,
        "equipped": False,
    }

# -------------------- PLAYER LOGIN / PROFILE --------------------

if "username" not in st.session_state:
    st.session_state.username = ""
if "player" not in st.session_state:
    st.session_state.player = None

if st.session_state.player is None:
    st.markdown("""
    <div class="login-card">
      <div style="font-size:54px">💸</div>
      <h1> MONEY SIMULATOR </h1>
      <p>Build your fortune, collect pets, and unlock new worlds!</p>
    </div>
    """, unsafe_allow_html=True)
    username_input = st.text_input("Choose a player name", max_chars=18, placeholder="YourPlayerName")
    st.caption("Use the same name next time to load your saved local profile.")
    if st.button("🚀 PLAY NOW", use_container_width=True):
        clean_name = username_input.strip()
        if not clean_name:
            st.error("Please enter a player name.")
        else:
            st.session_state.username = clean_name
            st.session_state.player = load_player(clean_name)
            st.rerun()
    st.stop()

username = st.session_state.username
data = st.session_state.player

# -------------------- STYLE / ANIMATION --------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
html, body, [class*="css"] { font-family: 'Nunito', sans-serif; }
.stApp {
  background: radial-gradient(circle at 15% 10%, #263f73 0%, #111b34 42%, #0a1020 100%);
  color: #f5f7ff;
}
h1,h2,h3,h4,p,label,span { color: #f5f7ff; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1450px; }
.hero {
  padding: 24px; border-radius: 22px; text-align: center;
  background: linear-gradient(120deg, #263e72, #4c36a5, #176b91);
  border: 1px solid rgba(255,255,255,.18);
  box-shadow: 0 12px 35px rgba(0,0,0,.25);
  animation: glow 4s ease-in-out infinite alternate;
}
@keyframes glow { from {filter:brightness(.96)} to {filter:brightness(1.12)} }
.stat-card {
  background: linear-gradient(145deg,#1d2d4c,#263c62);
  border: 1px solid #40577f; border-radius: 17px;
  padding: 16px; text-align: center; min-height: 108px;
}
.stat-number { font-size: clamp(22px,3vw,34px); font-weight: 900; color: #72f1bd; }
.stat-label { font-size: 13px; color: #c4d2ed; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }
.pet-card {
  background: linear-gradient(145deg,#233657,#182842);
  border: 1px solid #52688e; border-radius: 16px;
  padding: 14px; margin-bottom: 10px;
}
div.stButton > button {
  border-radius: 13px; border: 1px solid #6585b9;
  background: linear-gradient(90deg,#2879d0,#5b58d6);
  color: white; font-weight: 900; min-height: 45px;
  transition: transform .15s ease, filter .15s ease;
}
div.stButton > button:hover { transform: translateY(-2px); filter: brightness(1.18); color: white; }
div[data-testid="stMetric"] {
  background:#1c2d4b; padding:12px; border-radius:14px;
  border:1px solid #40577f;
}
section[data-testid="stSidebar"] { background:#101a30; }
hr { border-color:#3a4e70; }
.small-muted { color:#b8c8e5; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# Refresh the page so passive income updates.
st_autorefresh(interval=1000, key="game_refresh")
update_passive_income(data)

# -------------------- TOP HEADER / STATS --------------------

world = next(w for w in WORLDS if w["name"] == data["current_world"])
st.markdown(f"""
<div class="hero">
  <div style="font-size:44px">{world['emoji']} 💸 🐾</div>
  <h1 style="margin:0;font-weight:900">MONEY SIMULATOR</h1>
  <p style="margin:5px 0 0 0">Welcome back, <b>{username}</b>! Your empire is growing.</p>
</div>
""", unsafe_allow_html=True)

st.write("")
stat_cols = st.columns(4)
stats = [
    ("💵 MONEY", fmt(data["money"])),
    ("💎 GEMS", f"{data['gems']:,}"),
    ("⚡ PER SECOND", fmt(data["auto_power"] * total_multiplier(data))),
    ("🌟 REBIRTHS", str(data["rebirths"])),
]
for col, (label, value) in zip(stat_cols, stats):
    col.markdown(
        f'<div class="stat-card"><div class="stat-label">{label}</div>'
        f'<div class="stat-number">{value}</div></div>',
        unsafe_allow_html=True,
    )

# -------------------- SIDEBAR --------------------

with st.sidebar:
    st.markdown("## 🎮 Player Menu")
    st.write(f"**Player:** {username}")
    st.write(f"**World:** {world['name']}")
    st.write(f"**Pet bonus:** x{pet_bonus(data):.2f}")
    st.write(f"**Total multiplier:** x{total_multiplier(data):.2f}")
    st.divider()
    st.caption("Your game saves automatically.")
    if st.button("💾 SAVE NOW", use_container_width=True):
        save_player(username, data)
        st.success("Progress saved!")
    if st.button("↪ Switch player", use_container_width=True):
        save_player(username, data)
        st.session_state.player = None
        st.session_state.username = ""
        st.rerun()
    st.caption("Local prototype: profiles are stored on this server, not shared across separate deployments.")

# -------------------- MAIN TABS --------------------

tabs = st.tabs(["🏠 Home", "🛒 Shop", "🥚 Eggs", "🐾 Pets", "🌍 Worlds", "🎁 Rewards", "📜 Quests", "🏆 Achievements"])

# HOME
with tabs[0]:
    st.subheader("💰 Make money")
    st.write("Click the big button to earn cash. Your generators keep earning while the game is open.")
    click_amount = data["click_power"] * total_multiplier(data)
    click_col, info_col = st.columns([1.3, 1])
    with click_col:
        if st.button(f"💸  CLICK  +{fmt(click_amount)}", use_container_width=True):
            add_money(data, click_amount)
            data["stats"]["clicks"] += 1
            save_player(username, data)
            st.rerun()
    with info_col:
        st.markdown(
            f'<div class="pet-card"><b>👆 Click power</b><h2>{fmt(click_amount)}</h2>'
            f'<span class="small-muted">Each click, including your pet and rebirth bonuses</span></div>',
            unsafe_allow_html=True,
        )
    st.subheader("📊 Your progress")
    st.progress(min(data["stats"]["total_earned"] / 100000, 1.0))
    st.caption(f"Lifetime earnings: {fmt(data['stats']['total_earned'])} / $100K starter milestone")
    st.write(f"Pets collected: **{len(data['pets'])}** · Eggs hatched: **{data['stats']['eggs_hatched']}** · Upgrades: **{data['stats']['upgrades_bought']}**")
    st.info("Tip: hatch pets to increase your multiplier, then unlock stronger worlds for better eggs.")

# SHOP
with tabs[1]:
    st.subheader("🛒 Upgrade shop")
    st.caption("Upgrades become more expensive each time you buy them.")
    c1, c2, c3 = st.columns(3)
    click_cost = int(25 * (data["click_power"] ** 1.65))
    auto_cost = int(100 * ((data["auto_power"] + 1) ** 1.8))
    mult_cost = int(1000 * data["multiplier"])
    with c1:
        st.markdown('<div class="pet-card"><h3>👆 Stronger Click</h3><p>+1 base click power</p></div>', unsafe_allow_html=True)
        st.metric("Current power", data["click_power"])
        st.write(f"Cost: **{fmt(click_cost)}**")
        if st.button("BUY CLICK UPGRADE", key="buy_click", use_container_width=True):
            if data["money"] >= click_cost:
                data["money"] -= click_cost
                data["click_power"] += 1
                data["stats"]["upgrades_bought"] += 1
                save_player(username, data)
                st.success("Click power upgraded!")
                st.rerun()
            else: st.error("Not enough money.")
    with c2:
        st.markdown('<div class="pet-card"><h3>⚡ Generator</h3><p>+1 base cash per second</p></div>', unsafe_allow_html=True)
        st.metric("Generators", data["auto_power"])
        st.write(f"Cost: **{fmt(auto_cost)}**")
        if st.button("BUY GENERATOR", key="buy_auto", use_container_width=True):
            if data["money"] >= auto_cost:
                data["money"] -= auto_cost
                data["auto_power"] += 1
                data["stats"]["upgrades_bought"] += 1
                save_player(username, data)
                st.success("Generator purchased!")
                st.rerun()
            else: st.error("Not enough money.")
    with c3:
        st.markdown('<div class="pet-card"><h3>🚀 Double Multiplier</h3><p>Doubles your base multiplier</p></div>', unsafe_allow_html=True)
        st.metric("Current multiplier", f"x{data['multiplier']:.0f}")
        st.write(f"Cost: **{fmt(mult_cost)}**")
        if st.button("BUY 2X MULTIPLIER", key="buy_multi", use_container_width=True):
            if data["money"] >= mult_cost:
                data["money"] -= mult_cost
                data["multiplier"] *= 2
                data["stats"]["upgrades_bought"] += 1
                save_player(username, data)
                st.success("Multiplier doubled!")
                st.rerun()
            else: st.error("Not enough money.")
    st.divider()
    rebirth_cost = 100_000 * (data["rebirths"] + 1)
    st.subheader("🌟 Rebirth")
    st.write(f"Reset your cash and upgrades for a permanent +25% bonus per rebirth. Your pets and unlocked worlds stay.")
    st.write(f"Next rebirth: **{fmt(rebirth_cost)}**")
    if st.button("🌟 REBIRTH", use_container_width=True):
        if data["money"] >= rebirth_cost:
            data["money"] = 0
            data["click_power"] = 1
            data["auto_power"] = 0
            data["multiplier"] = 1.0
            data["rebirths"] += 1
            data["stats"]["rebirths"] = data["rebirths"]
            save_player(username, data)
            st.success("Rebirth complete! Permanent bonus increased.")
            st.rerun()
        else:
            st.error("You need more money to rebirth.")

# EGGS
with tabs[2]:
    st.subheader("🥚 Hatch an egg")
    st.write(f"Current world: **{world['emoji']} {world['name']}**")
    egg_cost = world["egg_cost"]
    st.markdown(
        f'<div class="pet-card"><h2>🥚 {world["name"]} Egg</h2>'
        f'<p>Possible pets: {", ".join(p[0] for p in PETS[world["name"]])}</p>'
        f'<h3>Price: {fmt(egg_cost)}</h3></div>',
        unsafe_allow_html=True,
    )
    if st.button("🥚 HATCH EGG", use_container_width=True):
        if data["money"] >= egg_cost:
            data["money"] -= egg_cost
            pet = draw_pet(world["name"])
            data["pets"].append(pet)
            data["stats"]["eggs_hatched"] += 1
            data["stats"]["pets_hatched_total"] += 1
            save_player(username, data)
            st.success(f"You hatched {RARITY_EMOJI[pet['rarity']]} {pet['rarity']} {pet['name']}! x{pet['multiplier']} multiplier")
            st.rerun()
        else:
            st.error(f"You need {fmt(egg_cost - data['money'])} more.")

# PETS / INVENTORY
with tabs[3]:
    st.subheader("🐾 Pet inventory")
    st.write(f"Pets owned: **{len(data['pets'])}** · Equipped: **{len(data['equipped'])}/{MAX_EQUIPPED}**")
    st.write(f"Your pet multiplier: **x{pet_bonus(data):.2f}**")
    if not data["pets"]:
        st.info("You don't have any pets yet. Visit the Eggs tab to hatch your first one!")
    else:
        for pet in data["pets"]:
            is_equipped = pet["id"] in data["equipped"]
            with st.container(border=True):
                p1, p2, p3 = st.columns([2, 1, 1])
                p1.markdown(
                    f"**{RARITY_EMOJI.get(pet['rarity'], '🐾')} {pet['name']}**  \n"
                    f"{pet['rarity']} · x{pet['multiplier']} · {pet['world']}"
                )
                p2.write("✅ Equipped" if is_equipped else "In inventory")
                if is_equipped:
                    if p3.button("Unequip", key=f"unequip_{pet['id']}"):
                        data["equipped"].remove(pet["id"])
                        save_player(username, data)
                        st.rerun()
                else:
                    if p3.button("Equip", key=f"equip_{pet['id']}", disabled=len(data["equipped"]) >= MAX_EQUIPPED):
                        data["equipped"].append(pet["id"])
                        save_player(username, data)
                        st.rerun()
    st.caption("Equip up to 3 pets. Their bonuses add together.")

# WORLDS
with tabs[4]:
    st.subheader("🌍 Explore new worlds")
    st.write("Unlock worlds with money. Each world has its own egg and pets.")
    for item in WORLDS:
        unlocked = item["name"] in data["unlocked_worlds"]
        current = item["name"] == data["current_world"]
        with st.container(border=True):
            w1, w2, w3 = st.columns([2, 1, 1])
            w1.markdown(f"### {item['emoji']} {item['name']}")
            w1.caption(f"Egg price: {fmt(item['egg_cost'])}")
            if current:
                w2.success("Current world")
            elif unlocked:
                w2.info("Unlocked")
            else:
                w2.write(f"Unlock: **{fmt(item['cost'])}**")
            if current:
                w3.button("CURRENT", key=f"world_{item['name']}", disabled=True)
            elif unlocked:
                if w3.button("TRAVEL", key=f"travel_{item['name']}"):
                    data["current_world"] = item["name"]
                    save_player(username, data)
                    st.rerun()
            else:
                if w3.button("UNLOCK", key=f"unlock_{item['name']}"):
                    if data["money"] >= item["cost"]:
                        data["money"] -= item["cost"]
                        data["unlocked_worlds"].append(item["name"])
                        data["current_world"] = item["name"]
                        save_player(username, data)
                        st.success(f"{item['name']} unlocked!")
                        st.rerun()
                    else:
                        st.error(f"Need {fmt(item['cost'] - data['money'])} more.")

# DAILY REWARDS
with tabs[5]:
    st.subheader("🎁 Daily login reward")
    today = date.today()
    last_claim = data.get("daily_last_claim", "")
    claimed_today = last_claim == today.isoformat()
    yesterday = (today - timedelta(days=1)).isoformat()
    next_streak = data["daily_streak"] + 1 if last_claim == yesterday else 1
    reward = 500 * min(next_streak, 7)
    st.markdown(
        f'<div class="pet-card"><h2>🎁 Day {next_streak} reward</h2>'
        f'<h1 style="color:#72f1bd">{fmt(reward)}</h1>'
        f'<p>Current streak: {data["daily_streak"]} day(s)</p></div>',
        unsafe_allow_html=True,
    )
    if claimed_today:
        st.success("You already claimed today's reward. Come back tomorrow!")
    elif st.button("CLAIM DAILY REWARD", use_container_width=True):
        data["daily_streak"] = next_streak
        data["daily_last_claim"] = today.isoformat()
        add_money(data, reward)
        save_player(username, data)
        st.success(f"You received {fmt(reward)}!")
        st.rerun()
    st.caption("The reward streak grows up to 7 days, then stays at the day-7 reward.")

# QUESTS
with tabs[6]:
    st.subheader("📜 Quests")
    st.caption("Complete objectives to earn bonus cash. Each quest can be claimed once in this prototype.")
    for quest in QUESTS:
        progress = data["stats"].get(quest["stat"], 0)
        completed = progress >= quest["target"]
        claimed = quest["id"] in data["claimed_quests"]
        st.markdown(f"**{quest['title']}** — {quest['description']}")
        st.progress(min(progress / quest["target"], 1.0))
        st.caption(f"{progress:,.0f} / {quest['target']:,.0f} · Reward: {fmt(quest['reward'])}")
        if claimed:
            st.success("Reward claimed")
        elif completed:
            if st.button(f"CLAIM {fmt(quest['reward'])}", key=f"quest_{quest['id']}"):
                add_money(data, quest["reward"])
                data["claimed_quests"].append(quest["id"])
                save_player(username, data)
                st.rerun()
        else:
            st.info("Keep playing to complete this quest.")
        st.divider()

# ACHIEVEMENTS
with tabs[7]:
    st.subheader("🏆 Achievements")
    for achievement in ACHIEVEMENTS:
        progress = data["stats"].get(achievement["stat"], 0)
        completed = progress >= achievement["target"]
        claimed = achievement["id"] in data["claimed_achievements"]
        with st.container(border=True):
            st.markdown(f"**{'🏅' if completed else '🔒'} {achievement['title']}**")
            st.caption(achievement["description"])
            st.progress(min(progress / achievement["target"], 1.0))
            st.caption(f"{progress:,.0f} / {achievement['target']:,.0f} · Reward: {fmt(achievement['reward'])}")
            if claimed:
                st.success("Claimed")
            elif completed:
                if st.button(f"CLAIM {fmt(achievement['reward'])}", key=f"achievement_{achievement['id']}"):
                    add_money(data, achievement["reward"])
                    data["claimed_achievements"].append(achievement["id"])
                    save_player(username, data)
                    st.rerun()

# Save automatically after each rerun, including passive income.
save_player(username, data)

st.markdown("---")
st.markdown(
    '<p style="text-align:center;color:#9fb2d4;font-size:12px">'
    'MONEY SIMULATOR · Streamlit prototype · Keep upgrading and have fun!</p>',
    unsafe_allow_html=True,
)
