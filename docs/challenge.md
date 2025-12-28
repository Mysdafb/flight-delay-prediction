# Development Decisions

* En lugar de usar GitFlow, he decidido seguir un enfoque Trunk-based, comúnmente el estándar para desarrollo ágil.
* Integré un pipeline de pre-commit hooks para estandarizar algunas prácticas de desarrollo antes de que el código llegué al repositorio, las cuales se duplican en el pipeline del CI para evitar que los desarrolladores omitan estas reglas.
* Utilicé el manejador de paquetes uv para facilitar la resolución de conflictos entre dependencias del proyecto.

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



