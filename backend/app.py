from fastapi import FastAPI

app = FastAPI(
    title="OPRD Insight API",
    description="AI Literature Discovery Platform",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "project": "OPRD Insight",
        "status": "running",
        "version": "1.0.0"
    }