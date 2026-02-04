#!/usr/bin/env python3
"""
Pixel Check Pro v1.1 - Análisis MEJORADO de sensores
Con detección de problemas y diagnósticos avanzados
"""
import sys, os, json, numpy as np, cv2, pandas as pd
from datetime import datetime
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("pixel_check.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def verificar_dark_frame(img_normalizada):
    """
    Verifica si realmente es un dark frame
    Devuelve True si parece ser dark frame válido
    """
    media = np.mean(img_normalizada)
    desv = np.std(img_normalizada)
    
    # En un dark frame verdadero:
    # - La media debería ser baja (poca señal)
    # - El SNR debería ser razonable (> 10 dB)
    
    snr_db = 20 * np.log10(media / desv) if desv > 0 and media > 0 else -100
    
    # Umbrales para dark frame válido
    es_dark_frame = (
        media < 0.1 and          # Media baja (menos del 10% del rango)
        snr_db > 10 and          # SNR aceptable
        desv < 0.05              # Desviación baja
    )
    
    return es_dark_frame, {
        "media": float(media),
        "desviacion": float(desv),
        "snr_db": float(snr_db),
        "es_valido": bool(es_dark_frame)
    }

def analizar_sensor_mejorado(imagen_path):
    """Análisis científico MEJORADO del sensor"""
    logger.info(f"Analizando: {imagen_path}")
    
    # Cargar imagen
    img = cv2.imread(imagen_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"No se pudo cargar: {imagen_path}")
    
    # Convertir a escala de grises
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # DETECTAR BIT DEPTH automáticamente
    max_val = img.max()
    if max_val <= 255:
        bit_depth = 8
    elif max_val <= 4095:
        bit_depth = 12
    elif max_val <= 16383:
        bit_depth = 14
    else:
        bit_depth = 16
    
    logger.info(f"Bit depth detectado: {bit_depth}-bit")
    
    # Normalizar correctamente
    img_float = img.astype(np.float32)
    max_posible = 2 ** bit_depth - 1
    img_norm = img_float / max_posible
    
    # VERIFICAR si es dark frame real
    es_dark, info_dark = verificar_dark_frame(img_norm)
    
    if not es_dark:
        logger.warning("¡ADVERTENCIA! Esto NO parece un dark frame válido")
        logger.warning(f"Media: {info_dark['media']:.4f}, SNR: {info_dark['snr_db']:.1f} dB")
    
    # Estadísticas robustas
    flat = img_norm.flatten()
    media = np.mean(flat)
    desv = np.std(flat)
    mediana = np.median(flat)
    q1, q3 = np.percentile(flat, [25, 75])
    iqr = q3 - q1
    
    # Umbrales AJUSTADOS para DSLR
    # Más estrictos para evitar falsos positivos
    umbral_hot_sigma = media + 6 * desv    # 6σ en lugar de 5σ
    umbral_dead_sigma = media - 6 * desv
    
    umbral_hot_iqr = q3 + 3.5 * iqr        # 3.5*IQR en lugar de 3
    umbral_dead_iqr = q1 - 3.5 * iqr
    
    mad = np.median(np.abs(flat - mediana))
    umbral_hot_mad = mediana + 4.0 * mad   # 4.0*MAD en lugar de 3.5
    umbral_dead_mad = mediana - 4.0 * mad
    
    # Detección por consenso (más estricta)
    hot_sigma = img_norm > umbral_hot_sigma
    hot_iqr = img_norm > umbral_hot_iqr
    hot_mad = img_norm > umbral_hot_mad
    
    dead_sigma = img_norm < umbral_dead_sigma
    dead_iqr = img_norm < umbral_dead_iqr
    dead_mad = img_norm < umbral_dead_mad
    
    # Requerir que 2 de 3 métodos coincidan
    hot_det = (hot_sigma.astype(int) + hot_iqr.astype(int) + hot_mad.astype(int)) >= 2
    dead_det = (dead_sigma.astype(int) + dead_iqr.astype(int) + dead_mad.astype(int)) >= 2
    
    # Contar defectos
    hot_pix = int(np.sum(hot_det))
    dead_pix = int(np.sum(dead_det))
    total_pix = img_norm.size
    
    # Porcentajes
    hot_porc = (hot_pix / total_pix) * 100
    dead_porc = (dead_pix / total_pix) * 100
    
    # SNR real
    snr_linear = media / desv if desv > 0 else 0
    snr_db = 20 * np.log10(snr_linear) if snr_linear > 0 else -100
    
    # Clasificación ISO MEJORADA
    if hot_porc < 0.001 and dead_porc < 0.0005 and snr_db > 30:
        clase_iso = "A+ (Excelente - Profesional)"
        recomendacion = "Sensor en óptimas condiciones"
    elif hot_porc < 0.005 and dead_porc < 0.002 and snr_db > 25:
        clase_iso = "A (Bueno - Avanzado)"
        recomendacion = "Sensor adecuado para uso profesional"
    elif hot_porc < 0.01 and dead_porc < 0.005 and snr_db > 20:
        clase_iso = "B (Aceptable - Enthusiast)"
        recomendacion = "Adecuado para fotografía avanzada"
    elif hot_porc < 0.02 and dead_porc < 0.01 and snr_db > 15:
        clase_iso = "C (Básico - Consumer)"
        recomendacion = "Aceptable para uso general"
    else:
        clase_iso = "D (Deficiente - Requiere atención)"
        if snr_db < 10:
            recomendacion = "¡NO ES DARK FRAME! Verifique captura"
        elif hot_porc > 0.1:
            recomendacion = "Sensor con defectos severos. Revisión urgente"
        else:
            recomendacion = "Sensor necesita calibración/reparación"
    
    # Análisis de distribución
    hist, bins = np.histogram(flat, bins=50)
    moda_idx = np.argmax(hist)
    moda_valor = (bins[moda_idx] + bins[moda_idx + 1]) / 2
    
    return {
        "archivo": Path(imagen_path).name,
        "resolucion": f"{img.shape[1]}x{img.shape[0]}",
        "total_pixeles": int(total_pix),
        "bit_depth": bit_depth,
        "hot_pixels": hot_pix,
        "dead_pixels": dead_pix,
        "hot_porcentaje": float(hot_porc),
        "dead_porcentaje": float(dead_porc),
        "clase_iso": clase_iso,
        "recomendacion": recomendacion,
        "snr_db": float(snr_db),
        "fecha_analisis": datetime.now().isoformat(),
        "estadisticas": {
            "media": float(media),
            "desviacion": float(desv),
            "mediana": float(mediana),
            "q1": float(q1),
            "q3": float(q3),
            "iqr": float(iqr),
            "moda": float(moda_valor),
            "min": float(np.min(flat)),
            "max": float(np.max(flat))
        },
        "dark_frame_valido": info_dark,
        "umbrales_usados": {
            "sigma": 6.0,
            "iqr_mult": 3.5,
            "mad_mult": 4.0
        }
    }

def generar_diagnostico(resultados):
    """Genera diagnóstico detallado basado en resultados"""
    diagnostico = []
    
    # Verificar SNR
    if resultados["snr_db"] < 10:
        diagnostico.append("❌ SNR MUY BAJO: Esto NO parece un dark frame verdadero")
        diagnostico.append("   → Posible luz en la imagen o ISO extremo")
    
    # Verificar hot pixels excesivos
    if resultados["hot_porcentaje"] > 0.1:
        diagnostico.append(f"🔥 HOT PIXELS EXCESIVOS: {resultados['hot_pixels']:,} ({resultados['hot_porcentaje']:.3f}%)")
        diagnostico.append("   → Sensor sobrecalentado o dañado")
    
    # Verificar distribución
    media = resultados["estadisticas"]["media"]
    if media > 0.1:
        diagnostico.append(f"📈 MEDIA ALTA: {media:.4f} (debe ser < 0.1 para dark frame)")
        diagnostico.append("   → No es dark frame puro")
    
    # Recomendaciones específicas
    if "NO ES DARK FRAME" in resultados["recomendacion"]:
        diagnostico.append("🎯 RECOMENDACIÓN: Capturar dark frame correcto:")
        diagnostico.append("   1. Tapa OBJETIVO puesta (no cuerpo)")
        diagnostico.append("   2. ISO 100-400")
        diagnostico.append("   3. Exposición 1-30 segundos")
        diagnostico.append("   4. Temperatura ambiente (20-25°C)")
    
    return diagnostico

def guardar_resultados_completos(resultados, nombre_base):
    """Guardar resultados en JSON, Excel y reporte de texto"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. JSON completo
    json_file = f"resultado_{nombre_base}_{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    # 2. Excel resumido
    excel_file = f"resultado_{nombre_base}_{timestamp}.xlsx"
    datos_excel = {
        "Campo": [
            "Archivo", "Resolución", "Bit Depth", "Total píxeles",
            "Hot Pixels", "Dead Pixels", "% Hot", "% Dead",
            "Clase ISO", "Recomendación", "SNR (dB)",
            "Media", "Desviación", "Fecha análisis"
        ],
        "Valor": [
            resultados["archivo"],
            resultados["resolucion"],
            f"{resultados['bit_depth']}-bit",
            f"{resultados['total_pixeles']:,}",
            f"{resultados['hot_pixels']:,}",
            f"{resultados['dead_pixels']:,}",
            f"{resultados['hot_porcentaje']:.6f}%",
            f"{resultados['dead_porcentaje']:.6f}%",
            resultados["clase_iso"],
            resultados["recomendacion"],
            f"{resultados['snr_db']:.2f}",
            f"{resultados['estadisticas']['media']:.4f}",
            f"{resultados['estadisticas']['desviacion']:.4f}",
            resultados["fecha_analisis"]
        ]
    }
    
    df_excel = pd.DataFrame(datos_excel)
    df_excel.to_excel(excel_file, index=False)
    
    # 3. Reporte de texto (legible)
    txt_file = f"diagnostico_{nombre_base}_{timestamp}.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("PIXEL CHECK PRO - DIAGNÓSTICO COMPLETO\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"📷 CÁMARA ANALIZADA: {resultados['archivo']}\n")
        f.write(f"📐 RESOLUCIÓN: {resultados['resolucion']} ({resultados['bit_depth']}-bit)\n")
        f.write(f"🔢 TOTAL PÍXELES: {resultados['total_pixeles']:,}\n\n")
        
        f.write("📊 DEFECTOS DETECTADOS:\n")
        f.write("-" * 40 + "\n")
        f.write(f"🔥 Hot Pixels: {resultados['hot_pixels']:,} ({resultados['hot_porcentaje']:.4f}%)\n")
        f.write(f"💀 Dead Pixels: {resultados['dead_pixels']:,} ({resultados['dead_porcentaje']:.4f}%)\n")
        f.write(f"📈 Total defectos: {resultados['hot_pixels'] + resultados['dead_pixels']:,} ")
        f.write(f"({resultados['hot_porcentaje'] + resultados['dead_porcentaje']:.4f}%)\n\n")
        
        f.write("🎯 CLASIFICACIÓN:\n")
        f.write("-" * 40 + "\n")
        f.write(f"🏷️  Clase ISO: {resultados['clase_iso']}\n")
        f.write(f"📋 Recomendación: {resultados['recomendacion']}\n\n")
        
        f.write("📶 MÉTRICAS DE CALIDAD:\n")
        f.write("-" * 40 + "\n")
        f.write(f"📡 SNR: {resultados['snr_db']:.2f} dB\n")
        f.write(f"📊 Media: {resultados['estadisticas']['media']:.4f}\n")
        f.write(f"📉 Desviación: {resultados['estadisticas']['desviacion']:.4f}\n")
        f.write(f"📐 Mediana: {resultados['estadisticas']['mediana']:.4f}\n")
        f.write(f"📈 Moda: {resultados['estadisticas']['moda']:.4f}\n\n")
        
        # Diagnóstico
        diagnostico = generar_diagnostico(resultados)
        if diagnostico:
            f.write("⚠️  DIAGNÓSTICO:\n")
            f.write("-" * 40 + "\n")
            for linea in diagnostico:
                f.write(linea + "\n")
            f.write("\n")
        
        f.write("ℹ️  INFORMACIÓN TÉCNICA:\n")
        f.write("-" * 40 + "\n")
        f.write(f"📅 Fecha análisis: {resultados['fecha_analisis']}\n")
        f.write(f"⚙️  Umbral sigma: {resultados['umbrales_usados']['sigma']}σ\n")
        f.write(f"📏 Umbral IQR: {resultados['umbrales_usados']['iqr_mult']}×IQR\n")
        f.write(f"📐 Umbral MAD: {resultados['umbrales_usados']['mad_mult']}×MAD\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("📁 ARCHIVOS GENERADOS:\n")
        f.write(f"• {json_file} (datos completos JSON)\n")
        f.write(f"• {excel_file} (tabla resumen Excel)\n")
        f.write(f"• {txt_file} (este reporte)\n")
        f.write(f"• pixel_check.log (log de ejecución)\n")
        f.write("=" * 60 + "\n")
    
    return json_file, excel_file, txt_file

def main():
    """Función principal MEJORADA"""
    if len(sys.argv) < 2:
        print("PIXEL CHECK PRO v1.1 - Análisis MEJORADO")
        print("=" * 50)
        print("Uso: python pixel_check.py <ruta_imagen.tif>")
        print()
        print("📋 INSTRUCCIONES PARA DARK FRAME CORRECTO:")
        print("1. Modo Manual (M), ISO 100-400")
        print("2. Tapa OBJETIVO puesta (no cuerpo de cámara)")
        print("3. Exposición: 1-30 segundos")
        print("4. Temperatura ambiente (20-25°C)")
        print("5. Exportar a TIFF 16-bit SIN compresión")
        print("=" * 50)
        return 1
    
    imagen_path = sys.argv[1]
    
    if not os.path.exists(imagen_path):
        print(f"❌ ERROR: Archivo no encontrado: {imagen_path}")
        return 1
    
    try:
        print("\n" + "="*60)
        print("PIXEL CHECK PRO v1.1 - ANÁLISIS CIENTÍFICO MEJORADO")
        print("="*60)
        
        print(f"\n🔬 ANALIZANDO: {os.path.basename(imagen_path)}")
        print("   (Esto puede tomar unos segundos...)")
        
        resultados = analizar_sensor_mejorado(imagen_path)
        
        nombre_base = Path(imagen_path).stem
        json_file, excel_file, txt_file = guardar_resultados_completos(resultados, nombre_base)
        
        # Mostrar resultados en pantalla
        print("\n📊 RESULTADOS PRINCIPALES:")
        print("-" * 50)
        
        print(f"📷 Archivo: {resultados['archivo']}")
        print(f"📐 Resolución: {resultados['resolucion']} ({resultados['bit_depth']}-bit)")
        print(f"🔢 Total píxeles: {resultados['total_pixeles']:,}")
        
        print(f"\n🔥 Hot Pixels: {resultados['hot_pixels']:,} ({resultados['hot_porcentaje']:.4f}%)")
        print(f"💀 Dead Pixels: {resultados['dead_pixels']:,} ({resultados['dead_porcentaje']:.4f}%)")
        
        print(f"\n🏷️  Clase ISO: {resultados['clase_iso']}")
        print(f"📋 {resultados['recomendacion']}")
        
        print(f"\n📶 SNR: {resultados['snr_db']:.2f} dB")
        print(f"📊 Media: {resultados['estadisticas']['media']:.4f}")
        
        # Mostrar diagnóstico si hay problemas
        diagnostico = generar_diagnostico(resultados)
        if diagnostico:
            print("\n⚠️  DIAGNÓSTICO DETECTADO:")
            print("-" * 50)
            for linea in diagnostico:
                print(linea)
        
        print("\n" + "="*60)
        print("✅ ANÁLISIS COMPLETADO")
        print("📁 ARCHIVOS GUARDADOS:")
        print(f"   📄 {json_file}")
        print(f"   📊 {excel_file}")
        print(f"   📝 {txt_file}")
        print(f"   📋 pixel_check.log")
        print("="*60 + "\n")
        
        # Advertencia final si hay problemas graves
        if resultados["clase_iso"].startswith("D"):
            print("🚨 ¡ATENCIÓN! Sensor en estado DEFICIENTE")
            print("   Considere revisión profesional de la cámara\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error en análisis: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        print("📝 Ver pixel_check.log para detalles técnicos")
        return 1

if __name__ == "__main__":
    sys.exit(main())