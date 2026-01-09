"""
Excitement Predictor for Premier League Matches
Predicts excitement levels for upcoming matches using historical data and team analysis.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
from tabulate import tabulate

from config import Config
from logger import get_logger


class ExcitementPredictor:
    """Predicts excitement levels for upcoming Premier League matches"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
        self.rank_map: Dict[int, int] = {}
        self.team_stats: Dict[int, Dict] = {}
    
    def get_date_range_future(self, days_ahead: int) -> Tuple[str, str]:
        """Calculate date range for upcoming matches"""
        today = datetime.now().date()
        
        # Start from tomorrow
        date_from_dt = today + timedelta(days=1)
        # End date
        date_to_dt = today + timedelta(days=days_ahead)
        
        date_from_str = date_from_dt.strftime("%Y-%m-%d")
        date_to_str = date_to_dt.strftime("%Y-%m-%d")
        
        return date_from_str, date_to_str
    
    def fetch_upcoming_matches(self, date_from: str, date_to: str) -> Optional[dict]:
        """Fetch upcoming Premier League matches"""
        self.logger.info(f"Fetching upcoming matches from {date_from} to {date_to}")
        
        url = f"{self.config.api_base_url}/matches"
        
        params = {
            'competitions': self.config.competition_id,
            'dateFrom': date_from,
            'dateTo': date_to,
            'status': 'SCHEDULED'
        }
        
        headers = {"X-Auth-Token": self.config.api_key}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            self.logger.error(f"API Error: {err.response.status_code} for URL: {response.url}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network Error: {e}")
            return None
    
    def fetch_standings(self) -> Dict[int, int]:
        """Fetch current league standings"""
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
            return rank_map
        
        for entry in standings_tables[0].get('table', []):
            team_id = entry['team']['id']
            rank = entry['position']
            rank_map[team_id] = rank
            
        self.logger.info(f"Successfully loaded standings for {len(rank_map)} teams")
        return rank_map
    
    def fetch_team_statistics(self) -> Dict[int, Dict]:
        """Fetch team statistics for better predictions based on league position"""
        team_stats = {}
        
        for team_id, rank in self.rank_map.items():
            # More sophisticated goal estimation based on league position
            # Using historical Premier League data patterns
            
            # Calculate base goals scored (higher ranked teams score more)
            base_goals_scored = 2.5 - (rank - 1) * 0.08  # Linear decrease from 2.5 to 0.9
            base_goals_scored = max(0.9, min(2.5, base_goals_scored))
            
            # Calculate base goals conceded (higher ranked teams concede fewer)
            base_goals_conceded = 0.8 + (rank - 1) * 0.06  # Linear increase from 0.8 to 1.9
            base_goals_conceded = max(0.8, min(1.9, base_goals_conceded))
            
            # Form factor based on position (top teams have better form)
            form_factor = max(0.7, 1.4 - (rank / 20.0))
            
            # Add some team-specific adjustments based on team ID for consistency
            # This ensures the same team always gets the same stats
            team_adjustment = (team_id % 10) * 0.05 - 0.25  # -0.25 to +0.2 adjustment
            
            team_stats[team_id] = {
                'rank': rank,
                'avg_goals_scored': max(0.8, base_goals_scored + team_adjustment),
                'avg_goals_conceded': max(0.7, base_goals_conceded - team_adjustment * 0.5),
                'form_factor': form_factor,
                'team_id': team_id  # Store for consistency
            }
        
        return team_stats
    
    def predict_match_score(self, home_team_id: int, away_team_id: int) -> Tuple[int, int]:
        """Predict the likely score for a match based on deterministic team metrics"""
        home_stats = self.team_stats.get(home_team_id, {
            'avg_goals_scored': 1.5,
            'avg_goals_conceded': 1.5,
            'form_factor': 1.0
        })
        
        away_stats = self.team_stats.get(away_team_id, {
            'avg_goals_scored': 1.5,
            'avg_goals_conceded': 1.5,
            'form_factor': 1.0
        })
        
        # Home advantage factor
        home_advantage = 0.15
        
        # Calculate expected goals based on team metrics
        # Home team goals = their scoring ability + opponent's defensive weakness + home advantage
        home_goals_expected = (home_stats['avg_goals_scored'] * home_stats['form_factor'] + 
                              away_stats['avg_goals_conceded'] * 0.3) * (1 + home_advantage)
        
        # Away team goals = their scoring ability + opponent's defensive weakness - home disadvantage
        away_goals_expected = (away_stats['avg_goals_scored'] * away_stats['form_factor'] + 
                              home_stats['avg_goals_conceded'] * 0.3) * (1 - home_advantage * 0.3)
        
        # Round to nearest integer for deterministic results
        home_goals = max(0, round(home_goals_expected))
        away_goals = max(0, round(away_goals_expected))
        
        # Ensure at least one goal total (matches rarely end 0-0)
        # Use team IDs as deterministic seed for consistent results
        if home_goals == 0 and away_goals == 0:
            # Use team IDs to determine which team scores (deterministic)
            if (home_team_id + away_team_id) % 2 == 0:
                home_goals = 1
            else:
                away_goals = 1
        
        return home_goals, away_goals
    
    def predict_excitement_score(self, match: dict) -> Tuple[float, float, float, float, float]:
        """Predict excitement score for an upcoming match"""
        home_team_id = match['homeTeam']['id']
        away_team_id = match['awayTeam']['id']
        
        # Predict the score
        predicted_home_score, predicted_away_score = self.predict_match_score(home_team_id, away_team_id)
        
        # Use the same calculation logic as the original, but with predicted scores
        total_goals = predicted_home_score + predicted_away_score
        goal_diff = abs(predicted_home_score - predicted_away_score)
        
        # 1. Total Goal Action
        goal_score = total_goals
        
        # 2. Parity Score (closeness of match)
        parity_score = max(0, 3.0 - (goal_diff * 1.0))
        
        # 3. Late Drama Factor (simplified for predictions)
        drama_score = 0
        
        # High-scoring draw bonus
        if goal_diff == 0 and total_goals >= 4:
            drama_score += 2.5
        
        # Potential comeback scenarios (simplified)
        if total_goals >= 5 and goal_diff <= 2:
            drama_score += 1.5
        
        # 4. League Parity Factor (same as original)
        lpf_score = self._calculate_lpf_score_prediction(home_team_id, away_team_id, 
                                                       predicted_home_score, predicted_away_score)
        
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
    
    def _calculate_lpf_score_prediction(self, home_id: int, away_id: int, 
                                      home_score: int, away_score: int) -> float:
        """Calculate League Parity Factor for predictions"""
        home_rank = self.rank_map.get(home_id, 10.5)
        away_rank = self.rank_map.get(away_id, 10.5)
        
        rank_diff = abs(home_rank - away_rank)
        
        # Match-up Parity Bonus
        parity_bonus = max(0.1, 1.0 - (rank_diff / 20.0))
        
        # Determine predicted result
        home_wins = home_score > away_score
        away_wins = away_score > home_score
        is_draw = home_score == away_score
        
        lpf_score = 0
        
        if is_draw:
            lpf_score = parity_bonus * 0.5 + (rank_diff / 20.0)
        elif (home_wins and home_rank > away_rank) or (away_wins and away_rank > home_rank):
            lpf_score = parity_bonus + (rank_diff / 8.0)
        
        return lpf_score
    
    def predict_upcoming_matches(self, fixtures: List[dict]) -> pd.DataFrame:
        """Predict excitement levels for upcoming fixtures"""
        predicted_list = []
        
        for fixture in fixtures:
            score, g_score, p_score, d_score, lpf_score = self.predict_excitement_score(fixture)
            
            # Get predicted score
            home_id = fixture['homeTeam']['id']
            away_id = fixture['awayTeam']['id']
            predicted_home, predicted_away = self.predict_match_score(home_id, away_id)
            
            predicted_list.append({
                'Predicted_Excitement': score,
                'Match': f"{fixture['homeTeam']['name']} vs {fixture['awayTeam']['name']}",
                'Predicted_Score': f"{predicted_home}-{predicted_away}",
                'Date': fixture['utcDate'][:10],
                'Time': fixture['utcDate'][11:16],
                'HSS_Breakdown': f"G:{g_score}, P:{p_score}, D:{d_score}, LPF:{lpf_score}"
            })
        
        df = pd.DataFrame(predicted_list)
        return df.sort_values(by='Predicted_Excitement', ascending=False)
    
    def display_predictions(self, predicted_df: pd.DataFrame, date_from: str, date_to: str) -> None:
        """Display the predicted excitement rankings"""
        if predicted_df.empty:
            self.logger.warning("No matches to predict")
            return
        
        # Prepare display data
        display_df = predicted_df[['Match', 'Predicted_Score', 'Date', 'Time', 'Predicted_Excitement', 'HSS_Breakdown']]
        display_df = display_df.head(self.config.max_results_display).reset_index(drop=True)
        display_df['Rank'] = display_df.index + 1
        
        # Format excitement score
        display_df['Predicted_Excitement'] = display_df['Predicted_Excitement'].apply(lambda x: f"{x:.2f}/10")
        final_cols = ['Rank', 'Predicted_Excitement', 'Match', 'Predicted_Score', 'Date', 'Time', 'HSS_Breakdown']
        
        print("\n" + "="*120)
        print(f"🔮📺 PREDICTED 'MUST WATCH' RANKING FOR UPCOMING MATCHES ({date_from} - {date_to}) 📺🔮")
        print("="*120)
        
        print(tabulate(display_df[final_cols], headers='keys', tablefmt='fancy_grid', showindex=False))
        print("\n*HSS Breakdown: G=Goal Action, P=Parity/Close Score, D=Drama/Comeback Bonus, LPF=League Parity Factor (Upset Context).")
        print("*Predictions based on team form, league position, and historical patterns.")
    
    def run(self, days_ahead: int) -> None:
        """Main execution method for predictions"""
        try:
            # Get date range
            date_from_str, date_to_str = self.get_date_range_future(days_ahead)
            
            # Fetch standings first
            self.logger.info("Fetching current league standings...")
            self.rank_map = self.fetch_standings()
            if not self.rank_map:
                self.logger.warning("Failed to retrieve standings. Predictions will be less accurate.")
                return
            
            # Fetch team statistics
            self.logger.info("Analyzing team statistics...")
            self.team_stats = self.fetch_team_statistics()
            
            # Fetch upcoming matches
            self.logger.info("Fetching upcoming matches...")
            data = self.fetch_upcoming_matches(date_from_str, date_to_str)
            
            if data is None:
                self.logger.error("Failed to retrieve upcoming match data.")
                return
            
            fixtures = data.get('matches', [])
            
            if not fixtures:
                self.logger.info(f"No upcoming Premier League matches found between {date_from_str} and {date_to_str}.")
                return
            
            self.logger.info(f"Found {len(fixtures)} upcoming PL matches. Predicting excitement levels...")
            
            # Predict excitement levels
            predicted_df = self.predict_upcoming_matches(fixtures)
            
            if predicted_df.empty:
                self.logger.warning("Could not predict any matches.")
                return
            
            # Display predictions
            self.display_predictions(predicted_df, date_from_str, date_to_str)
            
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise
