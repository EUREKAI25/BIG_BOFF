# CHANTIER 09 — API BACKEND (FastAPI)

⚠️ **CE PROJET N'UTILISE PAS EUREKAI**

---

## OBJECTIF
Créer l'API REST qui orchestre tout le pipeline de conversion : parsing → analyse → mapping → génération.

## PRÉREQUIS
- C01-C08 (tous les services)

## ENDPOINTS

```
POST /api/convert           # Lance une conversion
GET  /api/status/{job_id}   # Statut d'une conversion
GET  /api/result/{job_id}   # Télécharge le résultat
POST /api/preview/{job_id}  # Génère un preview
GET  /api/health            # Health check
```

---

## STRUCTURE

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py        # Tous les endpoints
│   │   └── dependencies.py  # Injection dépendances
│   ├── core/
│   │   ├── config.py        # Settings
│   │   └── pipeline.py      # Orchestration
│   ├── models/
│   │   └── job.py           # Job model
│   └── services/            # C01-C08
└── requirements.txt
```

---

## MAIN APP

### main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .core.config import settings

app = FastAPI(
    title="Web2App API",
    description="Convertissez n'importe quel site web en app mobile",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router, prefix="/api")

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}
```

---

## ROUTES

### api/routes.py

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional
from ..core.pipeline import ConversionPipeline
from ..models.job import Job, JobStatus
import uuid

router = APIRouter()
pipeline = ConversionPipeline()

# Store des jobs (en prod: Redis/DB)
jobs: dict[str, Job] = {}


class ConvertRequest(BaseModel):
    url: HttpUrl
    options: Optional[dict] = None


class ConvertResponse(BaseModel):
    job_id: str
    status: str
    message: str


@router.post("/convert", response_model=ConvertResponse)
async def convert(request: ConvertRequest, background_tasks: BackgroundTasks):
    """Lance une conversion de site web."""
    
    # Créer un job
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        url=str(request.url),
        status=JobStatus.PENDING,
    )
    jobs[job_id] = job
    
    # Lancer en background
    background_tasks.add_task(pipeline.run, job_id, str(request.url), request.options)
    
    return ConvertResponse(
        job_id=job_id,
        status="pending",
        message="Conversion démarrée"
    )


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """Récupère le statut d'une conversion."""
    
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    return {
        "job_id": job_id,
        "status": job.status.value,
        "progress": job.progress,
        "current_step": job.current_step,
        "error": job.error,
    }


@router.get("/result/{job_id}")
async def get_result(job_id: str):
    """Récupère le résultat d'une conversion."""
    
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(400, f"Job not completed: {job.status.value}")
    
    return {
        "job_id": job_id,
        "download_url": f"/api/download/{job_id}",
        "preview_url": job.preview_url,
        "stats": job.stats,
    }


@router.get("/download/{job_id}")
async def download(job_id: str):
    """Télécharge le projet généré en ZIP."""
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    job = jobs.get(job_id)
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(404, "Project not found")
    
    zip_path = Path(f"./generated/{job_id}.zip")
    if not zip_path.exists():
        raise HTTPException(404, "ZIP file not found")
    
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"web2app_{job_id[:8]}.zip"
    )
```

---

## PIPELINE

### core/pipeline.py

```python
from enum import Enum
from pathlib import Path
import asyncio
import shutil

from ..parser.service import ParserService
from ..analyzer.service import AnalyzerService
from ..mapper.service import MapperService
from ..generator.service import GeneratorService
from ..assets.service import AssetService
from ..navigation.service import NavigationService
from ..preview.service import PreviewService
from ..models.job import Job, JobStatus

# Référence au store (à améliorer)
jobs = {}

class ConversionPipeline:
    def __init__(self):
        self.parser = ParserService()
        self.analyzer = AnalyzerService()
        self.mapper = MapperService()
        self.generator = GeneratorService()
        self.assets = AssetService()
        self.navigation = NavigationService()
        self.preview = PreviewService()
    
    async def run(self, job_id: str, url: str, options: dict = None):
        """Exécute le pipeline complet."""
        job = jobs.get(job_id)
        if not job:
            return
        
        try:
            job.status = JobStatus.RUNNING
            
            # Étape 1: Parser
            job.current_step = "Analyse du site web..."
            job.progress = 10
            parsed = await self.parser.parse_url(url)
            
            # Étape 2: Analyzer
            job.current_step = "Identification des composants..."
            job.progress = 30
            analyzed = await self.analyzer.analyze(parsed)
            
            # Étape 3: Mapper
            job.current_step = "Conversion des styles..."
            job.progress = 50
            mappings = await self.mapper.map_site(parsed, analyzed)
            
            # Étape 4: Assets
            job.current_step = "Téléchargement des assets..."
            job.progress = 60
            output_dir = Path(f"./generated/{job_id}")
            output_dir.mkdir(parents=True, exist_ok=True)
            assets_manifest = await self.assets.process(parsed, output_dir)
            
            # Étape 5: Generator
            job.current_step = "Génération du code..."
            job.progress = 80
            await self.generator.generate(analyzed, mappings, output_dir)
            
            # Étape 6: Navigation
            job.current_step = "Configuration de la navigation..."
            job.progress = 85
            await self.navigation.generate(analyzed, output_dir)
            
            # Étape 7: ZIP
            job.current_step = "Création du package..."
            job.progress = 95
            zip_path = self._create_zip(output_dir)
            
            # Étape 8: Preview (optionnel)
            job.current_step = "Génération du preview..."
            preview_result = await self.preview.create_preview(output_dir)
            job.preview_url = preview_result.get("url")
            
            # Terminé
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.current_step = "Terminé"
            job.stats = {
                "screens": len(analyzed.screens),
                "components": len(analyzed.components),
                "pages_analyzed": len(parsed.pages),
            }
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.current_step = "Erreur"
    
    def _create_zip(self, project_dir: Path) -> Path:
        """Crée un ZIP du projet."""
        zip_path = project_dir.parent / f"{project_dir.name}.zip"
        shutil.make_archive(str(zip_path.with_suffix("")), "zip", project_dir)
        return zip_path
```

---

## JOB MODEL

### models/job.py

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Job:
    id: str
    url: str
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    current_step: str = ""
    error: Optional[str] = None
    preview_url: Optional[str] = None
    stats: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
```

---

## LIVRABLES

```
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── dependencies.py
│   ├── core/
│   │   ├── config.py
│   │   └── pipeline.py
│   └── models/
│       └── job.py
└── requirements.txt
```

## CRITÈRES DE VALIDATION

- [ ] POST /convert lance le pipeline
- [ ] GET /status retourne la progression
- [ ] GET /result retourne le lien de téléchargement
- [ ] GET /download retourne le ZIP
- [ ] Gestion des erreurs propre

## TEMPS ESTIMÉ
4 heures
