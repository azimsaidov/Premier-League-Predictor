"""
Enhanced Excitement Ranker for Premier League Matches
Analyzes completed matches and ranks them by excitement level using multiple factors.
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
from tabulate import tabulate

# Import our custom modules
from config import Config
from logger import setup_logging, get_logger

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


class ExcitementRanker:
    """Main class for ranking football matches by excitement level"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
        self.rank_map: Dict[int, int] = {}
    
    def get_date_range_api(self, days_back: int) -> Tuple[str, str, str]:
        """Calculate date range strings needed for API calls"""
        today = datetime.now().date()
        
        # date_to_api: Tomorrow's date (API dateTo is exclusive)
        date_to_dt_api = today + timedelta(days=1)
        # date_from_dt: The starting point for the query period
        date_from_dt = today - timedelta(days=days_back)
        
        date_from_str = date_from_dt.strftime("%Y-%m-%d")
        date_to_str_api = date_to_dt_api.strftime("%Y-%m-%d")
        
        # Also return today's date string for display purposes
        return date_from_str, date_to_str_api, today.strftime("%Y-%m-%d")
    
    def fetch_data_single_call(self, date_from: str, date_to_api: str) -> Optional[dict]:
        """Fetch finished Premier League matches using a single API call"""
        self.logger.info(f"Fetching matches from {date_from} to {date_to_api}")
        
        url = f"{self.config.api_base_url}/matches"
        
        params = {
            'competitions': self.config.competition_id,
            'dateFrom': date_from,
            'dateTo': date_to_api,
            'status': 'FINISHED'
        }
        
        headers = {"X-Auth-Token": self.config.api_key}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            self.logger.error(f"API Error: {err.response.status_code} for URL: {response.url}")
            self.logger.error("Note: Check API limits or requested date range")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network Error: {e}")
            return None
    
    def fetch_standings(self) -> Dict[int, int]:
        """
        Fetch current league standings and return a map of {team_id: rank}
        """
        url = f"{self.config.api_base_url}/competitions/{self.config.competition_id}/standings"
        headers = {"X-Auth-Token": self.config.api_key}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching standings: {e}")
            return {}
        
        rank_map = {}
        standings_tables = data.get('standings', [])
        if not standings_tables:
            self.logger.warning("No standings data found")
            return rank_map
        
        # Assuming the first entry in 'standings' is the TOTAL league table
        for entry in standings_tables[0].get('table', []):
            team_id = entry['team']['id']
            rank = entry['position']
            rank_map[team_id] = rank
            
        self.logger.info(f"Successfully loaded standings for {len(rank_map)} teams")
        return rank_map
    
    def calculate_excitement_score(self, match: dict) -> Tuple[float, float, float, float, float]:
        """
        Calculate excitement score based on match metrics and league context
        
        Returns:
            Tuple of (excitement_score, goal_score, parity_score, drama_score, lpf_score)
        """
        home_score = match['score']['fullTime']['home']
        away_score = match['score']['fullTime']['away']
        
        if home_score is None or away_score is None:
            return 0, 0, 0, 0, 0
        
        total_goals = home_score + away_score
        goal_diff = abs(home_score - away_score)
        
        # 1. Total Goal Action
        goal_score = total_goals
        
        # 2. Parity Score (closeness of match)
        parity_score = max(0, 3.0 - (goal_diff * 1.0))
        
        # 3. Late Drama Factor
        drama_score = self._calculate_drama_score(match, home_score, away_score, goal_diff)
        
        # 4. League Parity Factor
        lpf_score = self._calculate_lpf_score(match, home_score, away_score)
        
        # Final calculation with configurable weights
        raw_score = (
            goal_score * self.config.goal_weight +
            parity_score * self.config.parity_weight +
            drama_score * self.config.drama_weight +
            lpf_score * self.config.lpf_weight
        )
        
        # Normalize against configured max score
        excitement_score = ((raw_score / self.config.max_realistic_raw_score) * 9.0) + 1.0
        excitement_score = min(10.0, excitement_score)
        
        # Return weighted breakdown for display
        return (
            round(excitement_score, 2),
            round(goal_score * self.config.goal_weight, 1),
            round(parity_score * self.config.parity_weight, 1),
            round(drama_score * self.config.drama_weight, 1),
            round(lpf_score * self.config.lpf_weight, 1)
        )
    
    def _calculate_drama_score(self, match: dict, home_score: int, away_score: int, goal_diff: int) -> float:
        """Calculate late drama factor"""
        drama_points = 0
        
        # Large Comeback Heuristic
        if match['score'].get('halfTime'):
            ht_home = match['score']['halfTime']['home']
            ht_away = match['score']['halfTime']['away']
            
            if ht_home is not None and ht_away is not None:
                ht_diff = abs(ht_home - ht_away)
                ft_diff = abs(home_score - away_score)
                
                # If halftime lead was large but final result was close
                if ht_diff >= 2 and ft_diff <= 1:
                    drama_points += 2.5
        
        # High-Scoring Draw Bonus
        if goal_diff == 0 and (home_score + away_score) >= 4:
            drama_points += 2.5
        
        return drama_points
    
    def _calculate_lpf_score(self, match: dict, home_score: int, away_score: int) -> float:
        """Calculate League Parity Factor"""
        home_id = match['homeTeam']['id']
        away_id = match['awayTeam']['id']
        
        # Get ranks, default to middle (10.5) if team missing from standings
        home_rank = self.rank_map.get(home_id, 10.5)
        away_rank = self.rank_map.get(away_id, 10.5)
        
        rank_diff = abs(home_rank - away_rank)
        
        # Match-up Parity Bonus: rewards games between similarly ranked teams
        parity_bonus = max(0.1, 1.0 - (rank_diff / 20.0))
        
        # Determine match result
        home_wins = home_score > away_score
        away_wins = away_score > home_score
        is_draw = home_score == away_score
        
        lpf_score = 0
        
        if is_draw:
            # Draw bonus: slightly boosted by rank difference
            lpf_score = parity_bonus * 0.5 + (rank_diff / 20.0)
        elif (home_wins and home_rank > away_rank) or (away_wins and away_rank > home_rank):
            # Underdog won: significant bonus based on upset size
            lpf_score = parity_bonus + (rank_diff / 8.0)
        
        return lpf_score
    
    def rank_completed_matches(self, fixtures: List[dict]) -> pd.DataFrame:
        """Apply excitement scoring to rank past fixtures"""
        ranked_list = []
        
        for fixture in fixtures:
            if fixture['score']['fullTime']['home'] is None:
                continue
            
            score, g_score, p_score, d_score, lpf_score = self.calculate_excitement_score(fixture)
            
            ranked_list.append({
                'Excitement_Score': score,
                'Match': f"{fixture['homeTeam']['name']} vs {fixture['awayTeam']['name']}",
                'Result': f"{fixture['score']['fullTime']['home']}-{fixture['score']['fullTime']['away']}",
                'Date': fixture['utcDate'][:10],
                'HSS_Breakdown': f"G:{g_score}, P:{p_score}, D:{d_score}, LPF:{lpf_score}"
            })
        
        df = pd.DataFrame(ranked_list)
        return df.sort_values(by='Excitement_Score', ascending=False)
    
    def display_results(self, ranked_df: pd.DataFrame, date_from: str, date_to: str) -> None:
        """Display the ranked results in a formatted table"""
        if ranked_df.empty:
            self.logger.warning("No matches to display")
            return
        
        # Prepare display data
        display_df = ranked_df[['Match', 'Result', 'Date', 'Excitement_Score', 'HSS_Breakdown']]
        display_df = display_df.head(self.config.max_results_display).reset_index(drop=True)
        display_df['Rank'] = display_df.index + 1
        
        # Format excitement score
        display_df['Excitement_Score'] = display_df['Excitement_Score'].apply(lambda x: f"{x:.2f}/10")
        final_cols = ['Rank', 'Excitement_Score', 'Match', 'Result', 'Date', 'HSS_Breakdown']
        
        print("\n" + "="*105)
        print(f"🎬📺 ENHANCED RETROSPECTIVE 'BEST TO WATCH' RANKING ({date_from} - {date_to}) 📺🎬")
        print("="*105)
        
        print(tabulate(display_df[final_cols], headers='keys', tablefmt='fancy_grid', showindex=False))
        print("\n*HSS Breakdown: G=Goal Action, P=Parity/Close Score, D=Drama/Comeback Bonus, LPF=League Parity Factor (Upset Context).")
    
    def run(self, days_back: int) -> None:
        """Main execution method"""
        try:
            # Get date range
            date_from_str, date_to_str_api, date_to_str_display = self.get_date_range_api(days_back)
            
            # Fetch standings first
            self.logger.info("Fetching current league standings...")
            self.rank_map = self.fetch_standings()
            if not self.rank_map:
                self.logger.warning("Failed to retrieve standings. Ranking will only use score data (LPF set to 0).")
            
            # Fetch matches
            self.logger.info("Fetching completed matches...")
            data = self.fetch_data_single_call(date_from_str, date_to_str_api)
            
            if data is None:
                self.logger.error("Failed to retrieve match data. Check the error output above or try a smaller 'DAYS BACK' number.")
                return
            
            fixtures = data.get('matches', [])
            
            if not fixtures:
                self.logger.info(f"No FINISHED Premier League matches found between {date_from_str} and {date_to_str_display}.")
                return
            
            self.logger.info(f"Found {len(fixtures)} completed PL matches. Ranking them now...")
            
            # Rank matches
            ranked_df = self.rank_completed_matches(fixtures)
            
            if ranked_df.empty:
                self.logger.warning("Could not rank any matches (missing score data).")
                return
            
            # Display results
            self.display_results(ranked_df, date_from_str, date_to_str_display)
            
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise


def main():
    """Main entry point"""
    # Set up logging
    logger = setup_logging()
    
    try:
        # Load configuration
        config = Config.from_env()
        config.validate()
        
        # Get user input
        days_back_str = input("Enter number of DAYS BACK to check for COMPLETED matches (e.g., 7 for last week): ")
        if not days_back_str.isdigit():
            raise ValueError("Invalid input. Please enter a valid number of days.")
        
        days_back = int(days_back_str)
        if days_back <= 0:
            raise ValueError("Days back must be a positive number.")
        
        # Create ranker and run
        ranker = ExcitementRanker(config)
        ranker.run(days_back)
        
    except ValueError as e:
        logger.error(f"Input error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
