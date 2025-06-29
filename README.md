# ChileCensusDP

Este archivo describe la implementación del algoritmo TopDown para el Censo de Chile 2017, adaptado de la implementación utilizada en el Censo de Estados Unidos 2020. El sistema transforma microdatos de censo crudo en microdatos sintéticos protegidos por privacidad, preservando la utilidad estadística a través de técnicas sofisticadas de optimización y procesando datos jerárquicamente a través de las divisiones administrativas chilenas.
  
## Inicialización  
  
La inicialización del algoritmo TopDown se realiza a través del método `init_routine()` de la clase `TopDown`. [1](#0-0)  Este proceso incluye:  
  
- **Carga de datos**: Los datos del censo se cargan utilizando pandas con filtrado específico de columnas geográficas y demográficas  
- **Construcción del árbol geográfico**: Se crea la estructura jerárquica que representa las divisiones administrativas chilenas (Región → Provincia → Comuna → Distrito → Zona)  
- **Creación del nodo raíz**: Se establece el nodo raíz con su vector de contingencia que representa toda la distribución demográfica del dataset  
  
La entrada principal del sistema se gestiona a través del archivo `driver.py`, que orquesta la ejecución completa del algoritmo. 

## Configuración de Parámetros  
  
El sistema utiliza un enfoque de configuración centralizado a través del archivo `config.py`. Los parámetros principales incluyen:

- **Jerarquía geográfica**: GEO_COLUMNS y PROCESS_UNTIL definen los niveles administrativos a procesar
- **Parámetros de privacidad**: PRIVACY_PARAMETERS y MECHANISM configuran los presupuestos de privacidad y el mecanismo de ruido
- **Rutas de datos**: DATA_PATH, OUTPUT_PATH y OUTPUT_FILE especifican las ubicaciones de entrada y salida
- **Definición de consultas**: QUERIES determina las columnas demográficas a analizar

El sistema soporta dos mecanismos de privacidad diferencial: Gaussiano Discreto y Laplace Discreto, configurables mediante el parámetro MECHANISM.

## Preprocesamiento de Datos  
  
El preprocesamiento se ejecuta en varias etapas secuenciales:  
  
**Carga y filtrado de datos**: Los datos del censo se cargan selectivamente usando pandas con filtrado de columnas para optimizar el uso de memoria. [4](#0-3)   
  
**Generación de permutaciones**: El método `compute_permutation()` genera todas las combinaciones posibles de valores demográficos. [5](#0-4)  Esto crea una matriz de permutaciones que representa cada combinación de consulta posible para construir vectores de contingencia.  
  
**Construcción del árbol geográfico**: Se construye la estructura jerárquica usando la clase `GeographicTree`, que maneja la construcción de vectores de contingencia y la aplicación de ruido. [6](#0-5)   
  
## Fase de Medición  
  
La fase de medición aplica mecanismos de privacidad diferencial a los vectores de contingencia: [7](#0-6)   
  
**Selección del mecanismo**: El método `set_mechanism()` configura el mecanismo de privacidad basado en la configuración. [8](#0-7)   
  
**Aplicación de ruido**: El método `apply_noise()` recorre el árbol geográfico y aplica el mecanismo de ruido seleccionado con presupuestos de privacidad específicos por nivel. [9](#0-8)   
  
**Generación de ruido**: Se utilizan las implementaciones de ruido discreto `sample_dgauss()` y `sample_dlaplace()` del módulo `discretegauss.py` para generar ruido según el mecanismo seleccionado.  
  
## Fase de Estimación  
  
La fase de estimación utiliza optimización para estimar vectores de contingencia consistentes: [10](#0-9)   
  
**Estimación de la raíz**: Se inicia con la optimización del nodo raíz usando `root_estimation()`. [11](#0-10)   
  
**Estimación recursiva**: El método `recursive_estimation()` procesa los nodos nivel por nivel usando traversal basado en cola. [12](#0-11)   
  
**Optimización en dos fases**:   
1. Estimación real no negativa usando `non_negative_real_estimation()`  
2. Redondeo entero con preservación de restricciones usando `rounding_estimation()`  
  
Ambas fases utilizan el solver de optimización matemática Gurobi a través de la clase `OptimizationModel` para mantener consistencia padre-hijo en toda la jerarquía geográfica.  
  
## Generación de Microdatos  
  
La generación final de microdatos sintéticos se realiza a través del método `construct_microdata()`: [13](#0-12)   
  
**Construcción recursiva**: El método `recursive_construct_microdata()` recorre los nodos hoja y crea registros individuales. [14](#0-13)   
  
**Muestreo de individuos**: Para cada combinación de permutación, se replican valores demográficos según los conteos del vector de contingencia. [15](#0-14)   
  
**Salida de datos**: El resultado es un archivo CSV que contiene registros sintéticos que mantienen propiedades estadísticas mientras protegen la privacidad individual.  
  
## Funcionalidad de Reanudación  
  
El sistema incluye capacidad de reanudación para procesos interrumpidos a través de: [16](#0-15)   
  
- `load_state()`: Recupera el estado de procesamiento previo  
- `extend_tree()`: Añade nuevos niveles geográficos al árbol existente  
- `resume_measurement_phase()`: Aplica ruido a nuevos nodos  
- `resume_estimation_phase()`: Optimiza nuevos niveles geográficos  
  
El método `resume_run()` permite continuar el procesamiento desde donde se detuvo. [17](#0-16)   
  
## Validación de Calidad  
  
El sistema incluye validación de corrección para asegurar consistencia de datos:  
  
- `check_correctness()`: Verifica consistencia de suma padre-hijo [18](#0-17)   
- `check_correctness_node()`: Valida consistencia de nodos individuales [19](#0-18)   
- Métricas de distancia: Miden el equilibrio privacidad-utilidad [20](#0-19)   
  
