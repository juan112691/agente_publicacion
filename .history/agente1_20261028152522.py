import os
import glob
import json
import re
import random
import ollama
from datetime import datetime
from shutil import move
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --- Configuración de Directorios ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_ENTRADA = os.path.join(BASE_DIR, "imagenes_brutas")
DIR_SALIDA = os.path.join(BASE_DIR, "publicaciones")
DIR_PROCESADAS = os.path.join(BASE_DIR, "procesadas")
DIR_PLANTILLAS = os.path.join(BASE_DIR, "plantillas")
FUENTE_PATH = "C:/Windows/Fonts/arialbd.ttf" # Tipografía negrita de Windows

# Crear carpetas si no existen
for d in [DIR_ENTRADA, DIR_SALIDA, DIR_PROCESADAS, DIR_PLANTILLAS]:
    os.makedirs(d, exist_ok=True)

# --- CONFIGURACIÓN DE CATÁLOGO DE PLANTILLAS ---
# Configura aquí las coordenadas (X, Y, Ancho, Alto) para cada una de tus plantillas
CATALOGO_PLANTILLAS = {
    
    "plantilla_1": {
        "archivo": os.path.join(DIR_PLANTILLAS, "plantilla_1.png"),
        "forma": "rectangulo",
        "posicion_foto": (0, 170, 1080, 580), # (X, Y, Ancho, Alto)
        "pos_titulo": (50, 60),
        "pos_ubicacion": (50, 120)
    },
    
    "plantilla_2": {
        "archivo": os.path.join(DIR_PLANTILLAS, "plantilla_2.png"),
        "forma": "circulo",
        "posicion_foto": (140, 200, 800, 800), # Círculo de 800x800 centrado
        "pos_titulo": (60, 120),
        "pos_ubicacion": (60, 180)
    },
    "plantilla_3": {
        "archivo": os.path.join(DIR_PLANTILLAS, "plantilla_3.png"),
        "forma": "rectangulo",
        "posicion_foto": (50, 150, 980, 600),
        "pos_titulo": (50, 780),
        "pos_ubicacion": (50, 840)
    }
    # Agrega aquí desde plantilla_4 hasta plantilla_10 ajustando las coordenadas
}

# --- 1. Módulo LLM Multimodal Gratuito (Ollama + LLaVA) ---

