"""
Premier League Excitement Analyzer - Unified Application
Combines retrospective analysis and future predictions in one user-friendly interface.
"""
import os
import sys
from datetime import datetime
from typing import Optional

# Import our custom modules
from config import Config
from logger import setup_logging, get_logger
from excitement_ranker_improved import ExcitementRanker
from excitement_predictor import ExcitementPredictor

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


class PremierLeagueExcitementApp:
    """Unified application for Premier League excitement analysis and prediction"""
    
    def __init__(self):
        self.config = None
        self.logger = None
        self.ranker = None
        self.predictor = None
    
    def initialize(self) -> bool:
        """Initialize the application with configuration and logging"""
        try:
            # Set up logging
            self.logger = setup_logging()
            
            # Load configuration
            self.config = Config.from_env()
            self.config.validate()
            
            # Initialize components
            self.ranker = ExcitementRanker(self.config)
            self.predictor = ExcitementPredictor(self.config)
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Initialization error: {e}")
            else:
                print(f"Error: {e}")
            return False
    
    def display_welcome(self):
        """Display welcome message and application info"""
        print("\n" + "="*80)
        print("🏆 PREMIER LEAGUE EXCITEMENT ANALYZER 🏆")
        print("="*80)
        print("📊 Analyze past matches for excitement rankings")
        print("🔮 Predict future matches for viewing recommendations")
        print("⚽ Powered by Football Data API")
        print("="*80)
    
    def display_main_menu(self):
        """Display the main menu options"""
        print("\n🎯 MAIN MENU:")
        print("1. 📈 Analyze Past Matches (Retrospective Ranking)")
        print("2. 🔮 Predict Future Matches (Excitement Prediction)")
        print("3. ℹ️  About This Application")
        print("4. ❌ Exit")
        print("-" * 50)
    
    def get_user_choice(self) -> str:
        """Get user's menu choice with validation"""
        while True:
            try:
                choice = input("Enter your choice (1-4): ").strip()
                if choice in ['1', '2', '3', '4']:
                    return choice
                else:
                    print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
            except EOFError:
                print("\n👋 Goodbye!")
                sys.exit(0)
    
    def analyze_past_matches(self):
        """Handle past match analysis"""
        print("\n📈 ANALYZING PAST MATCHES")
        print("-" * 30)
        print("This will rank completed Premier League matches by excitement level.")
        print("The analysis considers:")
        print("• Goal action and scoring")
        print("• Match closeness and parity")
        print("• Late drama and comebacks")
        print("• League standings context")
        
        while True:
            try:
                days_back_str = input("\nEnter number of DAYS BACK to analyze (e.g., 7 for last week): ")
                if not days_back_str.isdigit():
                    raise ValueError("Please enter a valid number.")
                
                days_back = int(days_back_str)
                if days_back <= 0:
                    raise ValueError("Days back must be a positive number.")
                if days_back > 365:
                    raise ValueError("Please enter a reasonable number (max 365 days).")
                
                break
                
            except ValueError as e:
                print(f"❌ {e}")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
        
        try:
            self.logger.info(f"Starting past match analysis for {days_back} days back")
            self.ranker.run(days_back)
            
            # Ask if user wants to continue
            self.ask_continue()
            
        except Exception as e:
            self.logger.error(f"Error in past match analysis: {e}")
            print(f"❌ An error occurred: {e}")
            self.ask_continue()
    
    def predict_future_matches(self):
        """Handle future match prediction"""
        print("\n🔮 PREDICTING FUTURE MATCHES")
        print("-" * 30)
        print("This will predict excitement levels for upcoming Premier League matches.")
        print("Predictions are based on:")
        print("• Team form and league position")
        print("• Historical scoring patterns")
        print("• Home advantage factors")
        print("• Same excitement algorithm as past analysis")
        
        while True:
            try:
                days_ahead_str = input("\nEnter number of DAYS AHEAD to predict (e.g., 7 for next week): ")
                if not days_ahead_str.isdigit():
                    raise ValueError("Please enter a valid number.")
                
                days_ahead = int(days_ahead_str)
                if days_ahead <= 0:
                    raise ValueError("Days ahead must be a positive number.")
                if days_ahead > 90:
                    raise ValueError("Please enter a reasonable number (max 90 days).")
                
                break
                
            except ValueError as e:
                print(f"❌ {e}")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
        
        try:
            self.logger.info(f"Starting future match prediction for {days_ahead} days ahead")
            self.predictor.run(days_ahead)
            
            # Ask if user wants to continue
            self.ask_continue()
            
        except Exception as e:
            self.logger.error(f"Error in future match prediction: {e}")
            print(f"❌ An error occurred: {e}")
            self.ask_continue()
    
    def show_about(self):
        """Display information about the application"""
        print("\nℹ️  ABOUT THIS APPLICATION")
        print("-" * 30)
        print("🏆 Premier League Excitement Analyzer")
        print("📅 Created: October 2025")
        print("⚽ Data Source: Football Data API")
        print("")
        print("🎯 FEATURES:")
        print("• Retrospective match analysis with excitement scoring")
        print("• Future match prediction using the same algorithm")
        print("• Multi-factor scoring system:")
        print("  - Goal Action (Weight: 4.0)")
        print("  - Parity/Closeness (Weight: 3.0)")
        print("  - Late Drama (Weight: 5.0)")
        print("  - League Parity Factor (Weight: 2.0)")
        print("")
        print("🔧 TECHNICAL DETAILS:")
        print("• Object-oriented Python design")
        print("• Environment variable configuration")
        print("• Professional logging system")
        print("• Comprehensive error handling")
        print("• Unit test coverage")
        print("")
        print("📊 SCORING EXPLANATION:")
        print("• G = Goal Action: Total goals scored")
        print("• P = Parity: How close the match was")
        print("• D = Drama: Late comebacks and high-scoring draws")
        print("• LPF = League Parity Factor: Upsets and competitive matchups")
        print("")
        print("🎮 HOW TO USE:")
        print("1. Choose 'Analyze Past Matches' to rank completed games")
        print("2. Choose 'Predict Future Matches' to see upcoming excitement")
        print("3. Use the rankings to plan your viewing schedule!")
        
        self.ask_continue()
    
    def ask_continue(self):
        """Ask if user wants to continue or return to main menu"""
        print("\n" + "-" * 50)
        while True:
            try:
                choice = input("Would you like to return to the main menu? (y/n): ").strip().lower()
                if choice in ['y', 'yes']:
                    return
                elif choice in ['n', 'no']:
                    print("👋 Thank you for using Premier League Excitement Analyzer!")
                    sys.exit(0)
                else:
                    print("❌ Please enter 'y' for yes or 'n' for no.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
            except EOFError:
                print("\n👋 Goodbye!")
                sys.exit(0)
    
    def run(self):
        """Main application loop"""
        # Initialize the application
        if not self.initialize():
            print("❌ Failed to initialize application. Please check your configuration.")
            sys.exit(1)
        
        # Display welcome message
        self.display_welcome()
        
        # Main application loop
        while True:
            try:
                self.display_main_menu()
                choice = self.get_user_choice()
                
                if choice == '1':
                    self.analyze_past_matches()
                elif choice == '2':
                    self.predict_future_matches()
                elif choice == '3':
                    self.show_about()
                elif choice == '4':
                    print("👋 Thank you for using Premier League Excitement Analyzer!")
                    break
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                print(f"❌ An unexpected error occurred: {e}")
                print("Returning to main menu...")
                continue


def main():
    """Main entry point"""
    app = PremierLeagueExcitementApp()
    app.run()


if __name__ == "__main__":
    main()

