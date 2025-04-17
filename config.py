# COLUMNS_TO_KEEP = ['REGION', 'PROVINCIA', 'COMUNA', 'DC', 'AREA', 'ZC_LOC', 'ID_ZONA_LOC', 'P08', 'P09']
GEO_COLUMNS = ['REGION', 'PROVINCIA', 'COMUNA', 'DC', 'ZC_LOC'] # Region, Provincia, Comuna, Distrito Censal, Zona/Localidad
DATA_PATH = 'data/csv-personas-censo-2017/microdato_censo2017-personas/Microdato_Censo2017-Personas.csv'
PRIVACY_PARAMETERS = [.1, .2, .4, .8, 1.6, 3.2]
QUERIES = ['P08', 'P09'] # Sex and Age
MECHANISM = 'discrete_laplace' # Mechanism to use for noise generation (discrete_gaussian or discrete_laplace)

# Edit Constraints
GEO_CONSTRAINTS = {
    'REGION': [lambda x, y: x.sum() == y], # Region
    'PROVINCIA': [lambda x, y: x.sum() == y], # Provincia
    'COMUNA': [], # Comuna
    'DC': [], # Distrito Censal
    'ZC_LOC': [] # Zona/Localidad
}