def analizar_foto_con_llm(ruta_imagen):
    print(f"🤖 Analizando imagen: {os.path.basename(ruta_imagen)}...")
    
    plantillas_disponibles = list(CATALOGO_PLANTILLAS.keys())
    
    prompt = (
        "Analiza esta imagen de un inmueble en Perú. "
        "Devuelve SOLO un objeto JSON válido sin texto adicional, sin explicaciones y sin bloques markdown. "
        '{"titulo": "TASACIÓN DE DEPARTAMENTO", "ubicacion": "MIRAFLORES, LIMA", "plantilla": "plantilla_1"}. '
        "Opciones para 'titulo': 'TASACIÓN DE TERRENO', 'TASACIÓN LOCALES COMERCIALES', "
        "'TASACIÓN DE EDIFICIO', 'TASACIÓN DE DEPARTAMENTO', 'TASACIÓN DE CASAS'. "
        f"Opciones para 'plantilla': {plantillas_disponibles}."
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
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            raise ValueError("No se encontró JSON válido")
            
    except Exception as e:
        print(f"⚠️ Aviso del LLM: {e}. Se utilizarán datos por defecto.")
        return {
            "titulo": "TASACIÓN DE INMUEBLE", 
            "ubicacion": "LIMA, PERÚ", 
            "plantilla": random.choice(plantillas_disponibles)
        }

# --- 2. Funciones de Máscara y Renderizado Gráfico ---

def recortar_foto(foto, forma, ancho, alto):
    """Ajusta y recorta la foto en rectángulo o círculo perfecto."""
    foto_fit = ImageOps.fit(foto, (ancho, alto), Image.Resampling.LANCZOS)
    
    if forma == "circulo":
        mascara = Image.new('L', (ancho, alto), 0)
        draw = ImageDraw.Draw(mascara)
        draw.ellipse((0, 0, ancho, alto), fill=255)
        
        resultado = Image.new('RGBA', (ancho, alto), (0, 0, 0, 0))
        resultado.paste(foto_fit, (0, 0), mascara)
        return resultado
    
    return foto_fit

def generar_diseno_publicitario(ruta_foto, datos_llm):
    # Validar o seleccionar plantilla
    id_plantilla = datos_llm.get("plantilla")
    if id_plantilla not in CATALOGO_PLANTILLAS:
        id_plantilla = random.choice(list(CATALOGO_PLANTILLAS.keys()))
        print(f"🎲 Seleccionando plantilla al azar: {id_plantilla}")
    else:
        print(f"🎨 Usando plantilla seleccionada por LLM: {id_plantilla}")

    config = CATALOGO_PLANTILLAS[id_plantilla]
    
    # 1. Crear fondo base 1080x1080 (Blanco)
    fondo = Image.new("RGBA", (1080, 1080), (255, 255, 255, 255))

    # 2. Cargar y procesar la foto del inmueble
    foto = Image.open(ruta_foto).convert("RGBA")
    x, y, ancho, alto = config["posicion_foto"]
    
    foto_procesada = recortar_foto(foto, config["forma"], ancho, alto)
    fondo.paste(foto_procesada, (x, y), foto_procesada if config["forma"] == "circulo" else None)

    # 3. Superponer la Plantilla PNG correspondiente
    if os.path.exists(config["archivo"]):
        marco = Image.open(config["archivo"]).convert("RGBA")
        fondo.alpha_composite(marco)
    else:
        print(f"⚠️ No se encontró la plantilla en '{config['archivo']}'. Se usará lienzo blanco.")

    # 4. Dibujar textos dinámicos
    resultado = fondo.convert("RGB")
    draw = ImageDraw.Draw(resultado)
    COLOR_VERDE_CORPORATIVO = "#004B49"

    try:
        font_titulo = ImageFont.truetype(FUENTE_PATH, 42)
        font_ubicacion = ImageFont.truetype(FUENTE_PATH, 32)
    except IOError:
        font_titulo = font_ubicacion = ImageFont.load_default()

    titulo_texto = datos_llm.get("titulo", "TASACIÓN DE INMUEBLE").upper()
    ubicacion_texto = datos_llm.get("ubicacion", "LIMA, PERÚ").upper()

    draw.text(config["pos_titulo"], titulo_texto, font=font_titulo, fill=COLOR_VERDE_CORPORATIVO)
    draw.text(config["pos_ubicacion"], ubicacion_texto, font=font_ubicacion, fill=COLOR_VERDE_CORPORATIVO)

    return resultado

# --- 3. Ejecución del Agente (UNA SOLA FOTO POR EJECUCIÓN) ---

def ejecutar_agente():
    patrones = [os.path.join(DIR_ENTRADA, "*.jpg"), os.path.join(DIR_ENTRADA, "*.png"), os.path.join(DIR_ENTRADA, "*.JPG")]
    fotos = [f for p in patrones for f in glob.glob(p)]

    if not fotos:
        print("📁 Coloca una imagen en 'imagenes_brutas' para iniciar.")
        return

    # Tomar únicamente LA PRIMERA foto encontrada
    foto = fotos[0]
    nombre_archivo = os.path.basename(foto)
    
    print(f"🚀 Procesando publicación única para: {nombre_archivo}")
    
    # 1. Analizar imagen con LLM
    datos = analizar_foto_con_llm(foto)
    
    # 2. Generar el diseño
    imagen_final = generar_diseno_publicitario(foto, datos)
    
    # 3. Guardar el resultado final
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_salida = os.path.join(DIR_SALIDA, f"post_{timestamp}_{nombre_archivo}")
    imagen_final.save(ruta_salida, "PNG")
    
    print(f"✅ Publicación única generada con éxito: {ruta_salida}")

    # 4. Mover la foto procesada a su carpeta final
    move(foto, os.path.join(DIR_PROCESADAS, nombre_archivo))

if __name__ == "__main__":
    ejecutar_agente()