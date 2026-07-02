from fastapi import FastAPI

app = FastAPI(
    title="Prism API",
    version=0.1
)

@app.get("/")
def root():
    return {"message": "Prism backend is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}