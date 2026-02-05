#!/usr/bin/env python3
"""
Pixel Check Pro v3.0 - Sistema Profesional de Análisis de Sensores
Soporte completo para DSLR, Mirrorless y cámaras científicas
"""

import sys
import os
import argparse
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

import numpy as np
import cv2
import pandas as pd
from PIL import Image
import rawpy
import tifffile
import exifread
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats, ndimage
from tqdm import tqdm
import colorama
from colorama import Fore, Style

# Inicializar colorama para colores en terminal
colorama.init(autoreset=True)

# ============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================================

class ImageFormat(Enum):
    """Formatos de imagen soportados"""
    TIFF = "tiff"
    RAW = "raw"
    JPEG = "jpeg"
    PNG = "png"
    DNG = "dng"
    NEF = "nef"
    CR2 = "cr2"
    CR3 = "cr3"

class SensorType(Enum):
    """Tipos de sensor conocidos"""
    DSLR = "dslr"
    MIRRORLESS = "mirrorless"
    SCIENTIFIC = "scientific"
    PHONE = "phone"
    UNKNOWN = "unknown"

@dataclass
class AnalysisConfig:
    """Configuración para el análisis"""
    # Umbrales de detección
    hot_pixel_sigma: float = 6.0
    dead_pixel_sigma: float = 6.0
    hot_pixel_iqr_mult: float = 3.5
    dead_pixel_iqr_mult: float = 3.5
    hot_pixel_mad_mult: float = 4.0
    dead_pixel_mad_mult: float = 4.0
    
    # Configuración de análisis
    min_snr_db: float = 10.0
    max_dark_mean: float = 0.1
    require_dark_frame: bool = True
    generate_heatmap: bool = True
    save_intermediate: bool = False
    
    # Configuración de salida
    output_formats: List[str] = None
    
    def __post_init__(self):
        if self.output_formats is None:
            self.output_formats = ["json", "excel", "txt", "html"]

@dataclass
class PixelStats:
    """Estadísticas de píxeles"""
    total_pixels: int
    hot_pixels: int
    dead_pixels: int
    hot_percentage: float
    dead_percentage: float
    mean: float
    std: float
    median: float
    min: float
    max: float
    q1: float
    q3: float
    iqr: float
    mad: float
    snr_db: float

@dataclass
class ImageMetadata:
    """Metadatos de la imagen"""
    filename: str
    format: str
    sensor_type: str
    resolution: Tuple[int, int]
    bit_depth: int
    color_space: str
    exposure_time: Optional[float] = None
    iso: Optional[int] = None
    aperture: Optional[float] = None
    camera_model: Optional[str] = None
    timestamp: Optional[str] = None

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

def setup_logging(verbose: bool = False, log_file: str = "pixel_check.log"):
    """Configurar sistema de logging profesional"""
    
    # Crear directorio de logs si no existe
    log_dir = Path(log_file).parent
    log_dir.mkdir(exist_ok=True)
    
    # Configurar nivel
    level = logging.DEBUG if verbose else logging.INFO
    
    # Formateadores
    console_format = logging.Formatter(
        f"{Fore.CYAN}%(asctime)s{Fore.RESET} - "
        f"{Fore.YELLOW}%(levelname)s{Fore.RESET} - "
        f"%(message)s",
        datefmt="%H:%M:%S"
    )
    
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_format)
    console_handler.setLevel(level)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(file_format)
    file_handler.setLevel(logging.DEBUG)
    
    # Configurar logger raíz
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[console_handler, file_handler]
    )
    
    # Reducir verbosidad de algunas librerías
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# ============================================================================
# MANEJO DE IMÁGENES
# ============================================================================

