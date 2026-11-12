from io import BytesIO

import matplotlib

# Dibuja sin abrir ventanas: los gráficos solo se guardan como imagen dentro del archivo exportado.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


def dibujar_grafico(grafico):
    """Dibuja un gráfico de barras y lo devuelve como imagen PNG en memoria. Lo usan los tres formatos."""
    figura, ejes = plt.subplots(figsize=(8, 4))
    ejes.bar(grafico.etiquetas, grafico.valores, color="#1F4E79")
    ejes.set_title(grafico.titulo)
    ejes.set_ylabel(grafico.unidad)
    ejes.tick_params(axis="x", labelrotation=15)
    if all(isinstance(valor, int) for valor in grafico.valores):
        # Una cantidad no puede tener decimales en el eje.
        ejes.yaxis.set_major_locator(MaxNLocator(integer=True))
    figura.tight_layout()
    imagen = BytesIO()
    figura.savefig(imagen, format="png", dpi=150)
    plt.close(figura)
    imagen.seek(0)
    return imagen
