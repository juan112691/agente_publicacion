import os
import glob
import json
import ollama
from datetime import datetime
from shutil import move
from PIL import Image, ImageDraw, ImageFont, ImageOps

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

def analizar_foto_con_llm(ruta_imagen):
    """
    Analiza la foto con LLaVA para identificar la categoría
    y sugerir el texto del encabezado.
    """
    print(f"🤖 Analizando imagen: {os.path.basename(ruta_imagen)}...")
    
    prompt = (
        "Analiza esta imagen inmobiliaria y responde ÚNICAMENTE un JSON plano con este formato: "
        '{"titulo": "TASACIÓN DE TERRENO", "ubicacion": "LIMA, PERÚ"}. '
        "El campo 'titulo' debe ser corto, por ejemplo: 'TASACIÓN DE TERRENO', "
        "'TASACIÓN LOCALES COMERCIALES', 'TASACIÓN DE EDIFICIO' o 'TASACIÓN DE DEPARTAMENTO'."
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
        json_str = raw_text[raw_text.find('{'):raw_text.rfind('}')+1]
        return json.loads(json_str)
    except Exception as e:
        print(f"⚠️ Aviso del LLM: {e}. Se utilizarán textos genéricos.")
        return {"titulo": "TASACIÓN DE INMUEBLE", "ubicacion": "LIMA, PERÚ"}

# --- 2. Módulo de Renderizado Gráfico (Pillow) ---

def generar_diseno_publicitario(ruta_foto, datos_llm):
    # Lienzo de 1080x1080 px (Formato estándar para redes)
    lienzo = Image.new("RGB", (1080, 1080), (255, 255, 255))

    # Cargar y ajustar la foto de la propiedad al centro
    foto = Image.open(ruta_foto).convert("RGBA")
    foto_fit = ImageOps.fit(foto, (1080, 600), Image.Resampling.LANCZOS)
    lienzo.paste(foto_fit, (0, 180))

    # Superponer el marco transparente PNG
    if os.path.exists(PLANTILLA_PATH):
        marco = Image.open(PLANTILLA_PATH).convert("RGBA")
        lienzo.paste(marco, (0, 0), marco)

    # Renderizar el texto detectado
    draw = ImageDraw.Draw(lienzo)
    COLOR_VERDE_CORPORATIVO = "#004B49"

    try:
        font_titulo = ImageFont.truetype(FUENTE_PATH, 44)
        font_ubicacion = ImageFont.truetype(FUENTE_PATH, 34)
    except IOError:
        font_titulo = font_ubicacion = ImageFont.load_default()

    # Escribir Título
    draw.text((60, 680), datos_llm["titulo"].upper(), font=font_titulo, fill=COLOR_VERDE_CORPORATIVO)

    # Escribir Ubicación
    draw.text((60, 740), datos_llm["ubicacion"].upper(), font=font_ubicacion, fill=COLOR_VERDE_CORPORATIVO)

    return lienzo

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