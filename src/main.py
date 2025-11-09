try:
    from modules import *
    from movie_advisor import main as movie_advisor_main  # Import our new movie advisor
    from termcolor import colored

except ImportError as error:
    print("⚠️ Modules could not be imported: ", error)

sep_line = "-" * 50 # Graphical separator line in terminal

def main(): 
    print(colored("\nStarting Simple Movie Advisor...", "green"))
    movie_advisor_main()  # Run our new movie advisor

if __name__ == "__main__":
    main()
