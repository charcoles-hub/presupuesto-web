#!/usr/bin/env python3
"""Comprueba que la calculadora pública cobra lo mismo que el tarifario interno.

Uso:  python3 check_precios.py
Sale con codigo 1 si algo no cuadra, para poder encadenarlo en un commit.
"""
import re
import sys
from pathlib import Path

TARIFARIO = Path.home() / "Documentos" / "tarifario.html"
PUBLICA = Path(__file__).parent / "index.html"

# Mismo concepto, distinto nombre: interno -> publico
EQUIVALE = {
    "Reservas y cita online": "Cita online",
    "SEO local y ficha de Google": "SEO local",
    "Textos escritos por mí": "Textos escritos por Sergio",
    "Analítica de visitas": "Analítica",
    "Instagram integrado": "Instagram integrado",
    "Blog": "Blog",
    "Galería de trabajos": "Galería de trabajos",
    "Páginas adicionales (pack de 3)": "Páginas adicionales",
    "Segundo idioma": "Segundo idioma",
    "Formulario avanzado": "Formulario avanzado",
    "Correo profesional": "Correo profesional",
    "Textos legales y cookies": "Textos legales y cookies",
    "Traslado desde su web actual": "Traslado desde su web actual",
}


def precios_internos(src):
    filas = dict()
    for precio, dias, nombre in re.findall(
        r'data-precio="(\d+)" data-dias="(\d+)" data-nombre="([^"]+)"', src
    ):
        filas[nombre] = (int(precio), int(dias))
    base = int(re.search(r"const BASE_PRECIO = (\d+)", src).group(1))
    mant = sorted(int(v) for v in re.findall(r'name="mant" value="(\d+)"', src))
    return base, filas, mant


def precios_publicos(src):
    filas = dict()
    for valor, precio, dias in re.findall(
        r'value="([^"]+?) \(\d+ €\)" data-precio="(\d+)" data-dias="(\d+)"', src
    ):
        filas[valor] = (int(precio), int(dias))
    base = int(re.search(r"const BASE = (\d+)", src).group(1))
    mant = sorted(int(v) for v in re.findall(r'data-mes="(\d+)"', src))
    return base, filas, mant


def main():
    for f in (TARIFARIO, PUBLICA):
        if not f.exists():
            print(f"FALTA {f}")
            return 1

    base_i, filas_i, mant_i = precios_internos(TARIFARIO.read_text(encoding="utf-8"))
    base_p, filas_p, mant_p = precios_publicos(PUBLICA.read_text(encoding="utf-8"))

    fallos = []
    if base_i != base_p:
        fallos.append(f"base: tarifario {base_i} € vs pública {base_p} €")
    if mant_i != mant_p:
        fallos.append(f"mantenimiento: tarifario {mant_i} vs pública {mant_p}")

    for interno, (precio, dias) in filas_i.items():
        publico = EQUIVALE.get(interno)
        if publico is None:
            fallos.append(f"'{interno}' no está mapeado: revisa EQUIVALE")
            continue
        if publico not in filas_p:
            fallos.append(f"'{interno}' está en el tarifario pero no en la pública")
            continue
        if filas_p[publico] != (precio, dias):
            fallos.append(
                f"'{interno}': tarifario {precio} €/{dias}d vs "
                f"pública {filas_p[publico][0]} €/{filas_p[publico][1]}d"
            )

    sobran = set(filas_p) - set(EQUIVALE.values())
    for s in sobran:
        fallos.append(f"'{s}' está en la pública pero no en el tarifario")

    # El precio escrito en pantalla tiene que ser el que suma
    for src, quien in ((PUBLICA.read_text(encoding="utf-8"), "pública"),):
        for bloque in re.findall(r'<label class="row">(.*?)</label>', src, re.S):
            dp = re.search(r'data-precio="(\d+)"', bloque)
            txt = re.search(r'<span class="price">(\d+) €', bloque)
            if dp and txt and dp.group(1) != txt.group(1):
                fallos.append(f"{quien}: escrito {txt.group(1)} € pero suma {dp.group(1)} €")

    if fallos:
        print("NO CUADRA:")
        for f in fallos:
            print("  -", f)
        return 1

    print(f"OK · base {base_i} € · {len(filas_i)} complementos · mantenimiento {mant_i} €/mes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
