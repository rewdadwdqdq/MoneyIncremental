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
