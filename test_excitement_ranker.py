"""
Unit tests for Excitement Ranker
Tests the core scoring algorithm and configuration
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from excitement_ranker_improved import ExcitementRanker


class TestConfig(unittest.TestCase):
    """Test configuration management"""
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Valid config
        config = Config(
            api_key="test_key",
            competition_id=2021,
            goal_weight=4.0,
            parity_weight=3.0,
            drama_weight=5.0,
            lpf_weight=2.0,
            max_realistic_raw_score=85.0
        )
        config.validate()  # Should not raise
        
        # Invalid API key
        with self.assertRaises(ValueError):
            Config(api_key="").validate()
        
        # Invalid weights
        with self.assertRaises(ValueError):
            Config(api_key="test", goal_weight=-1.0).validate()


class TestExcitementRanker(unittest.TestCase):
    """Test the main ExcitementRanker class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config(
            api_key="test_key",
            competition_id=2021,
            goal_weight=4.0,
            parity_weight=3.0,
            drama_weight=5.0,
            lpf_weight=2.0,
            max_realistic_raw_score=85.0
        )
        self.ranker = ExcitementRanker(self.config)
        
        # Sample match data
        self.sample_match = {
            'homeTeam': {'id': 1, 'name': 'Team A'},
            'awayTeam': {'id': 2, 'name': 'Team B'},
            'score': {
                'fullTime': {'home': 2, 'away': 1},
                'halfTime': {'home': 1, 'away': 0}
            },
            'utcDate': '2024-01-01T15:00:00Z'
        }
        
        # Sample standings
        self.ranker.rank_map = {1: 5, 2: 10}  # Team A ranked 5th, Team B ranked 10th
    
    def test_calculate_excitement_score_basic(self):
        """Test basic excitement score calculation"""
        score, g_score, p_score, d_score, lpf_score = self.ranker.calculate_excitement_score(self.sample_match)
        
        # Basic checks
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 10.0)
        self.assertGreater(g_score, 0)  # Should have goal action
        self.assertGreater(p_score, 0)  # Should have parity score
    
    def test_calculate_excitement_score_high_scoring(self):
        """Test excitement score for high-scoring match"""
        high_scoring_match = self.sample_match.copy()
        high_scoring_match['score']['fullTime'] = {'home': 4, 'away': 3}
        
        score, g_score, p_score, d_score, lpf_score = self.ranker.calculate_excitement_score(high_scoring_match)
        
        # High-scoring match should have high goal action
        self.assertGreater(g_score, 20)  # 7 goals * 4.0 weight = 28
    
    def test_calculate_excitement_score_draw(self):
        """Test excitement score for draw"""
        draw_match = self.sample_match.copy()
        draw_match['score']['fullTime'] = {'home': 2, 'away': 2}
        
        score, g_score, p_score, d_score, lpf_score = self.ranker.calculate_excitement_score(draw_match)
        
        # Draw should have high parity score
        self.assertEqual(p_score, 9.0)  # 3.0 * 3.0 weight = 9.0
    
    def test_calculate_excitement_score_comeback(self):
        """Test excitement score for comeback scenario"""
        comeback_match = self.sample_match.copy()
        comeback_match['score'] = {
            'fullTime': {'home': 3, 'away': 2},
            'halfTime': {'home': 0, 'away': 2}  # 2-0 halftime, 3-2 final
        }
        
        score, g_score, p_score, d_score, lpf_score = self.ranker.calculate_excitement_score(comeback_match)
        
        # Should have drama points for comeback
        self.assertGreater(d_score, 0)
    
    def test_calculate_excitement_score_upset(self):
        """Test excitement score for upset (lower ranked team wins)"""
        upset_match = self.sample_match.copy()
        upset_match['score']['fullTime'] = {'home': 1, 'away': 2}  # Team B (ranked 10th) beats Team A (ranked 5th)
        
        score, g_score, p_score, d_score, lpf_score = self.ranker.calculate_excitement_score(upset_match)
        
        # Should have LPF points for upset
        self.assertGreater(lpf_score, 0)
    
    def test_calculate_excitement_score_missing_data(self):
        """Test excitement score with missing score data"""
        incomplete_match = self.sample_match.copy()
        incomplete_match['score']['fullTime'] = {'home': None, 'away': 1}
        
        score, g_score, p_score, d_score, lpf_score = self.ranker.calculate_excitement_score(incomplete_match)
        
        # Should return zeros for incomplete data
        self.assertEqual(score, 0)
        self.assertEqual(g_score, 0)
        self.assertEqual(p_score, 0)
        self.assertEqual(d_score, 0)
        self.assertEqual(lpf_score, 0)
    
    def test_drama_score_calculation(self):
        """Test drama score calculation specifically"""
        # Test comeback scenario
        comeback_match = self.sample_match.copy()
        comeback_match['score'] = {
            'fullTime': {'home': 2, 'away': 1},
            'halfTime': {'home': 0, 'away': 2}  # 2-0 halftime, 2-1 final
        }
        
        drama_score = self.ranker._calculate_drama_score(comeback_match, 2, 1, 1)
        self.assertGreater(drama_score, 0)
        
        # Test high-scoring draw
        draw_match = self.sample_match.copy()
        draw_match['score']['fullTime'] = {'home': 3, 'away': 3}
        
        drama_score = self.ranker._calculate_drama_score(draw_match, 3, 3, 0)
        self.assertGreater(drama_score, 0)
    
    def test_lpf_score_calculation(self):
        """Test League Parity Factor calculation"""
        # Test upset scenario
        lpf_score = self.ranker._calculate_lpf_score(self.sample_match, 1, 2)  # Lower ranked team wins
        self.assertGreater(lpf_score, 0)
        
        # Test draw scenario
        lpf_score = self.ranker._calculate_lpf_score(self.sample_match, 2, 2)  # Draw
        self.assertGreater(lpf_score, 0)
    
    def test_date_range_calculation(self):
        """Test date range calculation"""
        date_from, date_to_api, date_to_display = self.ranker.get_date_range_api(7)
        
        # Basic format checks
        self.assertEqual(len(date_from), 10)  # YYYY-MM-DD format
        self.assertEqual(len(date_to_api), 10)
        self.assertEqual(len(date_to_display), 10)
        
        # Should be different dates
        self.assertNotEqual(date_from, date_to_api)
        self.assertNotEqual(date_from, date_to_display)


if __name__ == '__main__':
    unittest.main()