class ImageLoader:
    """Cargador de imágenes con soporte para múltiples formatos"""
    
    @staticmethod
    def load_image(image_path: str) -> Tuple[np.ndarray, ImageMetadata]:
        """Cargar imagen de cualquier formato soportado"""
        path = Path(image_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {image_path}")
        
        # Determinar formato
        extension = path.suffix.lower()
        
        if extension in ['.tif', '.tiff']:
            return ImageLoader._load_tiff(path)
        elif extension in ['.nef', '.cr2', '.cr3', '.dng', '.arw', '.orf']:
            return ImageLoader._load_raw(path)
        elif extension in ['.jpg', '.jpeg', '.png']:
            return ImageLoader._load_standard(path)
        else:
            raise ValueError(f"Formato no soportado: {extension}")
    
    @staticmethod
    def _load_tiff(path: Path) -> Tuple[np.ndarray, ImageMetadata]:
        """Cargar imagen TIFF"""
        logger = logging.getLogger(__name__)
        logger.info(f"Cargando TIFF: {path.name}")
        
        try:
            with tifffile.TiffFile(path) as tif:
                image = tif.asarray()
                
                # Obtener metadatos
                metadata = ImageMetadata(
                    filename=path.name,
                    format="TIFF",
                    sensor_type=SensorType.UNKNOWN.value,
                    resolution=(image.shape[1], image.shape[0]),
                    bit_depth=tif.pages[0].bitspersample,
                    color_space="Gray" if len(image.shape) == 2 else "RGB"
                )
                
                return image, metadata
                
        except Exception as e:
            logger.error(f"Error cargando TIFF: {e}")
            raise
    
    @staticmethod
    def _load_raw(path: Path) -> Tuple[np.ndarray, ImageMetadata]:
        """Cargar imagen RAW"""
        logger = logging.getLogger(__name__)
        logger.info(f"Cargando RAW: {path.name}")
        
        try:
            with rawpy.imread(str(path)) as raw:
                # Procesar RAW a RGB
                rgb = raw.postprocess()
                
                # Convertir a escala de grises
                if len(rgb.shape) == 3:
                    image = np.mean(rgb, axis=2).astype(np.float32)
                else:
                    image = rgb.astype(np.float32)
                
                # Obtener metadatos
                metadata = ImageMetadata(
                    filename=path.name,
                    format=path.suffix.upper()[1:],
                    sensor_type=SensorType.DSLR.value,
                    resolution=(image.shape[1], image.shape[0]),
                    bit_depth=raw.raw_type,
                    color_space="RGB" if len(rgb.shape) == 3 else "Gray"
                )
                
                # Extraer EXIF
                try:
                    exif = raw.extract_thumb().to_exif()
                    # Aquí podrías parsear más metadatos
                except:
                    pass
                
                return image, metadata
                
        except Exception as e:
            logger.error(f"Error cargando RAW: {e}")
            # Fallback a PIL
            return ImageLoader._load_standard(path)
    
    @staticmethod
    def _load_standard(path: Path) -> Tuple[np.ndarray, ImageMetadata]:
        """Cargar imagen estándar (JPEG, PNG)"""
        logger = logging.getLogger(__name__)
        logger.info(f"Cargando imagen estándar: {path.name}")
        
        try:
            with Image.open(path) as img:
                # Convertir a numpy array
                image = np.array(img)
                
                # Convertir a escala de grises si es color
                if len(image.shape) == 3:
                    if image.shape[2] == 4:  # RGBA
                        image = image[:, :, :3]  # Remover alpha
                    image = np.mean(image, axis=2)
                
                # Obtener metadatos
                metadata = ImageMetadata(
                    filename=path.name,
                    format=img.format,
                    sensor_type=SensorType.UNKNOWN.value,
                    resolution=img.size,
                    bit_depth=img.bits if hasattr(img, 'bits') else 8,
                    color_space=img.mode
                )
                
                return image, metadata
                
        except Exception as e:
            logger.error(f"Error cargando imagen: {e}")
            raise

# ============================================================================
# ANÁLISIS DE PÍXELES
# ============================================================================

class PixelAnalyzer:
    """Analizador avanzado de píxeles"""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze_image(self, image: np.ndarray) -> PixelStats:
        """Analizar imagen y detectar defectos"""
        self.logger.info("Iniciando análisis de píxeles")
        
        # Normalizar imagen
        image_norm = self._normalize_image(image)
        
        # Verificar si es dark frame válido
        if self.config.require_dark_frame:
            self._validate_dark_frame(image_norm)
        
        # Aplanar imagen para análisis
        flat = image_norm.flatten()
        
        # Calcular estadísticas básicas
        stats = self._compute_basic_stats(flat)
        
        # Detectar píxeles defectuosos
        hot_mask, dead_mask = self._detect_defective_pixels(image_norm, stats)
        
        # Contar defectos
        stats.hot_pixels = int(np.sum(hot_mask))
        stats.dead_pixels = int(np.sum(dead_mask))
        stats.total_pixels = image_norm.size
        
        # Calcular porcentajes
        stats.hot_percentage = (stats.hot_pixels / stats.total_pixels) * 100
        stats.dead_percentage = (stats.dead_pixels / stats.total_pixels) * 100
        
        # Calcular SNR
        stats.snr_db = 20 * np.log10(stats.mean / stats.std) if stats.std > 0 else -100
        
        self.logger.info(f"Hot pixels: {stats.hot_pixels:,} ({stats.hot_percentage:.4f}%)")
        self.logger.info(f"Dead pixels: {stats.dead_pixels:,} ({stats.dead_percentage:.4f}%)")
        self.logger.info(f"SNR: {stats.snr_db:.2f} dB")
        
        return stats, hot_mask, dead_mask
    
    def _normalize_image(self, image: np.ndarray) -> np.ndarray:
        """Normalizar imagen a rango [0, 1]"""
        # Detectar bit depth
        max_val = np.max(image)
        
        if max_val <= 255:
            bit_depth = 8
        elif max_val <= 4095:
            bit_depth = 12
        elif max_val <= 16383:
            bit_depth = 14
        else:
            bit_depth = 16
        
        self.logger.info(f"Bit depth detectado: {bit_depth}")
        
        # Normalizar
        max_possible = 2 ** bit_depth - 1
        image_norm = image.astype(np.float32) / max_possible
        
        return image_norm
    
    def _validate_dark_frame(self, image_norm: np.ndarray):
        """Validar que sea un dark frame verdadero"""
        mean = np.mean(image_norm)
        std = np.std(image_norm)
        snr_db = 20 * np.log10(mean / std) if std > 0 and mean > 0 else -100
        
        issues = []
        
        if mean > self.config.max_dark_mean:
            issues.append(f"Media alta ({mean:.4f} > {self.config.max_dark_mean})")
        
        if snr_db < self.config.min_snr_db:
            issues.append(f"SNR bajo ({snr_db:.1f} dB < {self.config.min_snr_db} dB)")
        
        if issues:
            warning_msg = "Posiblemente NO es un dark frame válido: " + ", ".join(issues)
            self.logger.warning(warning_msg)
    
    def _compute_basic_stats(self, flat: np.ndarray) -> PixelStats:
        """Calcular estadísticas básicas"""
        return PixelStats(
            total_pixels=len(flat),
            hot_pixels=0,
            dead_pixels=0,
            hot_percentage=0.0,
            dead_percentage=0.0,
            mean=float(np.mean(flat)),
            std=float(np.std(flat)),
            median=float(np.median(flat)),
            min=float(np.min(flat)),
            max=float(np.max(flat)),
            q1=float(np.percentile(flat, 25)),
            q3=float(np.percentile(flat, 75)),
            iqr=float(np.percentile(flat, 75) - np.percentile(flat, 25)),
            mad=float(np.median(np.abs(flat - np.median(flat)))),
            snr_db=0.0
        )
    
    def _detect_defective_pixels(self, image_norm: np.ndarray, stats: PixelStats) -> Tuple[np.ndarray, np.ndarray]:
        """Detectar píxeles defectuosos usando múltiples métodos"""
        
        # Método 1: Desviación estándar
        hot_sigma = image_norm > (stats.mean + self.config.hot_pixel_sigma * stats.std)
        dead_sigma = image_norm < (stats.mean - self.config.dead_pixel_sigma * stats.std)
        
        # Método 2: IQR
        hot_iqr = image_norm > (stats.q3 + self.config.hot_pixel_iqr_mult * stats.iqr)
        dead_iqr = image_norm < (stats.q1 - self.config.dead_pixel_iqr_mult * stats.iqr)
        
        # Método 3: MAD
        hot_mad = image_norm > (stats.median + self.config.hot_pixel_mad_mult * stats.mad)
        dead_mad = image_norm < (stats.median - self.config.dead_pixel_mad_mult * stats.mad)
        
        # Consenso (2 de 3 métodos deben coincidir)
        hot_consensus = (hot_sigma.astype(int) + hot_iqr.astype(int) + hot_mad.astype(int)) >= 2
        dead_consensus = (dead_sigma.astype(int) + dead_iqr.astype(int) + dead_mad.astype(int)) >= 2
        
        return hot_consensus, dead_consensus

# ============================================================================
# GENERACIÓN DE REPORTES
# ============================================================================

class ReportGenerator:
    """Generador de reportes profesionales"""
    
    def __init__(self, output_dir: str = "resultados"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_all_reports(self, 
                           stats: PixelStats,
                           metadata: ImageMetadata,
                           config: AnalysisConfig,
                           hot_mask: np.ndarray = None,
                           dead_mask: np.ndarray = None) -> Dict[str, str]:
        """Generar todos los reportes"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{metadata.filename.split('.')[0]}_{timestamp}"
        
        reports = {}
        
        # 1. Reporte JSON
        reports['json'] = self._generate_json_report(stats, metadata, config, base_name)
        
        # 2. Reporte Excel
        reports['excel'] = self._generate_excel_report(stats, metadata, config, base_name)
        
        # 3. Reporte de texto
        reports['txt'] = self._generate_text_report(stats, metadata, config, base_name)
        
        # 4. Reporte HTML
        reports['html'] = self._generate_html_report(stats, metadata, config, base_name)
        
        # 5. Generar visualizaciones si hay máscaras
        if hot_mask is not None and dead_mask is not None:
            reports['images'] = self._generate_visualizations(
                hot_mask, dead_mask, metadata, base_name
            )
        
        return reports
    
    def _generate_json_report(self, stats: PixelStats, metadata: ImageMetadata, 
                            config: AnalysisConfig, base_name: str) -> str:
        """Generar reporte JSON completo"""
        report = {
            "metadata": asdict(metadata),
            "statistics": asdict(stats),
            "configuration": asdict(config),
            "analysis_timestamp": datetime.now().isoformat(),
            "quality_grade": self._calculate_quality_grade(stats)
        }
        
        filename = self.output_dir / f"{base_name}_report.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Reporte JSON guardado: {filename}")
        return str(filename)
    
    def _generate_excel_report(self, stats: PixelStats, metadata: ImageMetadata,
                             config: AnalysisConfig, base_name: str) -> str:
        """Generar reporte Excel"""
        filename = self.output_dir / f"{base_name}_report.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Hoja 1: Resumen
            summary_data = {
                'Métrica': [
                    'Archivo', 'Resolución', 'Bit Depth', 'Total Píxeles',
                    'Hot Pixels', 'Dead Pixels', '% Hot', '% Dead',
                    'Clasificación ISO', 'Recomendación', 'SNR (dB)',
                    'Media', 'Desviación', 'Fecha Análisis'
                ],
                'Valor': [
                    metadata.filename,
                    f"{metadata.resolution[0]}x{metadata.resolution[1]}",
                    f"{metadata.bit_depth}-bit",
                    f"{stats.total_pixels:,}",
                    f"{stats.hot_pixels:,}",
                    f"{stats.dead_pixels:,}",
                    f"{stats.hot_percentage:.6f}%",
                    f"{stats.dead_percentage:.6f}%",
                    self._calculate_iso_class(stats),
                    self._generate_recommendation(stats),
                    f"{stats.snr_db:.2f}",
                    f"{stats.mean:.6f}",
                    f"{stats.std:.6f}",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
            }
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Hoja 2: Estadísticas detalladas
            stats_data = asdict(stats)
            df_stats = pd.DataFrame([stats_data])
            df_stats.to_excel(writer, sheet_name='Estadísticas', index=False)
            
            # Hoja 3: Configuración
            config_data = asdict(config)
            df_config = pd.DataFrame([config_data])
            df_config.to_excel(writer, sheet_name='Configuración', index=False)
        
        self.logger.info(f"Reporte Excel guardado: {filename}")
        return str(filename)
    
    def _generate_text_report(self, stats: PixelStats, metadata: ImageMetadata,
                            config: AnalysisConfig, base_name: str) -> str:
        """Generar reporte de texto legible"""
        filename = self.output_dir / f"{base_name}_report.txt"
        
        iso_class = self._calculate_iso_class(stats)
        recommendation = self._generate_recommendation(stats)
        
        report_text = f"""
{'=' * 70}
PIXEL CHECK PRO v3.0 - REPORTE DE ANÁLISIS
{'=' * 70}

📷 INFORMACIÓN DE LA IMAGEN
{'─' * 40}
• Archivo: {metadata.filename}
• Formato: {metadata.format}
• Resolución: {metadata.resolution[0]}x{metadata.resolution[1]}
• Bit Depth: {metadata.bit_depth}-bit
• Tipo de sensor: {metadata.sensor_type}

📊 DEFECTOS DETECTADOS
{'─' * 40}
• Hot Pixels: {stats.hot_pixels:,} ({stats.hot_percentage:.4f}%)
• Dead Pixels: {stats.dead_pixels:,} ({stats.dead_percentage:.4f}%)
• Total defectos: {stats.hot_pixels + stats.dead_pixels:,} 
  ({(stats.hot_percentage + stats.dead_percentage):.4f}%)

🏷️  CLASIFICACIÓN
{'─' * 40}
• Clase ISO: {iso_class}
• Recomendación: {recommendation}

📈 MÉTRICAS DE CALIDAD
{'─' * 40}
• SNR: {stats.snr_db:.2f} dB
• Media: {stats.mean:.6f}
• Desviación: {stats.std:.6f}
• Mediana: {stats.median:.6f}
• Rango: [{stats.min:.6f}, {stats.max:.6f}]
• IQR: {stats.iqr:.6f}

⚙️  CONFIGURACIÓN USADA
{'─' * 40}
• Umbral sigma: {config.hot_pixel_sigma}σ
• Umbral IQR: {config.hot_pixel_iqr_mult}×IQR
• Umbral MAD: {config.hot_pixel_mad_mult}×MAD

📅 INFORMACIÓN DEL ANÁLISIS
{'─' * 40}
• Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Versión: 3.0

{'=' * 70}
        """.strip()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        self.logger.info(f"Reporte de texto guardado: {filename}")
        return str(filename)
    
    def _calculate_iso_class(self, stats: PixelStats) -> str:
        """Calcular clasificación ISO"""
        if stats.hot_percentage < 0.001 and stats.dead_percentage < 0.0005 and stats.snr_db > 30:
            return "A+ (Excelente - Nivel Profesional)"
        elif stats.hot_percentage < 0.005 and stats.dead_percentage < 0.002 and stats.snr_db > 25:
            return "A (Muy Bueno - Avanzado)"
        elif stats.hot_percentage < 0.01 and stats.dead_percentage < 0.005 and stats.snr_db > 20:
            return "B (Bueno - Entusiasta)"
        elif stats.hot_percentage < 0.02 and stats.dead_percentage < 0.01 and stats.snr_db > 15:
            return "C (Aceptable - Consumidor)"
        else:
            return "D (Deficiente - Requiere Atención)"
    
    def _generate_recommendation(self, stats: PixelStats) -> str:
        """Generar recomendación basada en resultados"""
        if stats.snr_db < 10:
            return "¡NO ES UN DARK FRAME VÁLIDO! Verifique la captura."
        elif stats.hot_percentage > 0.1:
            return "Sensor con defectos severos. Revisión profesional recomendada."
        elif stats.hot_percentage > 0.02:
            return "Sensor necesita calibración. Considere mapeo de píxeles defectuosos."
        elif stats.snr_db > 25:
            return "Sensor en excelente estado. Adecuado para trabajo profesional."
        else:
            return "Sensor en buen estado para uso general."

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal"""
    
    # Configurar argumentos
    parser = argparse.ArgumentParser(
        description="Pixel Check Pro v3.0 - Análisis profesional de sensores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s imagen.tif                    # Analizar archivo único
  %(prog)s --batch directorio/           # Analizar lote
  %(prog)s --no-dark-check               # Desactivar verificación dark frame
  %(prog)s --verbose                     # Modo detallado
        """
    )
    
    parser.add_argument("image", nargs="?", help="Ruta a la imagen a analizar")
    parser.add_argument("--batch", help="Analizar todas las imágenes en un directorio")
    parser.add_argument("--config", help="Archivo de configuración JSON")
    parser.add_argument("--no-dark-check", action="store_true", 
                       help="No verificar si es dark frame")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Modo verboso")
    parser.add_argument("--output-dir", default="resultados",
                       help="Directorio para resultados")
    parser.add_argument("--heatmap", action="store_true",
                       help="Generar mapas de calor de defectos")
    parser.add_argument("--version", action="version", 
                       version="Pixel Check Pro v3.0")
    
    args = parser.parse_args()
    
    # Configurar logging
    logger = setup_logging(args.verbose)
    
    try:
        logger.info(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}PIXEL CHECK PRO v3.0 - Iniciando análisis{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        
        # Verificar que se proporcionó una imagen o modo batch
        if not args.image and not args.batch:
            parser.print_help()
            logger.error("Debe proporcionar una imagen o usar --batch")
            return 1
        
        # Cargar configuración
        config = AnalysisConfig()
        if args.config:
            try:
                with open(args.config, 'r') as f:
                    config_dict = json.load(f)
                    for key, value in config_dict.items():
                        if hasattr(config, key):
                            setattr(config, key, value)
            except Exception as e:
                logger.warning(f"No se pudo cargar configuración: {e}")
        
        # Ajustar configuración según argumentos
        config.require_dark_frame = not args.no_dark_check
        config.generate_heatmap = args.heatmap
        
        # Inicializar componentes
        loader = ImageLoader()
        analyzer = PixelAnalyzer(config)
        reporter = ReportGenerator(args.output_dir)
        
        # Modo batch
        if args.batch:
            return process_batch(args.batch, loader, analyzer, reporter, config)
        
        # Modo archivo único
        return process_single(args.image, loader, analyzer, reporter, config)
        
    except KeyboardInterrupt:
        logger.info("\nAnálisis cancelado por el usuario")
        return 130
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        logger.debug(traceback.format_exc())
        return 1

def process_single(image_path: str, loader: ImageLoader, analyzer: PixelAnalyzer,
                  reporter: ReportGenerator, config: AnalysisConfig) -> int:
    """Procesar un archivo único"""
    logger = logging.getLogger(__name__)
    
    try:
        # Cargar imagen
        logger.info(f"Cargando imagen: {image_path}")
        image, metadata = loader.load_image(image_path)
        
        logger.info(f"Imagen cargada: {metadata.resolution[0]}x{metadata.resolution[1]}, "
                   f"{metadata.bit_depth}-bit, {metadata.format}")
        
        # Analizar
        stats, hot_mask, dead_mask = analyzer.analyze_image(image)
        
        # Generar reportes
        logger.info("Generando reportes...")
        reports = reporter.generate_all_reports(stats, metadata, config, hot_mask, dead_mask)
        
        # Mostrar resumen
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}ANÁLISIS COMPLETADO EXITOSAMENTE{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}RESUMEN:{Style.RESET_ALL}")
        print(f"  📷 Archivo: {metadata.filename}")
        print(f"  📏 Resolución: {metadata.resolution[0]}x{metadata.resolution[1]}")
        print(f"  🔥 Hot Pixels: {stats.hot_pixels:,} ({stats.hot_percentage:.4f}%)")
        print(f"  💀 Dead Pixels: {stats.dead_pixels:,} ({stats.dead_percentage:.4f}%)")
        print(f"  🏷️  Clasificación: {reporter._calculate_iso_class(stats)}")
        print(f"  📶 SNR: {stats.snr_db:.2f} dB")
        
        print(f"\n{Fore.YELLOW}ARCHIVOS GENERADOS:{Style.RESET_ALL}")
        for report_type, report_path in reports.items():
            if isinstance(report_path, str):
                print(f"  • {report_type.upper()}: {Path(report_path).name}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error procesando imagen: {e}")
        return 1

def process_batch(batch_dir: str, loader: ImageLoader, analyzer: PixelAnalyzer,
                 reporter: ReportGenerator, config: AnalysisConfig) -> int:
    """Procesar lote de imágenes"""
    logger = logging.getLogger(__name__)
    
    try:
        batch_path = Path(batch_dir)
        if not batch_path.exists():
            logger.error(f"Directorio no encontrado: {batch_dir}")
            return 1
        
        # Buscar imágenes
        #image_extensions = ['.tif', '.tiff', '.nef', '.cr2', '.cr3', '.dng', 
        #                  '.jpg', '.jpeg', '.png', '.arw', '.orf']
        image_extensions = ['.tif', '.tiff']

        image_files = []
        for ext in image_extensions:
            image_files.extend(batch_path.glob(f"*{ext}"))
            image_files.extend(batch_path.glob(f"*{ext.upper()}"))
        
        if not image_files:
            logger.error("No se encontraron imágenes en el directorio")
            return 1
        
        logger.info(f"Encontradas {len(image_files)} imágenes para analizar")
        
        # Procesar cada imagen
        results = []
        for image_file in tqdm(image_files, desc="Analizando imágenes"):
            try:
                image, metadata = loader.load_image(str(image_file))
                stats, _, _ = analyzer.analyze_image(image)
                
                results.append({
                    'file': metadata.filename,
                    'hot_pixels': stats.hot_pixels,
                    'dead_pixels': stats.dead_pixels,
                    'hot_percentage': stats.hot_percentage,
                    'dead_percentage': stats.dead_percentage,
                    'snr_db': stats.snr_db,
                    'iso_class': reporter._calculate_iso_class(stats)
                })
                
            except Exception as e:
                logger.warning(f"Error procesando {image_file.name}: {e}")
                continue
        
        # Generar reporte consolidado
        if results:
            df = pd.DataFrame(results)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_file = reporter.output_dir / f"batch_report_{timestamp}.xlsx"
            
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Resultados', index=False)
                
                # Agregar estadísticas resumen
                summary = {
                    'Total Imágenes': [len(results)],
                    'Hot Pixels Promedio': [df['hot_percentage'].mean()],
                    'Dead Pixels Promedio': [df['dead_percentage'].mean()],
                    'Mejor SNR': [df['snr_db'].max()],
                    'Peor SNR': [df['snr_db'].min()]
                }
                pd.DataFrame(summary).to_excel(writer, sheet_name='Resumen', index=False)
            
            logger.info(f"Reporte de lote guardado: {excel_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error en procesamiento por lote: {e}")
        return 1

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================
if __name__ == "__main__":
    sys.exit(main())
