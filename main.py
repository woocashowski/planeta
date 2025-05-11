from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lepiej ograniczyć do twojej domeny
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
CHART_FOLDER = "charts"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHART_FOLDER, exist_ok=True)

@app.post("/analyze")
async def analyze(request: Request, file: UploadFile = File(...)):
    contents = await file.read()
    filename = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(filename, "wb") as f:
        f.write(contents)

    if file.filename.endswith(".csv"):
        df = pd.read_csv(filename)
    else:
        df = pd.read_excel(filename)

    # Summary statistics jako dict
    summary = df.describe(include='all').fillna("").to_dict()

    # Wykres korelacji
    chart_id = f"{uuid.uuid4()}.png"
    chart_path = os.path.join(CHART_FOLDER, chart_id)

    try:
        sns.set(style="darkgrid")
        plt.figure(figsize=(10, 6))
        sns.heatmap(df.corr(numeric_only=True), annot=True, cmap="coolwarm")
        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close()
    except:
        chart_path = None

    chart_url = str(request.url_for("get_chart", filename=chart_id)) if chart_path else ""

    return {
        "summary": summary,
        "chart_url": chart_url
    }

@app.get("/chart/{filename}")
def get_chart(filename: str):
    return FileResponse(os.path.join(CHART_FOLDER, filename))
