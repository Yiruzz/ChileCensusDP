from top_down import TopDown
import time
        
def main():
    '''Main function to run the TopDown algorithm.'''

    # Define the geographic hierarchy, first element is the root and highest level of the hierarchy.
    GEO_COLUMNS = ['REGION', 'PROVINCIA', 'COMUNA', 'DC', 'ZC_LOC']
    PROCESS_UNTIL = 'COMUNA'
    GEO_COLUMNS_TO_USE = GEO_COLUMNS[:GEO_COLUMNS.index(PROCESS_UNTIL) + 1]

    # Chilean 2017 Census data can be found at:
    # https://www.ine.gob.cl/estadisticas/sociales/censos-de-poblacion-y-vivienda/censo-de-poblacion-y-vivienda
    
    # DATA_PATH_VIVIENDAS= 'data/csv-viviendas-censo-2017/microdato_censo2017-viviendas/Microdato_Censo2017-Viviendas.csv'
    # QUERIES_VIVIENDAS = ['P01', 'P02', 'P03A', 'P03B', 'P03C', 'P04', 'P05']
    DATA_PATH_PERSONAS = 'data/csv-personas-censo-2017/microdato_censo2017-personas/Microdato_Censo2017-Personas.csv'
    QUERIES_PERSONAS = ['P08', 'P09'] # Sex and Age


    OUTPUT_PATH = 'data/out/scability/'
    OUTPUT_FILE = 'viviendas_noisy_microdata_' + PROCESS_UNTIL + '_' + '_'.join(QUERIES_PERSONAS) + '.csv'


    # Privacy parameter to use for the whole algorithm.
    e_t = 10

    # We will consider and exponential allocation of the privacy budget across the levels of the tree.
    aux = 0
    for i in range(6):
        aux += (2**i)

    # Privacy parameters for the noise generation. First value for root, last for leaves.
    PRIVACY_PARAMETERS = [(e_t/aux)*(2**i) for i in range(6)]

    # Noise mechanism to use (discrete_laplace or discrete_gaussian).
    MECHANISM = 'discrete_laplace'

    # Edit Constraints
    # It uses a dictionary where keys are the geographic levels and values are lists of functions that recieve
    # the contingency vector and a value. Those functions will be used to set the constraints in the optimization problem.
    # TODO: Add a more complex set of constraints and implement an interface to define them.

    GEO_CONSTRAINTS = {
        'REGION': [lambda contingency_vector, total_population: contingency_vector.sum() == total_population],
        'PROVINCIA': [lambda contingency_vector, total_population: contingency_vector.sum() == total_population],
        'COMUNA': [lambda contingency_vector, total_population: contingency_vector.sum() == total_population],
        'DC': [],
        'ZC_LOC': []
    }

    ROOT_CONSTRAINTS = [lambda contingency_vector, total_population: contingency_vector.sum() == total_population]

    # Path of data that already has been processed
    # This is used to avoid reprocessing the data if it has already been processed by the algorithm.
    DATA_PATH_PROCESSED = None

    # Distance metric to use (manhattan, euclidean, cosine) if None no distance will be computed.
    # Only used for testing and analysis purposes.
    DISTANCE_METRIC = None

    time_start = time.time()
    
    topdown = TopDown()

    topdown.set_mechanism(MECHANISM)
    topdown.set_privacy_parameters(PRIVACY_PARAMETERS)

    topdown.set_geo_columns(GEO_COLUMNS_TO_USE)
    topdown.set_queries(QUERIES_PERSONAS)

    topdown.set_geo_constraints(GEO_CONSTRAINTS)
    topdown.set_root_constraints(ROOT_CONSTRAINTS)

    topdown.set_distance_metric(DISTANCE_METRIC)

    topdown.read_data(DATA_PATH_PERSONAS, sep=';')
    topdown.set_output_path(OUTPUT_PATH+OUTPUT_FILE)
    
    if DATA_PATH_PROCESSED: topdown.read_processed_data(DATA_PATH_PROCESSED, sep=';')

    # Run the TopDown algorithm
    topdown.run()
    time_end = time.time()
    print(f"TopDown algorithm finished in {time_end - time_start:.2f} seconds.\n")
    
    # This method can be used to check the correctness of the results.
    # topdown.check_correctness()

if __name__ == "__main__":
    main()