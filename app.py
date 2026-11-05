
import streamlit as st
import streamlit.components.v1 as components
import time

st.set_page_config(
    page_title="Money Incremental",
    page_icon="💰",
    layout="wide"
)

# -------------------------
# GAME DATA
# -------------------------

if "money" not in st.session_state:
    st.session_state.money = 0
    st.session_state.click_power = 1
    st.session_state.auto_power = 0
    st.session_state.multiplier = 1
    st.session_state.rebirths = 0
    st.session_state.last_update = time.time()

# -------------------------
# GAME CALCULATIONS
# -------------------------

now = time.time()
elapsed = now - st.session_state.last_update

st.session_state.money += (
    elapsed *
    st.session_state.auto_power *
    st.session_state.multiplier
)

st.session_state.last_update = now

money = st.session_state.money

# -------------------------
# HTML AND CSS
# -------------------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #10172a, #202d49);
    color: white;
}

h1, h2, h3, p, label {
    color: white !important;
}

div.stButton > button {
    width: 100%;
    height: 65px;
    border-radius: 15px;
    border: none;
    background: linear-gradient(90deg, #00c853, #64dd17);
    color: white;
    font-size: 22px;
    font-weight: bold;
    transition: 0.2s;
}

div.stButton > button:hover {
    transform: scale(1.03);
    background: #00e676;
    color: white;
}

.game-card {
    background: #263653;
    padding: 22px;
    border-radius: 18px;
    text-align: center;
    border: 1px solid #435577;
}

.money {
    font-size: 42px;
    font-weight: bold;
    color: #69f0ae;
}

</style>
""", unsafe_allow_html=True)

# -------------------------
# HEADER
# -------------------------

st.title("💰 MONEY INCREMENTAL")
st.caption("Earn money. Buy upgrades. Become rich.")

# -------------------------
# PLAYER STATS
# -------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="game-card">
        <h3>💵 Total Money</h3>
        <div class="money">${st.session_state.money:,.1f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="game-card">
        <h3>👆 Click Power</h3>
        <div class="money">+{st.session_state.click_power * st.session_state.multiplier}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="game-card">
        <h3>⚡ Auto Income</h3>
        <div class="money">${st.session_state.auto_power * st.session_state.multiplier}/s</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# -------------------------
# CLICK BUTTON
# -------------------------

st.subheader("💸 Earn Money")

if st.button("💰 CLICK TO EARN MONEY"):
    st.session_state.money += (
        st.session_state.click_power *
        st.session_state.multiplier
    )

# -------------------------
# UPGRADE SHOP
# -------------------------

st.divider()
st.header("🏪 Upgrade Shop")

col1, col2 = st.columns(2)

with col1:
    st.subheader("👆 Click Upgrade")

    click_cost = 25 * (st.session_state.click_power ** 2)

    st.write(f"Increase click power by 1")
    st.write(f"Cost: ${click_cost:,.0f}")

    if st.button("BUY CLICK UPGRADE"):
        if st.session_state.money >= click_cost:
            st.session_state.money -= click_cost
            st.session_state.click_power += 1
            st.success("Click power upgraded!")
        else:
            st.error("Not enough money!")

with col2:
    st.subheader("⚡ Auto Generator")

    auto_cost = 100 * (st.session_state.auto_power + 1) ** 2

    st.write("Generate passive income every second")
    st.write(f"Cost: ${auto_cost:,.0f}")

    if st.button("BUY AUTO GENERATOR"):
        if st.session_state.money >= auto_cost:
            st.session_state.money -= auto_cost
            st.session_state.auto_power += 1
            st.success("Auto generator purchased!")
        else:
            st.error("Not enough money!")

# -------------------------
# MULTIPLIER
# -------------------------

st.divider()
st.header("🚀 Money Multiplier")

multiplier_cost = 1000 * st.session_state.multiplier

st.write(f"Current multiplier: x{st.session_state.multiplier}")
st.write(f"Upgrade cost: ${multiplier_cost:,.0f}")

if st.button("BUY 2X MULTIPLIER"):
    if st.session_state.money >= multiplier_cost:
        st.session_state.money -= multiplier_cost
        st.session_state.multiplier *= 2
        st.success("Multiplier increased!")
    else:
        st.error("Not enough money!")

# -------------------------
# REBIRTH
# -------------------------

st.divider()
st.header("🌟 Rebirth")

rebirth_cost = 100000 * (st.session_state.rebirths + 1)

st.write(f"Rebirth cost: ${rebirth_cost:,.0f}")
st.write(f"Total rebirths: {st.session_state.rebirths}")

if st.button("🌟 REBIRTH"):
    if st.session_state.money >= rebirth_cost:
        st.session_state.money = 0
        st.session_state.click_power = 1
        st.session_state.auto_power = 0
        st.session_state.multiplier = 1
        st.session_state.rebirths += 1

        st.success("REBIRTH COMPLETE!")
    else:
        st.error("You need more money to rebirth!")

# -------------------------
# HTML ELEMENT EXAMPLE
# -------------------------

st.divider()
st.header("🌐 HTML Game Element")

components.html("""
<div style="
    background: linear-gradient(135deg,#172b4d,#304f80);
    border-radius: 20px;
    padding: 25px;
    text-align: center;
    color: white;
    font-family: Arial;
">
    <h2>🏆 MONEY TYCOON</h2>
    <p>Welcome to your money empire!</p>

    <div style="
        background: #14213d;
        padding: 15px;
        border-radius: 12px;
    ">
        <h3>💎 Become The Richest Player!</h3>
        <p>Click, upgrade, generate and rebirth.</p>
    </div>

    <p style="color: #69f0ae;">
        YOUR EMPIRE STARTS HERE
    </p>
</div>
""", height=240)

# -------------------------
# REFRESH
# -------------------------

time.sleep(0.5)
st.rerun()
