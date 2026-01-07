import requests
import pandas as pd
from datetime import datetime, timedelta
from tabulate import tabulate
import numpy as np
import sys

# --- CONFIGURATION ---
API_KEY = "302bf9f3449d4970a1ebaa2574088cfe" # Your confirmed API Token
PL_COMPETITION_ID = 2021 # Premier League ID
API_BASE_URL = "https://api.football-data.org/v4"
# NEW: Re-evaluated normalization max based on new LPF factor
MAX_REALISTIC_RAW_SCORE = 85 

# --- HELPER FUNCTIONS (API FETCHING) ---

def get_date_range_api(days_back):
    """Calculates the date range strings needed for a single API call."""
    today = datetime.now().date()
    
    # date_to_api: Tomorrow's date (API dateTo is exclusive)
    date_to_dt_api = today + timedelta(days=1)
    # date_from_dt: The starting point for the query period
    date_from_dt = today - timedelta(days=days_back)
    
    date_from_str = date_from_dt.strftime("%Y-%m-%d")
    date_to_str_api = date_to_dt_api.strftime("%Y-%m-%d")
    
    # Also return today's date string for display purposes (date_to_display)
    return date_from_str, date_to_str_api, today.strftime("%Y-%m-%d")

def fetch_data_single_call(date_from, date_to_api, api_key, competition_id, api_base_url):
    """Fetches FINISHED Premier League matches using a single, direct API call."""
    
    print(f"-> Attempting single fetch: {date_from} to {date_to_api}...")

    url = f"{api_base_url}/matches"
    
    params = {
        'competitions': competition_id,
        'dateFrom': date_from,
        'dateTo': date_to_api,
        'status': 'FINISHED'
    }
    
    headers = {"X-Auth-Token": api_key}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        sys.stderr.write(f"API Error: {err.response.status_code} for URL: {response.url}\n")
        sys.stderr.write("Note: Check API limits or requested date range.\n")
        return None
    except requests.exceptions.RequestException as e:
        sys.stderr.write(f"Network Error: {e}\n")
        return None

def fetch_standings(competition_id, api_key, api_base_url):
    """
    NEW: Fetches current league standings and returns a map of {team_id: rank}.
    If the API call fails, it returns an empty dictionary.
    """
    url = f"{api_base_url}/competitions/{competition_id}/standings"
    headers = {"X-Auth-Token": api_key}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        sys.stderr.write(f"\nError fetching standings: {e}\n")
        return {}

    rank_map = {}
    standings_tables = data.get('standings', [])
    if not standings_tables:
        return rank_map

    # Assuming the first entry in 'standings' is the TOTAL league table
    for entry in standings_tables[0].get('table', []):
        team_id = entry['team']['id']
        rank = entry['position']
        rank_map[team_id] = rank
        
    return rank_map

# --- 2. CORE LOGIC: ENHANCED EXCITEMENT SCORING ---

def calculate_excitement_score(match, rank_map):
    """
    Calculates the excitement score based on match metrics and league context (LPF).
    """
    
    home_score = match['score']['fullTime']['home']
    away_score = match['score']['fullTime']['away']
    
    if home_score is None or away_score is None:
        return 0, 0, 0, 0, 0 

    total_goals = home_score + away_score
    goal_diff = abs(home_score - away_score)
    
    # --- 1. Total Goal Action (Weight: 4.0) ---
    Goal_Score = total_goals 

    # --- 2. Parity Score (Weight: 3.0) ---
    Parity_Score = max(0, 3.0 - (goal_diff * 1.0))

    # --- 3. Late Drama Factor (Weight: 5.0) ---
    late_drama_points = 0
    
    # Large Comeback Heuristic
    if match['score'].get('halfTime'):
        ht_diff = abs(match['score']['halfTime']['home'] - match['score']['halfTime']['away'])
        ft_diff = abs(home_score - away_score)
        
        # If the half-time lead was large (2+ goals) but the full-time result was close (<=1 goal difference)
        if ht_diff >= 2 and ft_diff <= 1:
            late_drama_points += 2.5
    
    # High-Scoring Draw Bonus
    if goal_diff == 0 and total_goals >= 4:
        late_drama_points += 2.5
        
    Drama_Score = late_drama_points
    
    # --- 4. League Parity Factor (LPF) (New Weight: 2.0) ---
    
    home_id = match['homeTeam']['id']
    away_id = match['awayTeam']['id']

    # Get Ranks, default to middle (10.5) if team is missing from the standings (out of 20 teams)
    R_H = rank_map.get(home_id, 10.5) 
    R_A = rank_map.get(away_id, 10.5) 

    LPF_Score = 0
    rank_diff = abs(R_H - R_A)
    
    # 4a. Match-up Parity Bonus: Rewards games between teams of similar rank
    # Scale from max(1.0) for rank_diff 0 to min(0.1) for rank_diff 19
    LPF_Parity_Bonus = max(0.1, 1.0 - (rank_diff / 20.0))

    # 4b. Upset Bonus: Rewards a result where the lower-ranked team avoids defeat
    home_wins = home_score > away_score
    away_wins = away_score > home_score
    is_draw = home_score == away_score

    if is_draw:
        # Draw bonus: slightly boosted by rank difference (harder for underdog to draw a highly ranked team)
        LPF_Score = LPF_Parity_Bonus * 0.5 + (rank_diff / 20.0)
    
    elif (home_wins and R_H > R_A) or (away_wins and R_A > R_H):
        # Underdog won: Significant bonus based on the size of the upset
        LPF_Score = LPF_Parity_Bonus + (rank_diff / 8.0)
    
    # If the favorite won, LPF_Score remains low (LPF_Parity_Bonus is low for big rank diff, 
    # but still contributes slightly if ranks are close).

    # --- FINAL CALCULATION ---
    raw_score = (Goal_Score * 4.0) + (Parity_Score * 3.0) + (Drama_Score * 5.0) + (LPF_Score * 2.0)
    
    # Normalize against the new MAX_REALISTIC_RAW_SCORE
    Excitement_Score = ((raw_score / MAX_REALISTIC_RAW_SCORE) * 9.0) + 1.0
    Excitement_Score = min(10.0, Excitement_Score)
    
    LPF_Breakdown = round(LPF_Score * 2.0, 1) # Display LPF weighted value

    return round(Excitement_Score, 2), round(Goal_Score * 4.0, 1), round(Parity_Score * 3.0, 1), round(Drama_Score * 5.0, 1), LPF_Breakdown

