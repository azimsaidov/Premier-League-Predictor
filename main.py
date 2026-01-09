"""
Premier League Excitement Analyzer - Unified Application
Combines retrospective analysis and future predictions in one user-friendly interface.
"""
import sys
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import Config
from logger import setup_logging, get_logger
from excitement_ranker_improved import ExcitementRanker
from excitement_predictor import ExcitementPredictor


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
        print("\n" + "="*70)
        print("🏆 PREMIER LEAGUE EXCITEMENT ANALYZER 🏆")
        print("="*70)
        print("📊 Analyze past matches | 🔮 Predict future matches")
        print("="*70)
    
    def display_main_menu(self):
        """Display the main menu options"""
        print("\n🎯 MAIN MENU:")
        print("1. 📈 Analyze Past Matches")
        print("2. 🔮 Predict Future Matches")
        print("3. ℹ️  About")
        print("4. ❌ Exit")
        print("-" * 40)
    
    def _handle_exit(self):
        """Handle user exit (Ctrl+C or EOF)"""
        print("\n👋 Goodbye!")
        sys.exit(0)
    
    def get_user_choice(self) -> str:
        """Get user's menu choice with validation"""
        while True:
            try:
                choice = input("Enter your choice (1-4): ").strip()
                if choice in ['1', '2', '3', '4']:
                    return choice
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
            except (KeyboardInterrupt, EOFError):
                self._handle_exit()
    
    def analyze_past_matches(self):
        """Handle past match analysis"""
        print("\n📈 ANALYZING PAST MATCHES")
        print("-" * 30)
        
        while True:
            try:
                days_back_str = input("Enter number of DAYS BACK to analyze (e.g., 7): ")
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
            except (KeyboardInterrupt, EOFError):
                self._handle_exit()
        
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
        
        while True:
            try:
                days_ahead_str = input("Enter number of DAYS AHEAD to predict (e.g., 7): ")
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
            except (KeyboardInterrupt, EOFError):
                self._handle_exit()
        
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
        print("⚽ Data Source: Football Data API")
        print("\n🎯 FEATURES:")
        print("• Retrospective match analysis with excitement scoring")
        print("• Future match prediction using the same algorithm")
        print("• Multi-factor scoring: Goal Action (4.0), Parity (3.0), Drama (5.0), LPF (2.0)")
        print("\n📊 SCORING: G=Goals, P=Parity/Closeness, D=Drama/Comebacks, LPF=Upsets")
        print("🎮 Use menu options 1-2 to analyze past or predict future matches")
        
        self.ask_continue()
    
    def ask_continue(self):
        """Ask if user wants to continue or return to main menu"""
        print("\n" + "-" * 50)
        while True:
            try:
                choice = input("Return to main menu? (y/n): ").strip().lower()
                if choice in ['y', 'yes']:
                    return
                elif choice in ['n', 'no']:
                    print("👋 Thank you for using Premier League Excitement Analyzer!")
                    sys.exit(0)
                print("❌ Please enter 'y' for yes or 'n' for no.")
            except (KeyboardInterrupt, EOFError):
                self._handle_exit()
    
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
                    
            except (KeyboardInterrupt, EOFError):
                self._handle_exit()
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

