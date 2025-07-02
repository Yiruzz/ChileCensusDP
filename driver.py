from top_down import TopDown
import time
        
def main():
    '''Main function to run the TopDown algorithm.'''

    GEO_COLUMNS = ['REGION', 'PROVINCIA', 'COMUNA', 'DC', 'ZC_LOC']
    PROCESS_UNTIL = 'DC'
    GEO_COLUMNS_TO_USE = GEO_COLUMNS[:GEO_COLUMNS.index(PROCESS_UNTIL) + 1]

    QUERIES = ['P08', 'P09'] # Sex and Age

    DATA_PATH = 'data/csv-personas-censo-2017/microdato_censo2017-personas/Microdato_Censo2017-Personas.csv'

    OUTPUT_PATH = 'data/out/'
    OUTPUT_FILE = 'personas_noisy_microdata_' + PROCESS_UNTIL + '_' + '_'.join(QUERIES) + '.csv'

    # Privacy parameters for the noise generation. First value for root, last for leaves.
    PRIVACY_PARAMETERS = [.1, .2, .4, .8, 1.6, 3.2]

    MECHANISM = 'discrete_laplace'

    # Edit Constraints
    GEO_CONSTRAINTS = {
        'REGION': [lambda x, y: x.sum() == y],
        'PROVINCIA': [lambda x, y: x.sum() == y],
        'COMUNA': [],
        'DC': [],
        'ZC_LOC': []
    }

    # Path of data that already has been processed
    # This is used to avoid reprocessing the data if it has already been processed.
    DATA_PATH_PROCESSED = 'data/out/personas_noisy_microdata_COMUNA_P08P09.csv'

    # Distance metric to use (manhattan, euclidean, cosine) if None no distance will be computed.
    # Only used for testing and analysis purposes.
    DISTANCE_METRIC = None

    topdown = TopDown()
    time_start = time.time()

    topdown.set_mechanism(MECHANISM)
    topdown.set_privacy_parameters(PRIVACY_PARAMETERS)

    topdown.set_geo_columns(GEO_COLUMNS_TO_USE)
    topdown.set_queries(QUERIES)

    topdown.set_constraints(GEO_CONSTRAINTS)

    topdown.set_distance_metric(DISTANCE_METRIC)

    topdown.read_data(DATA_PATH, sep=';')
    topdown.set_output_path(OUTPUT_PATH+OUTPUT_FILE)
    
    if DATA_PATH_PROCESSED: topdown.read_processed_data(DATA_PATH_PROCESSED, sep=';')

    # Run the TopDown algorithm
    topdown.run()
    time_end = time.time()
    print(f"TopDown algorithm finished in {time_end - time_start:.2f} seconds.\n")
    
    topdown.check_correctness()

if __name__ == "__main__":
    main()