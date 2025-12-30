# Development Decisions

* En lugar de usar GitFlow, he decidido seguir un enfoque Trunk-based, comúnmente el estándar para desarrollo ágil.
* Integré un pipeline de pre-commit hooks para estandarizar algunas prácticas de desarrollo antes de que el código llegué al repositorio, las cuales se duplican en el pipeline del CI para evitar que los desarrolladores omitan estas reglas.
* todo el preprocesamiento de los datos se realiza en una nueva clase (DataProcessor), esto hace el código más modular, lo que nos permite aislar posibles errores sin afectar el sistema en general (mantenible y escalable).
* Utilicé el manejador de paquetes uv para facilitar la resolución de conflictos entre dependencias del proyecto.
* La lógica en la función `get_period_day`se puede simplificar, además, es una mejor práctica no utilizar elif después de un retorno.
* He dejado documentado que la función `get_min_diff`podría devolver valores negativos, esto considerando llegadas anticipadas.
* La api de inferencia descarga el modelo desde GCS, utiliza variables de entorno que se pasan en tiempo de ejecución para evitar exponer secrets, o agregarlos a los layers de la imagen de docker.
* Algunos docstrings fueron generados utilizando un LLM.
* aunque parezca innecesario, se ha creado una rama por cada cambio, en este projecto los cambios son mínimos, sin embargo, decidí hacerlo así para demostrar el flujo trunk-based.
* No soy un experto en GCP, sin embargo, aproveché este proyecto para familiarizarme un poco más con los servicios de GCP. Se están utilizando los siguientes servicios:
    * Cloud storage: Para alojar los datos del CI (se evita subir datos al repositorio) y los modelos.
    * Artifact Registry: Para alojar las imágenes generadas durante el despliegue.
    * Cloud Run: Para servir el modelo como una Restfull API.
* En GCP se crearon dos buckets, uno exclusivo para datos del CI (no se mezclan con los datos de procucción, para producción se debería crear un bucket adicional), y uno como registro de los modelos. Los modelos se sirven como artefactos de joblib (librería recomendada por sklearn).
* Decidí utilizar Cloud Run, con el servicio bajo demanda, con el billing basado en request y con cero instancias posibles en periodos sin carga, para optimizar los costos. Dado que la carga del modelo es relativamente rápida, no se consideraron los cold-starts.
* Existen dos service-accounts distintos, uno para CI y otro para despligue, ambos creados bajo el principio de privilegios mínimos.
* todo el deployment se ejecuta al crear un nuevo tag, de esta manera se asegura que los despliegues sean sin cambios en el código.
* Hace falta agregar algunas características al CD, como versionado automático y posiblemente blue-green deployment o rollback.
* De igual manera, hace falta considerar el reentrenamiento del modelo y un servicio de monitoreo.
* tanto el CI, como el CD, utilizan secrets, ninguna key u algun dato sensible se expone públicamente.

# Contribution
1. Primero clone el repositorio, asegúrese de haber configurado una llave ssh.
```bash
git clone git@github.com:Mysdafb/flight-delay-prediction.git
cd flight-delay-prediction
```
Este proyecto utiliza uv para la administración de dependencias y pre-commit hooks para forzar la verificación de nuestros estándares de calidad. Si no tiene instalado uv, por favor, siga los pasos descritos en la documentación oficial [aquí](https://docs.astral.sh/uv/getting-started/installation/).

2. Instale las dependencias necesarias para comenzar a desarrollar:
```bash
uv sync --group dev --group test
```
3. Instala los hooks de pre-commit:
```bash
uv run pre-commit install
```
Con esto, los hooks se ejecutarán de forma automática antes de cada commit, verificando que los cambios cumplan con los estándares de calidad definidos para este proyecto.

# Model selection
Basado en los hallazgos del DS, deberíamos desplegar el modelo entrenado con las 10 principales características, lo cual reduce la complejidad del modelo y su costo computacional sin sacrificar el desempeño, y en el cual se aplicó la técnica de balanceo de datos, lo cual mostró un incremento en la sensibilidad del modelo.
Ahora bien, considerando que no se encontró una clara diferencia entre el desempeño de ambos modelos, y utilizando el principio de parsimonía (Occam's razor), se ha seleccionado la regresión logística. Esta decisión es importante cuando los recursos computaciones que se tiene son limitados.