def rank_completed_matches(fixtures, rank_map):
    """Applies the Retrospective Scoring to rank past fixtures, now including LPF."""
    ranked_list = []

    for fixture in fixtures:
        if fixture['score']['fullTime']['home'] is None:
            continue
            
        score, g_score, p_score, d_score, lpf_score = calculate_excitement_score(fixture, rank_map)
        
        ranked_list.append({
            'Excitement_Score': score,
            'Match': f"{fixture['homeTeam']['name']} vs {fixture['awayTeam']['name']}",
            'Result': f"{fixture['score']['fullTime']['home']}-{fixture['score']['fullTime']['away']}",
            'Date': fixture['utcDate'][:10],
            'HSS_Breakdown': f"G:{g_score}, P:{p_score}, D:{d_score}, LPF:{lpf_score}"
        })

    df = pd.DataFrame(ranked_list)
    return df.sort_values(by='Excitement_Score', ascending=False)


# --- 3. MAIN EXECUTION ---

def main():
    if API_KEY == "YOUR_API_KEY_HERE":
        print("ERROR: Please replace 'YOUR_API_KEY_HERE' in the script with your actual API key.")
        return

    try:
        days_back_str = input("Enter number of DAYS BACK to check for COMPLETED matches (e.g., 7 for last week): ")
        if not days_back_str.isdigit():
            raise ValueError
        days_back = int(days_back_str)
        
        date_from_str, date_to_str_api, date_to_str_display = get_date_range_api(days_back)

    except ValueError:
        print("Invalid input. Please enter a valid number of days.")
        return

    # 1. Fetch League Standings first to get context (LPF)
    rank_map = fetch_standings(PL_COMPETITION_ID, API_KEY, API_BASE_URL)
    if not rank_map:
        print("\nWARNING: Failed to retrieve standings. Ranking will only use score data (LPF set to 0).")

    # 2. Fetch matches using the simplified single-call logic
    data = fetch_data_single_call(date_from_str, date_to_str_api, API_KEY, PL_COMPETITION_ID, API_BASE_URL)
    
    if data is None:
        print("\nFailed to retrieve match data. Check the error output above or try a smaller 'DAYS BACK' number.")
        return
    
    fixtures = data.get('matches', [])

    if not fixtures:
         print(f"\nNo FINISHED Premier League matches found between {date_from_str} and {date_to_str_display}.")
         return

    print(f"\nFound {len(fixtures)} completed PL matches. Ranking them now...")

    # 3. Apply the HSS and rank the fixtures (Pass rank_map)
    ranked_df = rank_completed_matches(fixtures, rank_map)
    
    if ranked_df.empty:
        print("\nCould not rank any matches (missing score data).")
        return

    # 4. Display Results (Limit to 10 if more are found)
    display_df = ranked_df[['Match', 'Result', 'Date', 'Excitement_Score', 'HSS_Breakdown']]
    display_df = display_df.head(10).reset_index(drop=True)
    display_df['Rank'] = display_df.index + 1
    
    display_df['Excitement_Score'] = display_df['Excitement_Score'].apply(lambda x: f"{x:.2f}/10")
    final_cols = ['Rank', 'Excitement_Score', 'Match', 'Result', 'Date', 'HSS_Breakdown']
    
    print("\n" + "="*105)
    print(f"🎬📺 ENHANCED RETROSPECTIVE 'BEST TO WATCH' RANKING ({date_from_str} - {date_to_str_display}) 📺🎬")
    print("="*105)
    
    print(tabulate(display_df[final_cols], headers='keys', tablefmt='fancy_grid', showindex=False))
    print("\n*HSS Breakdown: G=Goal Action, P=Parity/Close Score, D=Drama/Comeback Bonus, LPF=League Parity Factor (Upset Context).")

if __name__ == "__main__":
    main()