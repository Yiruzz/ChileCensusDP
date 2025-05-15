# Geographic columns used to build the geographic tree (from highest to lowest granularity)
GEO_COLUMNS = ['REGION', 'PROVINCIA', 'COMUNA', 'DC', 'ZC_LOC'] # Region, Provincia, Comuna, Distrito Censal, Zona/Localidad
PROCESS_UNTIL = 'COMUNA'
GEO_COLUMNS_TO_USE = GEO_COLUMNS[:GEO_COLUMNS.index(PROCESS_UNTIL) + 1]

# Queries to be answered (column names in the census data)
QUERIES = ['P08', 'P09'] # Sex and Age

# Path to the raw original census data file (CSV)
DATA_PATH = 'data/csv-personas-censo-2017/microdato_censo2017-personas/Microdato_Censo2017-Personas.csv'

OUTPUT_PATH = 'data/out/'
OUTPUT_FILE = 'personas_noisy_microdata_COMUNA_P08P09.csv'

# Privacy parameters for the noise generation. First value for root, last for leaves.
PRIVACY_PARAMETERS = [.1, .2, .4, .8, 1.6, 3.2]

 # Mechanism to use for noise generation (discrete_gaussian or discrete_laplace)
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
DATA_PATH_PROCESSED = None

# Distance metric to use (manhattan, euclidean, cosine) if None no distance will be computed.
# Only used for testing and analysis purposes.
DISTANCE_METRIC = None