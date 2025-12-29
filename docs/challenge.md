# Development Decisions

* En lugar de usar GitFlow, he decidido seguir un enfoque Trunk-based, comúnmente el estándar para desarrollo ágil.
* Integré un pipeline de pre-commit hooks para estandarizar algunas prácticas de desarrollo antes de que el código llegué al repositorio, las cuales se duplican en el pipeline del CI para evitar que los desarrolladores omitan estas reglas.
* Utilicé el manejador de paquetes uv para facilitar la resolución de conflictos entre dependencias del proyecto.
* La lógica en la función `get_period_day`se puede simplificar, además, es una mejor práctica no utilizar elif después de un retorno.
* He dejado documentado que la función `get_min_diff`podría devolver valores negativos, esto considerando llegadas anticipadas.
* Algunos docstrings fueron generados utilizando un LLM.

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



