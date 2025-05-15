from config import DATA_PATH_PROCESSED
from top_down import TopDown

from os import path
        
def main():
    '''Main function to run the TopDown algorithm.'''

    topdown = TopDown()
    
    # Check if a prevous run exists
    if path.exists(DATA_PATH_PROCESSED):
        print(f"Data already processed detected. Loading from {DATA_PATH_PROCESSED} to recover the already processed data.\n")
        topdown.resume_run()    
    else:
        print(f'Running TopDown alogorithm from scratch...\n')
        topdown.run()
    
    topdown.check_correctness()

if __name__ == "__main__":
    main()