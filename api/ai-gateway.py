from fastapi import FastAPI

app = FastAPI()

@app.post("/")
async def handler():
    return {"message": "ok"}
