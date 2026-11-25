
from pathlib import Path
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "static" / "icons"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NAVY = "#17324D"
TEAL = "#0D9488"
WHITE = "#FFFFFF"

# Dibujar en alta resolución.
SCALE = 4
SIZE = 192 * SCALE

image = Image.new("RGBA", (SIZE, SIZE), NAVY)
draw = ImageDraw.Draw(image)


def coords(values):
    return tuple(value * SCALE for value in values)


# Cuerpo de la cámara.
draw.rounded_rectangle(
    coords((35, 64, 157, 146)),
    radius=14 * SCALE,
    outline=WHITE,
    width=8 * SCALE,
)

# Parte superior de la cámara.
draw.line(
    [
        coords((65, 64)),
        coords((76, 46)),
        coords((116, 46)),
        coords((127, 64)),
    ],
    fill=WHITE,
    width=8 * SCALE,
    joint="curve",
)

# Lente.
draw.ellipse(
    coords((70, 78, 122, 130)),
    outline=WHITE,
    width=8 * SCALE,
)

# Círculo de verificación.
draw.ellipse(
    coords((118, 113, 176, 171)),
    fill=TEAL,
    outline=NAVY,
    width=5 * SCALE,
)

# Marca de verificación.
draw.line(
    [
        coords((133, 142)),
        coords((143, 152)),
        coords((162, 132)),
    ],
    fill=WHITE,
    width=7 * SCALE,
    joint="curve",
)

# Exportar ambas resoluciones.
for size in (192, 512):
    icon = image.resize(
        (size, size),
        Image.Resampling.LANCZOS,
    )

    output = OUTPUT_DIR / f"icon-{size}.png"

    icon.convert("RGB").save(output)

    print(f"Icono generado: {output.name}")
