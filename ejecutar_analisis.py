"""Compara tres filtros digitales sobre una señal con tonos, zumbido y ruido."""
from pathlib import Path
import csv
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

ROOT = Path(__file__).resolve().parent
FIGURES = ROOT / "figuras"
RESULTS = ROOT / "resultados"
FIGURES.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)

# Frecuencia de muestreo y tiempo del registro de prueba.
FS = 1200.0
DURATION = 3.0
count = int(FS * DURATION)
time = np.arange(count) / FS
rng = np.random.default_rng(731)

# Señal útil compuesta por tres tonos de distintas bandas.
# A sus componentes se agregan ruido blanco y zumbido de 50 Hz.
components = {8.0: 0.90, 40.0: 0.65, 160.0: 0.45}
useful = sum(amplitude * np.sin(2 * np.pi * hz * time)
             for hz, amplitude in components.items())
noise = 0.28 * rng.standard_normal(count)
mains_hum = 0.32 * np.sin(2 * np.pi * 50 * time + 0.4)
measured = useful + noise + mains_hum

# El pasa bajos conserva 8 Hz y reduce contenido por encima de 22 Hz.
low_sos = signal.butter(4, 22, btype="lowpass", fs=FS, output="sos")
# El pasa altos usa Chebyshev II, con atenuación mínima de 42 dB en rechazo.
high_sos = signal.cheby2(6, 42, 90, btype="highpass", fs=FS, output="sos")
# FIR con ventana Blackman, centrado en 40 Hz.
band_taps = signal.firwin(181, [33, 47], pass_zero=False,
                          window="blackman", fs=FS)

# Filtrado en ambas direcciones: análisis fuera de línea sin desfase neto.
outputs = {
    "Pasa bajos Butterworth": signal.sosfiltfilt(low_sos, measured),
    "Pasa altos Chebyshev II": signal.sosfiltfilt(high_sos, measured),
    "Pasa bandas FIR Blackman": signal.filtfilt(band_taps, [1.0], measured),
}

# Ajuste seno-coseno para medir la amplitud de cada frecuencia conocida.
def estimate_amplitude(values: np.ndarray, hz: float) -> float:
    basis = np.column_stack((np.sin(2*np.pi*hz*time),
                             np.cos(2*np.pi*hz*time),
                             np.ones_like(time)))
    coeff, *_ = np.linalg.lstsq(basis, values, rcond=None)
    return float(np.hypot(coeff[0], coeff[1]))

probe_frequencies = [8.0, 40.0, 50.0, 160.0]
input_amplitudes = {hz: estimate_amplitude(measured, hz) for hz in probe_frequencies}
records = []
for label, result in outputs.items():
    for hz in probe_frequencies:
        output_amplitude = estimate_amplitude(result, hz)
        difference_db = 20 * np.log10(max(output_amplitude, 1e-12) /
                                      max(input_amplitudes[hz], 1e-12))
        records.append({"filtro": label, "frecuencia_hz": hz,
                        "amplitud_entrada": input_amplitudes[hz],
                        "amplitud_salida": output_amplitude,
                        "cambio_db": float(difference_db)})

with (RESULTS / "comparacion_amplitudes.csv").open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)

rms = {"entrada": float(np.sqrt(np.mean(measured**2)))}
rms.update({name: float(np.sqrt(np.mean(result**2))) for name, result in outputs.items()})
(RESULTS / "resumen_rms.json").write_text(json.dumps({
    "frecuencia_muestreo_hz": FS,
    "duracion_segundos": DURATION,
    "componentes_utiles_hz": list(components),
    "interferencia_hz": 50.0,
    "rms": rms,
}, ensure_ascii=False, indent=2), encoding="utf-8")

# Ajustes gráficos de la bitácora.
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.22})
colors = {"entrada": "#667085", "low": "#16805d",
          "high": "#bc4b16", "band": "#5752a2"}

# Gráfica 1: medición original y señal útil de referencia.
short = time <= 0.35
fig, ax = plt.subplots(figsize=(9.5, 4.2))
ax.plot(time[short], measured[short], color=colors["entrada"], lw=.9,
        label="Entrada con ruido e interferencia")
