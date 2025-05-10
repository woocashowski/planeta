from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import uuid
import os

app = FastAPI()

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
CHART_DIR = "charts"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Read data with pandas
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Failed to read file: {e}"})

    # Get describe summary
    summary = df.describe(include='all').to_string()

    # Generate heatmap
    plt.figure(figsize=(10, 6))
    sns.heatmap(df.select_dtypes(include='number').corr(), annot=True, cmap="coolwarm")
    chart_id = str(uuid.uuid4()) + ".png"
    chart_path = os.path.join(CHART_DIR, chart_id)
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()

    return {
        "summary": summary,
        "chart_url": f"/chart/{chart_id}"
    }

@app.get("/chart/{filename}")
def get_chart(filename: str):
    chart_path = os.path.join(CHART_DIR, filename)
    if os.path.exists(chart_path):
        return FileResponse(chart_path, media_type="image/png")
    return JSONResponse(status_code=404, content={"error": "Chart not found"})
