# Excitement Ranker - Premier League Match Analysis

A sophisticated tool that analyzes completed Premier League matches and ranks them by excitement level using multiple weighted factors including goal action, parity, late drama, and league context.

## Features

- **Multi-Factor Scoring**: Considers goals, match closeness, late drama, and league standings
- **League Parity Factor**: Rewards upsets and competitive matchups based on current standings
- **Late Drama Detection**: Identifies comebacks and high-scoring draws
- **Configurable Weights**: Easily adjust scoring factors via environment variables
- **Professional Logging**: Structured logging with multiple levels
- **Error Handling**: Robust API error handling and input validation
- **Unit Tests**: Comprehensive test coverage for core algorithms

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Copy the example configuration file:
```bash
cp config.env.example .env
```

Edit `.env` and add your Football Data API key:
```
FOOTBALL_API_KEY=your_actual_api_key_here
```

### 3. Run the Unified Application

```bash
python main.py
```

This will launch the main menu where you can choose between:
- **Analyze Past Matches**: Rank completed games by excitement
- **Predict Future Matches**: Predict excitement for upcoming games
- **About**: Learn more about the application

## Configuration

The application uses environment variables for configuration. See `config.env.example` for all available options:

- `FOOTBALL_API_KEY`: Your Football Data API key (required)
- `GOAL_WEIGHT`: Weight for goal action factor (default: 4.0)
- `PARITY_WEIGHT`: Weight for match closeness factor (default: 3.0)
- `DRAMA_WEIGHT`: Weight for late drama factor (default: 5.0)
- `LPF_WEIGHT`: Weight for league parity factor (default: 2.0)
- `MAX_REALISTIC_RAW_SCORE`: Normalization factor (default: 85.0)

## Scoring Algorithm

The excitement score combines four weighted factors:

1. **Goal Action (Weight: 4.0)**: Total goals scored in the match
2. **Parity Score (Weight: 3.0)**: Rewards close matches (penalizes large goal differences)
3. **Late Drama Factor (Weight: 5.0)**: 
   - Large comeback detection (2+ goal halftime lead → ≤1 goal final difference)
   - High-scoring draw bonus (4+ goals in a draw)
4. **League Parity Factor (Weight: 2.0)**:
   - Match-up parity bonus (rewards games between similarly ranked teams)
   - Upset bonus (extra points when lower-ranked teams avoid defeat)

Final score is normalized to a 1-10 scale.

## Running Tests

```bash
python test_excitement_ranker.py
```

## File Structure

- `main.py`: **Unified application** - Start here! Main menu with both features
- `excitement_ranker_improved.py`: Retrospective match analysis
- `excitement_predictor.py`: Future match prediction
- `config.py`: Configuration management
- `logger.py`: Logging utilities
- `test_excitement_ranker.py`: Unit tests
- `requirements.txt`: Python dependencies
- `config.env.example`: Environment variables template

## Improvements Made

### Security
- ✅ Moved API key to environment variables
- ✅ Added configuration validation

### Code Quality
- ✅ Object-oriented design with ExcitementRanker class
- ✅ Separated concerns (config, logging, main logic)
- ✅ Improved error handling and input validation
- ✅ Professional logging system
- ✅ Comprehensive documentation

### Maintainability
- ✅ Configurable scoring weights
- ✅ Modular design for easy testing
- ✅ Type hints and docstrings
- ✅ Unit test coverage

### Performance
- ✅ Timeout handling for API calls
- ✅ Better error recovery
- ✅ Structured data handling

## API Requirements

You'll need a Football Data API key from [football-data.org](https://www.football-data.org/). The free tier provides:
- 10 requests per minute
- 1,000 requests per month

## Example Output

```
=========================================================================================================
🎬📺 ENHANCED RETROSPECTIVE 'BEST TO WATCH' RANKING (2024-01-01 - 2024-01-08) 📺🎬
=========================================================================================================
┌──────┬─────────────────┬─────────────────────────────┬────────┬────────────┬─────────────────────────────┐
│ Rank │ Excitement_Score │ Match                        │ Result │ Date       │ HSS_Breakdown               │
├──────┼─────────────────┼─────────────────────────────┼────────┼────────────┼─────────────────────────────┤
│    1 │ 8.45/10         │ Manchester City vs Arsenal  │ 3-2    │ 2024-01-05 │ G:28.0, P:3.0, D:12.5, LPF:4.2 │
│    2 │ 7.89/10         │ Liverpool vs Chelsea       │ 2-2    │ 2024-01-03 │ G:16.0, P:9.0, D:12.5, LPF:2.1 │
└──────┴─────────────────┴─────────────────────────────┴────────┴────────────┴─────────────────────────────┘

*HSS Breakdown: G=Goal Action, P=Parity/Close Score, D=Drama/Comeback Bonus, LPF=League Parity Factor (Upset Context).
```

## License

This project is for educational and personal use. Please respect the Football Data API terms of service.
