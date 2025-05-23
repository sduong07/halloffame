import pandas as pd
import streamlit as st
import numpy as np
import random
from collections import defaultdict
import base64
from pathlib import Path

# Set page config
st.set_page_config(page_title="NBA Hall of Fame Simulator", layout="wide")

def set_bg_local(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

set_bg_local("background.jpg")

top_bar_css = """
<style>
header[data-testid="stHeader"] {
    background-color: rgba(0, 0, 0, 0); /* Fully transparent */
}
</style>
"""

# Inject CSS
st.markdown(top_bar_css, unsafe_allow_html=True)


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def remote_css(url):
   st.markdown(f'<link href="{url}" rel="stylesheet">', unsafe_allow_html=True)

local_css("style.css")
remote_css('https://fonts.googleapis.com/icon?family=Material+Icons')


st.title("NBA Hall of Hame simulator")


st.header("This webapp randomly selects 10 players from the nba hall of fame and simulates a 5v5 for 48 minutes")


# Load your CSV file
df = pd.read_csv('filtered_output.csv')

#Define the required positions
positions = ['PointGuard', 'ShootingGuard', 'SmallForward', 'PowerForward', 'Center']

# For storing sampled rows
sampled_rows = []

# Sample 2 rows for each position
for pos in positions:
    subset = df[df['Position'] == pos]
    if len(subset) < 2:
        raise ValueError(f"Not enough players for position {pos}")
    sampled = subset.sample(n=2, random_state=(random.randint(0, 100)))  # Use random_state for reproducibility
    sampled_rows.append(sampled)

# Concatenate the sampled rows
final_team = pd.concat(sampled_rows).reset_index(drop=True)


#Team 1 
selected_rows_1= final_team.iloc[[1, 3, 5, 7, 9]]
team1_df = selected_rows_1


#Team 2 
selected_rows_2= final_team.iloc[[0, 2, 4, 6, 8]]
team2_df = selected_rows_2


st.header("Team 1")
st.dataframe(team1_df)

st.header("Team 2")
st.dataframe(team2_df)

for team in [team1_df, team2_df]:
    team['PTS_per_min'] = team['PTS_per_game'] / team['MP_per_game']
    team['AST_per_min'] = team['AST_per_game'] / team['MP_per_game']
    team['TRB_per_min'] = team['TRB_per_game'] / team['MP_per_game']

def simulate_minute(team):
    stats = []
    for _, player in team.iterrows():
        # Determine number of points scored this minute (Poisson works well for rare events)
        pts = np.random.poisson(player['PTS_per_min']) if player['PTS_per_min'] > 0 else 0
        ast = np.random.poisson(player['AST_per_min']) if player['AST_per_min'] > 0 else 0
        trb = np.random.poisson(player['TRB_per_min']) if player['TRB_per_min'] > 0 else 0

        stats.append({
            'Player': player['Player'],
            'PTS': pts,
            'AST': ast,
            'TRB': trb
        })
    return stats


def simulate_game(team1, team2):
    # Initialize stats
    team1_stats = defaultdict(lambda: {'PTS': 0, 'AST': 0, 'TRB': 0})
    team2_stats = defaultdict(lambda: {'PTS': 0, 'AST': 0, 'TRB': 0})
    team1_score = 0
    team2_score = 0

    for minute in range(48):
        t1_minute = simulate_minute(team1)
        t2_minute = simulate_minute(team2)

        for stat in t1_minute:
            team1_stats[stat['Player']]['PTS'] += stat['PTS']
            team1_stats[stat['Player']]['AST'] += stat['AST']
            team1_stats[stat['Player']]['TRB'] += stat['TRB']
            team1_score += stat['PTS']

        for stat in t2_minute:
            team2_stats[stat['Player']]['PTS'] += stat['PTS']
            team2_stats[stat['Player']]['AST'] += stat['AST']
            team2_stats[stat['Player']]['TRB'] += stat['TRB']
            team2_score += stat['PTS']

    return {
        'Team1': team1_stats,
        'Team2': team2_stats,
        'FinalScore': (team1_score, team2_score)
    }


with st.spinner("Simulating..."):
	results = []

	for _ in range(1000):  # 1000 simulations
	    result = simulate_game(team1_df, team2_df)
	    results.append(result['FinalScore'])


	#Example: calculate win probability
	team1_wins = sum(1 for score in results if score[0] > score[1])
	print(f"Team 1 win probability: {team1_wins / len(results) * 100:.1f}%")

	def print_game_stats(result):
	    print("🏀 Final Score")
	    print(f"Team 1: {result['FinalScore'][0]}  |  Team 2: {result['FinalScore'][1]}")
	    print("\n📊 Player Stats\n")

	    print("=== Team 1 ===")
	    for player, stats in result['Team1'].items():
	        print(f"{player:20} - PTS: {stats['PTS']:>2} | AST: {stats['AST']:>2} | TRB: {stats['TRB']:>2}")

	    print("\n=== Team 2 ===")
	    for player, stats in result['Team2'].items():
	        print(f"{player:20} - PTS: {stats['PTS']:>2} | AST: {stats['AST']:>2} | TRB: {stats['TRB']:>2}")


	result = simulate_game(team1_df, team2_df)
	gameresult= print_game_stats(result)





st.subheader("🏀 Final Score")


st.write(f"**Team 1:** {result['FinalScore'][0]}  |  **Team 2:** {result['FinalScore'][1]}")

st.subheader("📊 Player Stats")

st.markdown("### 🟦 Team 1")
for player, stats in result['Team1'].items():
    st.write(f"**{player}** — PTS: {stats['PTS']} | AST: {stats['AST']} | TRB: {stats['TRB']}")

st.markdown("### 🟥 Team 2")
for player, stats in result['Team2'].items():
    st.write(f"**{player}** — PTS: {stats['PTS']} | AST: {stats['AST']} | TRB: {stats['TRB']}")


