from fastapi import FastAPI, APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController
import aiofiles
from models import ResponseSignal
import logging

logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1","data"],
)

@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, file: UploadFile,app_settings: Settings=Depends(get_settings)):

    # validate the file properties
    is_valid, result_signal = DataController().validate_uploaded_file(file=file)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal,
                "Validation":is_valid
            }
        )
    
    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = DataController().generate_unique_filename(
        orig_file_name= file.filename,
        project_id=project_id
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunck := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunck)
    
    except Exception as e:

        logger.error(f"Error while uploading file: {e}")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "Signal": ResponseSignal.FILE_UPLOAD_FAILED.value,
            }
        )
    return JSONResponse(
        content={
            "Signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id":file_id
        }
    )