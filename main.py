from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, Union
from transformers import (
    pipeline,
    Pipeline,
)
import asyncio

app = FastAPI()

class Parameters(BaseModel):
    task: str
    options: Optional[Dict[str, Any]] = None  # Опции для pipeline

class RequestBody(BaseModel):
    model: str
    inputs: Any  # Для разных задач может быть строка или словарь
    parameters: Parameters

# Кэш для pipeline, чтобы не загружать модель при каждом запросе
pipeline_cache: Dict[str, Pipeline] = {}

async def get_pipeline(task: str, model: str) -> Pipeline:
    key = f"{task}::{model}"
    if key in pipeline_cache:
        return pipeline_cache[key]
    # Загрузка pipeline может быть блокирующей, обернём в поток
    loop = asyncio.get_event_loop()
    pipe = await loop.run_in_executor(None, lambda: pipeline(task=task, model=model))
    pipeline_cache[key] = pipe
    return pipe
@app.get("/")
async def health_check():
    return "Success";

@app.post("/ai-gateway")
async def ai_gateway(
    body: RequestBody,
    authorization: Optional[str] = Header(None)
):
    #if not authorization or not authorization.startswith("Bearer "):
    #    raise HTTPException(status_code=401, detail="Unauthorized")

    task = body.parameters.task
    model = body.model
    inputs = body.inputs
    options = body.parameters.options or {}

    try:
        pipe = await get_pipeline(task, model)
    # except PipelineException as e:
    #     raise HTTPException(status_code=400, detail=f"Failed to load pipeline: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error loading pipeline: {str(e)}")

    try:
        # В зависимости от задачи форматируем вызов
        # Большинство pipeline принимают inputs и **options
        output = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: pipe(inputs, **options)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

    return {"result": output}
