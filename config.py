GEO_COLUMNS = ['REGION', 'PROVINCIA', 'COMUNA', 'DC', 'ZC_LOC'] # Region, Provincia, Comuna, Distrito Censal, Zona/Localidad
QUERIES = ['P08', 'P09'] # Sex and Age
DATA_PATH = 'data/csv-personas-censo-2017/microdato_censo2017-personas/Microdato_Censo2017-Personas.csv'
OUTPUT_PATH = 'data/out/' # Path to save the output files
OUTPUT_FILE = 'personas_noisy_microdata.csv' # Name of the output file

PRIVACY_PARAMETERS = [.1, .2, .4, .8, 1.6, 3.2]
MECHANISM = 'discrete_laplace' # Mechanism to use for noise generation (discrete_gaussian or discrete_laplace)

# Edit Constraints
GEO_CONSTRAINTS = {
    'REGION': [lambda x, y: x.sum() == y], # Region
    'PROVINCIA': [lambda x, y: x.sum() == y], # Provincia
    'COMUNA': [], # Comuna
    'DC': [], # Distrito Censal
    'ZC_LOC': [] # Zona/Localidad
}
