import os
import glob
import json
import ollama
from datetime import datetime
from shutil import move
from PIL import Image, ImageDraw, ImageFont, ImageOps
import re

# --- Configuración de Directorios ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_ENTRADA = os.path.join(BASE_DIR, "imagenes_brutas")
DIR_SALIDA = os.path.join(BASE_DIR, "publicaciones")
DIR_PROCESADAS = os.path.join(BASE_DIR, "procesadas")
PLANTILLA_PATH = os.path.join(BASE_DIR, "plantilla", "marco_base.png")
FUENTE_PATH = "C:/Windows/Fonts/arialbd.ttf" # Tipografía negrita de Windows

# Crear carpetas si no existen
for d in [DIR_ENTRADA, DIR_SALIDA, DIR_PROCESADAS]:
    os.makedirs(d, exist_ok=True)

# --- 1. Módulo LLM Multimodal Gratuito (Ollama + LLaVA) ---

import re

def analizar_foto_con_llm(ruta_imagen):
    print(f"🤖 Analizando imagen: {os.path.basename(ruta_imagen)}...")
    
    prompt = (
        "Analiza esta imagen de un inmueble en Perú. "
        "Devuelve SOLO un objeto JSON válido sin texto adicional, sin explicaciones y sin bloques markdown ```json. "
        '{"titulo": "TASACIÓN DE DEPARTAMENTO", "ubicacion": "MIRAFLORES, LIMA"}. '
        "Opciones para 'titulo': 'TASACIÓN DE TERRENO', 'TASACIÓN LOCALES COMERCIALES', "
        "'TASACIÓN DE EDIFICIO', 'TASACIÓN DE DEPARTAMENTO', 'TASACIÓN DE CASAS'."
    )

    try:
        response = ollama.chat(
            model='llava',
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [ruta_imagen]
            }]
        )
        
        raw_text = response['message']['content'].strip()
        
        # Buscar la estructura de JSON usando expresiones regulares
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            raise ValueError("No se encontró JSON en la respuesta")
            
    except Exception as e:
        print(f"⚠️ Aviso del LLM: {e}. Se utilizarán textos genéricos.")
        return {"titulo": "TASACIÓN DE INMUEBLE", "ubicacion": "LIMA, PERÚ"}

# --- 2. Módulo de Renderizado Gráfico (Pillow) ---

def generar_diseno_publicitario(ruta_foto, datos_llm):
    # 1. Cargar el marco/plantilla base
    if os.path.exists(PLANTILLA_PATH):
        lienzo = Image.open(PLANTILLA_PATH).convert("RGBA")
    else:
        lienzo = Image.new("RGBA", (1080, 1080), (255, 255, 255, 255))

    # 2. Cargar y ajustar la foto de la propiedad al centro (área visible)
    foto = Image.open(ruta_foto).convert("RGBA")
    # Redimensionar la foto para encajar en el recuadro superior/central
    ancho_foto, alto_foto = 1080, 580
    foto_fit = ImageOps.fit(foto, (ancho_foto, alto_foto), Image.Resampling.LANCZOS)

    # Crear una imagen combinada donde la foto quede de fondo o en el hueco
    fondo = Image.new("RGBA", (1080, 1080), (255, 255, 255, 255))
    fondo.paste(foto_fit, (0, 150)) # Coloca la foto en el área superior

    # Superponer la plantilla encima usando su capa Alpha (transparencia)
    if os.path.exists(PLANTILLA_PATH):
        fondo.alpha_composite(lienzo)
    else:
        fondo = lienzo

    # Convertir a RGB para dibujar texto y guardar
    resultado = fondo.convert("RGB")
    draw = ImageDraw.Draw(resultado)
    COLOR_VERDE_CORPORATIVO = "#004B49"

    try:
        font_titulo = ImageFont.truetype(FUENTE_PATH, 42)
        font_ubicacion = ImageFont.truetype(FUENTE_PATH, 32)
    except IOError:
        font_titulo = font_ubicacion = ImageFont.load_default()

    # Escribir Título
    draw.text((60, 180), datos_llm["titulo"].upper(), font=font_titulo, fill=COLOR_VERDE_CORPORATIVO)

    # Escribir Ubicación
    draw.text((60, 240), datos_llm["ubicacion"].upper(), font=font_ubicacion, fill=COLOR_VERDE_CORPORATIVO)

    return resultado

# --- 3. Ejecución del Agente ---

def ejecutar_agente():
    patrones = [os.path.join(DIR_ENTRADA, "*.jpg"), os.path.join(DIR_ENTRADA, "*.png")]
    fotos = [f for p in patrones for f in glob.glob(p)]

    if not fotos:
        print("📁 Coloca las imágenes en la carpeta 'imagenes_brutas' para iniciar.")
        return

    for foto in fotos:
        nombre_archivo = os.path.basename(foto)
        
        # Analizar
        datos = analizar_foto_con_llm(foto)
        
        # Generar imagen
        imagen_final = generar_diseno_publicitario(foto, datos)
        
        # Guardar en 'publicaciones'
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_salida = os.path.join(DIR_SALIDA, f"post_{timestamp}_{nombre_archivo}")
        imagen_final.save(ruta_salida, "PNG")
        
        print(f"✅ Diseño generado exitosamente: {ruta_salida}")

        # Mover original a 'procesadas'
        move(foto, os.path.join(DIR_PROCESADAS, nombre_archivo))

if __name__ == "__main__":
    ejecutar_agente()