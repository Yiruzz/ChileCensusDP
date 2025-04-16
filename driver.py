from top_down import TopDown
        
def main():
    '''Main function to run the TopDown algorithm.'''
    topdown = TopDown()
    topdown.init_routine()
    topdown.measurement_phase()
    topdown.estimation_phase()


if __name__ == "__main__":
    main()