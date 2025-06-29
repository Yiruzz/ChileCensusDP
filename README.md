# ChileCensusDP

Este archivo describe la implementación del algoritmo TopDown para el Censo de Chile 2017, adaptado de la implementación utilizada en el Censo de Estados Unidos 2020. El sistema transforma microdatos de censo crudo en microdatos sintéticos protegidos por privacidad, preservando la utilidad estadística a través de técnicas sofisticadas de optimización y procesando datos jerárquicamente a través de las divisiones administrativas chilenas.
  
## Inicialización  
  
La inicialización del algoritmo TopDown se realiza a través del método [`init_routine()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L59) de la clase [`TopDown`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L14).  Este proceso incluye:  
  
- **Carga de datos**: Los datos del censo se cargan utilizando pandas con filtrado específico de columnas geográficas y demográficas  
- **Construcción del árbol geográfico**: Se crea la estructura jerárquica que representa las divisiones administrativas chilenas (Región → Provincia → Comuna → Distrito → Zona)  
- **Creación del nodo raíz**: Se establece el nodo raíz con su vector de contingencia que representa toda la distribución demográfica del dataset  
  
La entrada principal del sistema se gestiona a través del archivo [`driver.py`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/driver.py#L7), que orquesta la ejecución completa del algoritmo. 

## Configuración de Parámetros  
  
El sistema utiliza un enfoque de configuración centralizado a través del archivo [`config.py`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/config.py#L1). Los parámetros principales incluyen:

- **Jerarquía geográfica**: GEO_COLUMNS y PROCESS_UNTIL definen los niveles administrativos a procesar
- **Parámetros de privacidad**: PRIVACY_PARAMETERS y MECHANISM configuran los presupuestos de privacidad y el mecanismo de ruido
- **Rutas de datos**: DATA_PATH, OUTPUT_PATH y OUTPUT_FILE especifican las ubicaciones de entrada y salida
- **Definición de consultas**: QUERIES determina las columnas demográficas a analizar

El sistema soporta dos mecanismos de privacidad diferencial: Gaussiano Discreto y Laplace Discreto, configurables mediante el parámetro MECHANISM.

## Preprocesamiento de Datos  
  
El preprocesamiento se ejecuta en varias etapas secuenciales:  
  
**Carga y filtrado de datos**: Los datos del censo se [`cargan`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L59) selectivamente usando pandas con filtrado de columnas para optimizar el uso de memoria.    
  
**Generación de permutaciones**: El método [`compute_permutation()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L41) genera todas las combinaciones posibles de valores demográficos.  Esto crea una matriz de permutaciones que representa cada combinación de consulta posible para construir vectores de contingencia.  
  
**Construcción del árbol geográfico**: Se construye la estructura jerárquica usando la clase [`GeographicTree`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/geographic_tree.py#L8), que maneja la construcción de vectores de contingencia y la aplicación de ruido.
  
## Fase de Medición  
  
La [`fase de medición`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L106) aplica mecanismos de privacidad diferencial a los vectores de contingencia:
  
**Selección del mecanismo**: El método [`set_mechanism()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L249) configura el mecanismo de privacidad basado en la configuración. 
  
**Aplicación de ruido**: El método [`apply_noise()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L260) recorre el árbol geográfico y aplica el mecanismo de ruido seleccionado con presupuestos de privacidad específicos por nivel.
  
**Generación de ruido**: Se utilizan las implementaciones de ruido discreto [`sample_dgauss()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/discretegauss.py#L125) y [`sample_dlaplace()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/discretegauss.py#L88) del módulo `discretegauss.py` para generar ruido según el mecanismo seleccionado.  
  
## Fase de Estimación  
  
La [`fase de estimación`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L106) utiliza optimización para estimar vectores de contingencia consistentes:
  
**Estimación de la raíz**: Se inicia con la optimización del nodo raíz usando [`root_estimation()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L129).
  
**Estimación recursiva**: El método [`recursive_estimation()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L135) procesa los nodos nivel por nivel usando traversal basado en cola. 
  
**Optimización en dos fases**:   
1. Estimación real no negativa usando [`non_negative_real_estimation()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/optimizer.py#L12)  
2. Redondeo entero con preservación de restricciones usando [`rounding_estimation()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/optimizer.py#L49)  
  
Ambas fases utilizan el solver de optimización matemática Gurobi a través de la clase [`OptimizationModel`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/optimizer.py#L6) para mantener consistencia padre-hijo en toda la jerarquía geográfica.  
  
## Generación de Microdatos  
  
La generación final de microdatos sintéticos se realiza a través del método [`construct_microdata()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L188):  
  
**Construcción recursiva**: El método [`recursive_construct_microdata()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L211) recorre los nodos hoja y crea registros individuales.
  
**Muestreo de individuos**: Para cada combinación de permutación, se [`replican`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L229) valores demográficos según los conteos del vector de contingencia.
  
**Salida de datos**: El [`resultado`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L205) es un archivo CSV que contiene registros sintéticos que mantienen propiedades estadísticas mientras protegen la privacidad individual.  
  
## Funcionalidad de Reanudación  
  
El sistema incluye capacidad de reanudación para procesos interrumpidos a través de:
  
- [`load_state()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L359): Recupera el estado de procesamiento previo  
- [`extend_tree()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L367): Añade nuevos niveles geográficos al árbol existente  
- [`resume_measurement_phase()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L379): Aplica ruido a nuevos nodos  
- [`resume_estimation_phase()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L396): Optimiza nuevos niveles geográficos  
  
El método [`resume_run()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L409) permite continuar el procesamiento desde donde se detuvo.
  
## Validación de Calidad  
  
El sistema incluye validación de corrección para asegurar consistencia de datos:  
  
- [`check_correctness()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L270): Verifica consistencia de suma padre-hijo 
- [`check_correctness_node()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L281): Valida consistencia de nodos individuales
- [`Métricas de distancia`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/utils.py#L3): Miden el equilibrio privacidad-utilidad 
  
