"""
Configuration module for Excitement Ranker
Handles all configuration settings and environment variables
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration settings for the Excitement Ranker"""
    
    # API Settings
    api_key: str
    api_base_url: str = "https://api.football-data.org/v4"
    competition_id: int = 2021
    
    # Scoring Weights
    goal_weight: float = 4.0
    parity_weight: float = 3.0
    drama_weight: float = 5.0
    lpf_weight: float = 2.0
    
    # Normalization
    max_realistic_raw_score: float = 85.0
    
    # Display Settings
    max_results_display: int = 10
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        api_key = os.getenv('FOOTBALL_API_KEY')
        if not api_key:
            raise ValueError(
                "FOOTBALL_API_KEY environment variable is required. "
                "Please set it or create a .env file with your API key."
            )
        
        return cls(
            api_key=api_key,
            api_base_url=os.getenv('FOOTBALL_API_BASE_URL', cls.api_base_url),
            competition_id=int(os.getenv('PL_COMPETITION_ID', cls.competition_id)),
            goal_weight=float(os.getenv('GOAL_WEIGHT', cls.goal_weight)),
            parity_weight=float(os.getenv('PARITY_WEIGHT', cls.parity_weight)),
            drama_weight=float(os.getenv('DRAMA_WEIGHT', cls.drama_weight)),
            lpf_weight=float(os.getenv('LPF_WEIGHT', cls.lpf_weight)),
            max_realistic_raw_score=float(os.getenv('MAX_REALISTIC_RAW_SCORE', cls.max_realistic_raw_score)),
            max_results_display=int(os.getenv('MAX_RESULTS_DISPLAY', cls.max_results_display))
        )
    
    def validate(self) -> None:
        """Validate configuration values"""
        if not self.api_key or self.api_key == "your_api_key_here":
            raise ValueError("Invalid API key")
        
        if self.competition_id <= 0:
            raise ValueError("Competition ID must be positive")
        
        if any(w <= 0 for w in [self.goal_weight, self.parity_weight, self.drama_weight, self.lpf_weight]):
            raise ValueError("All weights must be positive")
        
        if self.max_realistic_raw_score <= 0:
            raise ValueError("Max realistic raw score must be positive")
