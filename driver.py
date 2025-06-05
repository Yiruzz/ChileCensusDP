from config import DATA_PATH_PROCESSED
from top_down import TopDown
import time

from os import path
        
def main():
    '''Main function to run the TopDown algorithm.'''

    topdown = TopDown()

    time_start = time.time()

    # Check if a prevous run exists
    if DATA_PATH_PROCESSED is not None and path.exists(DATA_PATH_PROCESSED):
        print(f"Data already processed detected. Loading from {DATA_PATH_PROCESSED} to recover the already processed data.\n")
        topdown.resume_run()    
    else:
        print(f'Running TopDown alogorithm from scratch...\n')
        topdown.run()
    
    time_end = time.time()

    topdown.check_correctness()

    print(f"TopDown algorithm finished in {time_end - time_start:.2f} seconds.\n")

if __name__ == "__main__":
    main()