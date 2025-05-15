from top_down import TopDown
        
def main():
    '''Main function to run the TopDown algorithm.'''
    topdown = TopDown()
    topdown.run()
    topdown.check_correctness()

if __name__ == "__main__":
    main()