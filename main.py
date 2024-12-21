from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import FileResponse
from spleeter.separator import Separator
import tensorflow as tf
import os
import shutil

app = FastAPI()

@app.post("/process-audio/")
async def process_audio(
    file: UploadFile = File(...),
    stems: int = Query(2, description="Número de pistas a separar (2, 4, 5)"),
    clear_memory: bool = Query(False, description="Liberar memoria después del procesamiento")
):
    if stems not in [2, 4, 5]:
        raise HTTPException(status_code=400, detail="Opción no válida para 'stems'. Solo se permiten 2, 4 o 5.")

    # Configurar el modelo de Spleeter
    model_name = f"spleeter:{stems}stems"
    separator = Separator(model_name)

    # Guardar el archivo subido temporalmente
    input_path = f"temp/{file.filename}"
    output_path = f"output/{os.path.splitext(file.filename)[0]}"
    os.makedirs("temp", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Separar el audio usando Spleeter
    separator.separate_to_file(input_path, output_path)

    # Liberar memoria si el parámetro está activado
    if clear_memory:
        tf.keras.backend.clear_session()
        print("Memoria liberada después del procesamiento")

    # Crear un diccionario con las rutas de las pistas generadas
    tracks = {}
    for root, dirs, files in os.walk(output_path):
        for f in files:
            track_name = os.path.splitext(f)[0]  # Ejemplo: 'vocals', 'drums'
            tracks[track_name] = f"/download/{f}"

    # Eliminar el archivo temporal
    os.remove(input_path)

    return {
        "tracks": tracks,
        "message": f"Audio procesado con {stems} pistas separadas."
    }


@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"output/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Archivo no encontrado")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