ax.plot(time[short], useful[short], color="#18212f", lw=1.4,
        label="Componentes útiles")
ax.set(title="Registro antes del filtrado", xlabel="Tiempo (s)", ylabel="Amplitud")
ax.legend(frameon=False, ncol=2)
fig.tight_layout(); fig.savefig(FIGURES / "senal_inicial.png", dpi=180); plt.close(fig)

# Gráfica 2: las respuestas se muestran como magnitud efectiva de ida y vuelta.
filter_specs = [
    ("Pasa bajos Butterworth", "sos", low_sos, colors["low"]),
    ("Pasa altos Chebyshev II", "sos", high_sos, colors["high"]),
    ("Pasa bandas FIR Blackman", "fir", band_taps, colors["band"]),
]
fig, axes = plt.subplots(3, 1, figsize=(9.5, 7.2), sharex=True)
for ax, (label, kind, coeff, color) in zip(axes, filter_specs):
    if kind == "sos":
        freq, response = signal.sosfreqz(coeff, worN=4096, fs=FS)
    else:
        freq, response = signal.freqz(coeff, worN=4096, fs=FS)
    # filtfilt aplica H dos veces: la ganancia efectiva es |H| al cuadrado.
    magnitude_db = 40 * np.log10(np.maximum(np.abs(response), 1e-8))
    ax.plot(freq, magnitude_db, color=color, lw=1.7)
    ax.set_ylim(-100, 5); ax.set_ylabel("Ganancia (dB)")
    ax.set_title(label, loc="left", fontsize=10)
    for hz in [8, 40, 50, 160]: ax.axvline(hz, color="#98a2b3", ls=":", lw=.65)
axes[-1].set_xlim(0, 240); axes[-1].set_xlabel("Frecuencia (Hz)")
fig.suptitle("Respuesta en frecuencia de cada diseño", fontsize=14, y=1.01)
fig.tight_layout(); fig.savefig(FIGURES / "respuesta_filtros.png", dpi=180, bbox_inches="tight"); plt.close(fig)

# Gráfica 3: vista temporal de la entrada y de cada señal filtrada.
fig, axes = plt.subplots(4, 1, figsize=(9.5, 8.5), sharex=True)
series = [("Entrada", measured, colors["entrada"])] + [
    (name, result, color) for (name, result), color in zip(outputs.items(),
        [colors["low"], colors["high"], colors["band"]])]
for ax, (label, values, color) in zip(axes, series):
    ax.plot(time[short], values[short], color=color, lw=1.0)
    ax.set_title(label, loc="left", fontsize=9); ax.set_ylabel("Amplitud")
axes[-1].set_xlabel("Tiempo (s)")
fig.suptitle("Comparación temporal de la entrada y las salidas", fontsize=14, y=1.01)
fig.tight_layout(); fig.savefig(FIGURES / "comparacion_tiempo.png", dpi=180, bbox_inches="tight"); plt.close(fig)

# Gráfica 4: densidad espectral de potencia calculada con Welch.
fig, axes = plt.subplots(4, 1, figsize=(9.5, 8.5), sharex=True)
for ax, (label, values, color) in zip(axes, series):
    freq, psd = signal.welch(values, fs=FS, nperseg=2048)
    ax.plot(freq, 10*np.log10(np.maximum(psd, 1e-14)), color=color, lw=1.05)
    ax.set_title(label, loc="left", fontsize=9); ax.set_ylabel("PSD (dB/Hz)")
    for hz in [8, 40, 50, 160]: ax.axvline(hz, color="#98a2b3", ls=":", lw=.65)
axes[-1].set_xlim(0, 240); axes[-1].set_xlabel("Frecuencia (Hz)")
fig.suptitle("Densidad espectral antes y después del filtrado", fontsize=14, y=1.01)
fig.tight_layout(); fig.savefig(FIGURES / "espectros.png", dpi=180, bbox_inches="tight"); plt.close(fig)

print("Análisis terminado; revisa las carpetas figuras/ y resultados/.")
print(f"RMS de la entrada: {rms['entrada']:.3f}")
for item in records:
    print(f"{item['filtro']} · {item['frecuencia_hz']:.0f} Hz: {item['cambio_db']:.1f} dB")
