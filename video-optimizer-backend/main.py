import os
import subprocess
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

UPLOAD_DIR = Path("/tmp/video_processing")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/api/optimize")
async def optimize_video(file: UploadFile = File(...)):
    # Validar formato de entrada
    if not file.filename.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="El archivo debe ser formato .mp4")
    
    name, ext = os.path.splitext(file.filename)
    
    input_path = UPLOAD_DIR / file.filename
    output_filename = f"{name}.optimized.mp4"
    output_path = UPLOAD_DIR / output_filename

    try:
        # Guardar el archivo subido temporalmente
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Comando FFmpeg con requisitos de calidad e idoneidad para fondo web:
        # -vf "scale='min(1920,iw)':-2": Escala a 1080p máximo si es mayor. Mantiene tamaño si es menor. Alto par obligatorio.
        # -r 30: Fuerza un máximo de 30 FPS para liberar CPU/GPU para scripts y Canvas en el cliente.
        # -b:v 3M -maxrate 4M -bufsize 6M: Tasa de bit controlada (Target 3 Mbps, Max 4 Mbps) para compresión óptima (<15MB).
        # -an: Elimina pistas de audio por completo (Garantiza Autoplay nativo sin bloqueos de navegador y reduce peso).
        ffmpeg_cmd = [
            "ffmpeg", "-y", 
            "-i", str(input_path),
            "-vf", "scale='min(1920,iw)':-2",
            "-r", "30",
            "-vcodec", "libx264",
            "-b:v", "3M",
            "-maxrate", "4M",
            "-bufsize", "6M",
            "-an",
            str(output_path)
        ]

        # Ejecutar la optimización mediante FFmpeg
        process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if process.returncode != 0:
            print(f"Error en FFmpeg: {process.stderr}")
            raise HTTPException(status_code=500, detail="Error al procesar el video con FFmpeg.")

        # Retornar el archivo optimizado listo para descarga
        return FileResponse(
            path=output_path, 
            filename=output_filename, 
            media_type="video/mp4"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Limpieza del archivo original de entrada
        if input_path.exists():
            input_path.unlink()
