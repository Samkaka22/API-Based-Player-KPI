import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Football Player Dashboard", layout="wide")

st.title("Football Player Analytics Dashboard")

if "players_list" not in st.session_state:
    st.session_state.players_list = []
if "seasons_list" not in st.session_state:
    st.session_state.seasons_list = []
if "player_data" not in st.session_state:
    st.session_state.player_data = None

st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("API Sports Key", type="password")

if api_key:
    headers = {"x-apisports-key": api_key}
    
    search_mode = st.sidebar.radio("Search Mode", ["Search by ID", "Search by Name"])
    
    if search_mode == "Search by ID":
        player_id = st.sidebar.text_input("Player ID", value="154")
        season = st.sidebar.text_input("Season Year", value="2022")
        
        if st.sidebar.button("Fetch Data", type="primary"):
            with st.spinner("Fetching data..."):
                res = requests.get(
                    "https://v3.football.api-sports.io/players",
                    headers=headers,
                    params={"id": player_id, "season": season}
                )
                data = res.json()
                if data.get("response"):
                    st.session_state.player_data = data["response"][0]
                else:
                    st.error("No statistics found for this player in the selected season.")
                    st.session_state.player_data = None
                    
    elif search_mode == "Search by Name":
        search_query = st.sidebar.text_input("Player Name")
        
        if st.sidebar.button("Search Player"):
            with st.spinner("Searching..."):
                res = requests.get(
                    "https://v3.football.api-sports.io/players/profiles",
                    headers=headers,
                    params={"search": search_query}
                )
                data = res.json()
                if data.get("response"):
                    st.session_state.players_list = data["response"]
                    st.session_state.player_data = None
                    st.session_state.seasons_list = []
                else:
                    st.sidebar.error("No players found.")
                    st.session_state.players_list = []
                    
        if st.session_state.players_list:
            player_options = {}
            for item in st.session_state.players_list:
                p = item["player"]
                label = f"{p.get('firstname', '')} {p.get('lastname', '')} ({p.get('nationality', '')}) - ID: {p.get('id')}"
                player_options[label] = p.get("id")

            selected_label = st.sidebar.selectbox("Select Player", list(player_options.keys()))
            selected_id = player_options[selected_label]

            if not st.session_state.seasons_list:
                s_res = requests.get(
                    "https://v3.football.api-sports.io/players/seasons",
                    headers=headers
                )
                s_data = s_res.json()
                if s_data.get("response"):
                    st.session_state.seasons_list = sorted(s_data["response"], reverse=True)

            if st.session_state.seasons_list:
                selected_season = st.sidebar.selectbox("Season Year", st.session_state.seasons_list)

                if st.sidebar.button("Get Detailed Stats", type="primary"):
                    with st.spinner("Fetching stats..."):
                        stat_res = requests.get(
                            "https://v3.football.api-sports.io/players",
                            headers=headers,
                            params={"id": selected_id, "season": selected_season}
                        )
                        stat_data = stat_res.json()

                        if stat_data.get("response"):
                            st.session_state.player_data = stat_data["response"][0]
                        else:
                            st.error("No statistics found for this player in the selected season.")
                            st.session_state.player_data = None

elif not api_key:
    st.info("Enter your API Key in the sidebar to get started.")

if st.session_state.player_data:
    p = st.session_state.player_data["player"]
    stats_list = st.session_state.player_data.get("statistics", [])

    st.markdown(f"## {p.get('firstname', '')} {p.get('lastname', '')} ({p.get('name', '')})")

    col1, col2, col3, col4, col5 = st.columns(5)

    if p.get("photo"):
        with col1:
            st.image(p.get("photo"), width=150)

    col2.metric("Player ID", p.get('id'))
    col2.metric("Nationality", p.get('nationality'))

    col3.metric("Age", p.get('age'))
    col3.metric("Height", p.get('height', 'N/A'))

    col4.metric("Weight", p.get('weight', 'N/A'))
    col4.metric("Position", p.get('position', 'N/A'))

    col5.metric("Number", p.get('number', 'N/A'))
    col5.metric("Injured", "Yes" if p.get('injured') else "No")

    st.divider()

    if stats_list:
        st.subheader("Competition Statistics")
        tab_titles = [f"{s['league']['name']} ({s['team']['name']})" for s in stats_list]
        tabs = st.tabs(tab_titles)

        for idx, stat in enumerate(stats_list):
            with tabs[idx]:
                league = stat.get('league', {})
                team = stat.get('team', {})
                games = stat.get('games', {})
                goals = stat.get('goals', {})
                shots = stat.get('shots', {})
                passes = stat.get('passes', {})
                tackles = stat.get('tackles', {})
                dribbles = stat.get('dribbles', {})
                fouls = stat.get('fouls', {})
                cards = stat.get('cards', {})
                penalty = stat.get('penalty', {})

                st.caption(f"Playing for {team.get('name', 'N/A')} in {league.get('name', 'N/A')} ({league.get('country', 'N/A')})")

                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Appearances", games.get('appearences') or 0)
                m2.metric("Lineups", games.get('lineups') or 0)
                m3.metric("Minutes Played", games.get('minutes') or 0)
                m4.metric("Position", games.get('position') or 'N/A')
                m5.metric("Rating", games.get('rating') or 'N/A')

                st.markdown("---")

                col_left, col_right = st.columns(2)

                with col_left:
                    st.markdown("### Attacking Output")
                    df_attack = pd.DataFrame({
                        "Metric": ["Total Goals", "Assists", "Total Shots", "Shots on Target", "Penalties Scored", "Penalties Missed"],
                        "Count": [
                            goals.get('total') or 0,
                            goals.get('assists') or 0,
                            shots.get('total') or 0,
                            shots.get('on') or 0,
                            penalty.get('scored') or 0,
                            penalty.get('missed') or 0
                        ]
                    })
                    st.dataframe(df_attack, hide_index=True, use_container_width=True)

                    st.markdown("### Passing & Dribbling")
                    df_pass_dribble = pd.DataFrame({
                        "Metric": ["Total Passes", "Key Passes", "Pass Accuracy", "Dribble Attempts", "Successful Dribbles"],
                        "Value": [
                            passes.get('total') or 0,
                            passes.get('key') or 0,
                            f"{passes.get('accuracy') or 0}%",
                            dribbles.get('attempts') or 0,
                            dribbles.get('success') or 0
                        ]
                    })
                    st.dataframe(df_pass_dribble, hide_index=True, use_container_width=True)

                with col_right:
                    st.markdown("### Defensive Output")
                    df_defense = pd.DataFrame({
                        "Metric": ["Total Tackles", "Interceptions", "Blocks"],
                        "Count": [
                            tackles.get('total') or 0,
                            tackles.get('interceptions') or 0,
                            tackles.get('blocks') or 0
                        ]
                    })
                    st.dataframe(df_defense, hide_index=True, use_container_width=True)

                    st.markdown("### Discipline & Physicality")
                    df_discipline = pd.DataFrame({
                        "Metric": ["Fouls Committed", "Fouls Drawn", "Yellow Cards", "Yellow-Red Cards", "Red Cards"],
                        "Count": [
                            fouls.get('committed') or 0,
                            fouls.get('drawn') or 0,
                            cards.get('yellow') or 0,
                            cards.get('yellowred') or 0,
                            cards.get('red') or 0
                        ]
                    })
                    st.dataframe(df_discipline, hide_index=True, use_container_width=True)
    else:
        st.warning("No statistics available for this selection.")
