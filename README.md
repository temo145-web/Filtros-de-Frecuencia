# Filtros digitales sobre una señal compuesta

Este proyecto crea una señal con tonos de 8, 40 y 160 Hz, añade ruido blanco y un zumbido de 50 Hz, y compara filtros pasa bajos, pasa altos y pasa bandas en tiempo y frecuencia.

## Preparación

Requiere Python 3.10 o posterior. Dentro de esta carpeta, instala dependencias y ejecuta:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python ejecutar_analisis.py
```

## Verificación del proyecto

El proyecto fue desarrollado en Python para analizar
filtros digitales pasa bajos, pasa altos y pasa bandas.

Se utilizó Git para el control de versiones y GitHub
para publicar el código y los resultados.

El programa crea las gráficas PNG en `figuras/` y los indicadores CSV/JSON en `resultados/`. El generador aleatorio usa semilla 731 para reproducir la señal de prueba.

## Filtros del experimento

- Pasa bajos Butterworth IIR, orden 4, corte de 22 Hz. Busca conservar 8 Hz.
- Pasa altos Chebyshev II IIR, orden 6 y atenuación de rechazo de 42 dB, con corte de 90 Hz. Busca conservar 160 Hz.
- Pasa bandas FIR de 181 coeficientes, ventana Blackman y cortes de 33 y 47 Hz. Busca conservar 40 Hz.

Se aplica `sosfiltfilt` a los IIR y `filtfilt` al FIR. El filtrado de ida y vuelta conserva la alineación temporal sin desfase neto, pero requiere procesar el registro completo; por tanto, el ejemplo es para análisis fuera de línea y no para una transmisión en tiempo real. La magnitud efectiva de la respuesta es el cuadrado de la respuesta del filtro de una pasada.

## Subir el proyecto a GitHub

1. Crea un repositorio vacío en GitHub.
2. Descomprime el ZIP y abre una terminal dentro de `filtros_frecuencia`.
3. Cambia la URL de ejemplo por la dirección de tu repositorio y ejecuta:

```bash
git init
git add .
git commit -m "Analizar filtros digitales en Python"
git branch -M main
git remote add origin https://github.com/USUARIO/REPOSITORIO.git
git push -u origin main
```
Proyecto académico de Señales y Sistemas: diseño y análisis de filtros digitales.
