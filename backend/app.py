"""
UT360 Model Configuration & Pipeline Management API
Backend FastAPI application for configuring weights and running ML pipeline
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import json
import os
import subprocess
import uuid
import sqlite3
from pathlib import Path
import pandas as pd
from functools import lru_cache

# Initialize FastAPI app
app = FastAPI(
    title="UT360 Pipeline Manager",
    description="API for configuring model weights and running the advance recommendation pipeline",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration paths
UT360_BASE_DIR = os.environ.get("UT360_BASE_DIR", "/data/ut360")
BASE_DIR = Path(UT360_BASE_DIR)
CONFIG_DIR = BASE_DIR / "config"
DB_PATH = Path("/data/web-ut360") / "database" / "pipeline.db"

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ========== DATABASE SETUP ==========
def init_db():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Configuration table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configurations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            config_type TEXT NOT NULL,
            config_data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 0
        )
    """)

    # Pipeline execution history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id TEXT PRIMARY KEY,
            config_id TEXT,
            phase TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            error_message TEXT,
            output_path TEXT,
            logs TEXT,
            metrics TEXT,
            FOREIGN KEY (config_id) REFERENCES configurations(id)
        )
    """)

    # Model metrics history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_metrics (
            id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            recorded_at TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES pipeline_runs(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ========== PYDANTIC MODELS ==========
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BadDebtWeights(BaseModel):
    """Bad debt risk calculation weights"""
    topup_advance_ratio_weight: float = Field(40.0, ge=0, le=100, description="Weight for topup/advance ratio (0-100)")
    topup_frequency_weight: float = Field(20.0, ge=0, le=100, description="Weight for topup frequency (0-100)")
    arpu_stability_weight: float = Field(20.0, ge=0, le=100, description="Weight for ARPU stability (0-100)")
    avg_topup_weight: float = Field(20.0, ge=0, le=100, description="Weight for average topup amount (0-100)")
    base_risk_score: float = Field(50.0, ge=0, le=100, description="Base risk score (0-100)")
    low_risk_threshold: float = Field(30.0, ge=0, le=100, description="Threshold for LOW risk (0-100)")
    high_risk_threshold: float = Field(60.0, ge=0, le=100, description="Threshold for HIGH risk (0-100)")


class BusinessRuleWeights(BaseModel):
    """Business rules configuration for service classification"""
    # ungsanluong
    voice_sms_threshold: float = Field(70.0, ge=0, le=100, description="Voice/SMS percentage threshold (%)")
    ungsanluong_arpu_multiplier: float = Field(0.8, ge=0, le=2, description="ARPU multiplier for ungsanluong")
    ungsanluong_min_amount: float = Field(10000, ge=5000, le=50000, description="Min advance amount (VND)")
    ungsanluong_max_amount: float = Field(50000, ge=10000, le=100000, description="Max advance amount (VND)")
    ungsanluong_revenue_rate: float = Field(0.20, ge=0, le=1, description="Revenue rate (0-1)")

    # EasyCredit
    easycredit_min_topup_count_1m: int = Field(1, ge=0, le=10, description="Min topup count last month")
    easycredit_min_topup_amount: float = Field(50000, ge=0, le=200000, description="Min topup amount (VND)")
    easycredit_min_topup_count_2m: int = Field(1, ge=0, le=10, description="Min topup count last 2 months")
    easycredit_vip_arpu_threshold: float = Field(100000, ge=50000, le=500000, description="VIP ARPU threshold (VND)")
    easycredit_default_amount: float = Field(25000, ge=10000, le=50000, description="Default advance amount (VND)")
    easycredit_vip_amount: float = Field(50000, ge=25000, le=100000, description="VIP advance amount (VND)")
    easycredit_revenue_rate: float = Field(0.30, ge=0, le=1, description="Revenue rate (0-1)")

    # MBFG
    mbfg_min_topup_count_1m: int = Field(2, ge=0, le=10, description="Min topup count last month")
    mbfg_arpu_multiplier: float = Field(1.2, ge=0, le=2, description="ARPU multiplier for MBFG")
    mbfg_min_amount: float = Field(10000, ge=5000, le=50000, description="Min advance amount (VND)")
    mbfg_max_amount: float = Field(50000, ge=10000, le=100000, description="Max advance amount (VND)")
    mbfg_revenue_rate: float = Field(0.30, ge=0, le=1, description="Revenue rate (0-1)")


class ClusteringConfig(BaseModel):
    """K-Means clustering configuration"""
    n_clusters: int = Field(3, ge=2, le=10, description="Number of clusters")
    n_init: int = Field(20, ge=1, le=100, description="Number of initializations")
    max_iter: int = Field(500, ge=100, le=2000, description="Maximum iterations")
    random_state: int = Field(42, ge=0, le=1000, description="Random seed")


class ConfigurationCreate(BaseModel):
    """Request model for creating a new configuration"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    config_type: str = Field(..., pattern="^(bad_debt|business_rules|clustering)$")
    config_data: Dict[str, Any]


class ConfigurationResponse(BaseModel):
    """Response model for configuration"""
    id: str
    name: str
    description: Optional[str]
    config_type: str
    config_data: Dict[str, Any]
    created_at: str
    updated_at: str
    is_active: bool


class DataFileSelection(BaseModel):
    """File selection for Phase 1 data loading"""
    n1_files: List[str] = Field(default=[], description="N1 (ARPU) file paths")
    n2_files: List[str] = Field(default=[], description="N2 (Package) file paths")
    n3_files: List[str] = Field(default=[], description="N3 (Usage) file paths")
    n4_files: List[str] = Field(default=[], description="N4 (Advance) file paths")
    n5_files: List[str] = Field(default=[], description="N5 (Topup) file paths")
    n6_files: List[str] = Field(default=[], description="N6 (Usage Detail) file paths")
    n7_files: List[str] = Field(default=[], description="N7 (Location) file paths")
    n8_files: List[str] = Field(default=[], description="N8 (Device) file paths")
    n10_files: List[str] = Field(default=[], description="N10 (Subscriber Info) file paths")


class PipelineRunRequest(BaseModel):
    """Request model for running the pipeline"""
    phases: List[str] = Field(default=["phase1", "phase2", "phase3", "phase4"], description="Phases to run")
    config_id: Optional[str] = Field(None, description="Configuration ID to use (uses active if not specified)")
    use_existing_data: bool = Field(True, description="Use existing intermediate data if available")
    file_selection: Optional[DataFileSelection] = Field(None, description="File selection for Phase 1 (if included)")


class PipelineRunResponse(BaseModel):
    """Response model for pipeline run status"""
    id: str
    config_id: Optional[str]
    phase: str
    status: JobStatus
    started_at: str
    completed_at: Optional[str]
    error_message: Optional[str]
    output_path: Optional[str]
    metrics: Optional[Dict[str, Any]]


# ========== DATABASE HELPERS ==========
def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_configuration(config: ConfigurationCreate) -> str:
    """Save configuration to database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    config_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO configurations (id, name, description, config_type, config_data, created_at, updated_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (config_id, config.name, config.description, config.config_type,
          json.dumps(config.config_data), now, now))

    conn.commit()
    conn.close()

    return config_id


def get_configuration(config_id: str) -> Optional[Dict]:
    """Get configuration by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM configurations WHERE id = ?", (config_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def get_active_configuration(config_type: str) -> Optional[Dict]:
    """Get active configuration by type"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM configurations
        WHERE config_type = ? AND is_active = 1
        ORDER BY updated_at DESC LIMIT 1
    """, (config_type,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def set_active_configuration(config_id: str):
    """Set a configuration as active (deactivate others of same type)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get config type
    cursor.execute("SELECT config_type FROM configurations WHERE id = ?", (config_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Configuration not found")

    config_type = row[0]

    # Deactivate all configs of this type
    cursor.execute("UPDATE configurations SET is_active = 0 WHERE config_type = ?", (config_type,))

    # Activate this config
    cursor.execute("UPDATE configurations SET is_active = 1, updated_at = ? WHERE id = ?",
                   (datetime.now().isoformat(), config_id))

    conn.commit()
    conn.close()


def save_pipeline_run(run_id: str, config_id: Optional[str], phase: str, status: str):
    """Save pipeline run to database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pipeline_runs (id, config_id, phase, status, started_at)
        VALUES (?, ?, ?, ?, ?)
    """, (run_id, config_id, phase, status, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def update_pipeline_run(run_id: str, status: str, error_message: Optional[str] = None,
                        output_path: Optional[str] = None, logs: Optional[str] = None,
                        metrics: Optional[Dict] = None):
    """Update pipeline run status"""
    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()
    metrics_json = json.dumps(metrics) if metrics else None

    cursor.execute("""
        UPDATE pipeline_runs
        SET status = ?, completed_at = ?, error_message = ?, output_path = ?, logs = ?, metrics = ?
        WHERE id = ?
    """, (status, now, error_message, output_path, logs, metrics_json, run_id))

    conn.commit()
    conn.close()


def get_pipeline_run(run_id: str) -> Optional[Dict]:
    """Get pipeline run by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pipeline_runs WHERE id = ?", (run_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


# ========== PIPELINE EXECUTION ==========
def run_phase_script(phase: str, config_id: Optional[str] = None, file_selection: Optional[Dict] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Run a specific phase script
    Returns: (success, logs, output_path)
    """
    phase_scripts = {
        "phase1": "scripts/phase1_data/01_load_master_full.py",
        "phase2": "scripts/phase2_features/feature_engineering.py",
        "phase3a": "scripts/phase3_models/01_clustering_segmentation.py",
        "phase3b": "scripts/phase3_models/03_recommendation_with_correct_arpu.py",
        "phase4": "scripts/phase3_models/04_apply_bad_debt_risk_filter.py",
        "phase5": "scripts/utils/generate_phase_summaries.py"
    }

    if phase not in phase_scripts:
        return False, f"Unknown phase: {phase}", None

    script_path = BASE_DIR / phase_scripts[phase]

    if not script_path.exists():
        return False, f"Script not found: {script_path}", None

    # Build command
    cmd = ["python3", str(script_path)]

    # Add file selection arguments for Phase 1
    if phase == "phase1" and file_selection:
        for folder_num in ['n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'n7', 'n8', 'n10']:
            key = f'{folder_num}_files'
            if file_selection.get(key):
                cmd.extend([f'--{folder_num}'] + file_selection[key])

    # Set environment variables for configuration
    env = os.environ.copy()
    if config_id:
        env["UT360_CONFIG_ID"] = config_id

    try:
        # Run the script
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
            env=env
        )

        logs = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        success = result.returncode == 0

        # Determine output path based on phase
        output_path = None
        if success:
            if phase == "phase1":
                output_path = "output/datasets/master_full_202503-202508.parquet"
            elif phase == "phase2":
                output_path = "output/datasets/dataset_with_features_202503-202508_CORRECTED.parquet"
            elif phase == "phase3b":
                output_path = "output/recommendations/final_recommendations_with_business_rules.csv"
            elif phase == "phase4":
                output_path = "output/recommendations/recommendations_final_filtered_typeupdate.csv"

        return success, logs, output_path

    except subprocess.TimeoutExpired:
        return False, f"Script execution timed out after 1 hour", None
    except Exception as e:
        return False, f"Error executing script: {str(e)}", None


def run_pipeline_background(run_id: str, phases: List[str], config_id: Optional[str], file_selection: Optional[Dict] = None):
    """Background task to run the pipeline"""
    all_logs = []
    all_outputs = []

    for idx, phase in enumerate(phases):
        # Update status with current phase info
        current_phase_info = f"{phase} ({idx+1}/{len(phases)})"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE pipeline_runs
            SET status = ?, phase = ?
            WHERE id = ?
        """, (JobStatus.RUNNING.value, current_phase_info, run_id))
        conn.commit()
        conn.close()

        # Run the phase
        success, logs, output_path = run_phase_script(phase, config_id, file_selection)

        all_logs.append(f"\n{'='*60}\nPHASE: {phase}\n{'='*60}\n{logs}")
        if output_path:
            all_outputs.append(f"{phase}: {output_path}")

        if not success:
            # Update status to failed with all logs
            update_pipeline_run(run_id, JobStatus.FAILED.value,
                              error_message=f"Failed at {phase}",
                              logs="\n".join(all_logs))
            return

    # All phases completed successfully
    final_logs = "\n".join(all_logs)
    final_output = "\n".join(all_outputs)
    update_pipeline_run(run_id, JobStatus.COMPLETED.value,
                       output_path=final_output,
                       logs=final_logs)


# ========== API ENDPOINTS ==========

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "UT360 Pipeline Manager",
        "version": "1.0.0"
    }


@app.post("/api/configurations", response_model=ConfigurationResponse)
async def create_configuration(config: ConfigurationCreate):
    """Create a new configuration"""
    try:
        config_id = save_configuration(config)
        saved_config = get_configuration(config_id)

        return ConfigurationResponse(
            id=saved_config["id"],
            name=saved_config["name"],
            description=saved_config["description"],
            config_type=saved_config["config_type"],
            config_data=json.loads(saved_config["config_data"]),
            created_at=saved_config["created_at"],
            updated_at=saved_config["updated_at"],
            is_active=bool(saved_config["is_active"])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/configurations", response_model=List[ConfigurationResponse])
async def list_configurations(config_type: Optional[str] = None):
    """List all configurations, optionally filtered by type"""
    conn = get_db_connection()
    cursor = conn.cursor()

    if config_type:
        cursor.execute("SELECT * FROM configurations WHERE config_type = ? ORDER BY updated_at DESC", (config_type,))
    else:
        cursor.execute("SELECT * FROM configurations ORDER BY updated_at DESC")

    rows = cursor.fetchall()
    conn.close()

    return [
        ConfigurationResponse(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            config_type=row["config_type"],
            config_data=json.loads(row["config_data"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            is_active=bool(row["is_active"])
        )
        for row in rows
    ]


@app.get("/api/configurations/{config_id}", response_model=ConfigurationResponse)
async def get_configuration_by_id(config_id: str):
    """Get a specific configuration by ID"""
    config = get_configuration(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    return ConfigurationResponse(
        id=config["id"],
        name=config["name"],
        description=config["description"],
        config_type=config["config_type"],
        config_data=json.loads(config["config_data"]),
        created_at=config["created_at"],
        updated_at=config["updated_at"],
        is_active=bool(config["is_active"])
    )


@app.put("/api/configurations/{config_id}", response_model=ConfigurationResponse)
async def update_configuration(config_id: str, config: ConfigurationCreate):
    """Update an existing configuration"""
    existing = get_configuration(config_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Configuration not found")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE configurations
        SET name = ?, description = ?, config_data = ?, updated_at = ?
        WHERE id = ?
    """, (config.name, config.description, json.dumps(config.config_data),
          datetime.now().isoformat(), config_id))

    conn.commit()
    conn.close()

    return await get_configuration_by_id(config_id)


@app.post("/api/configurations/{config_id}/activate")
async def activate_configuration(config_id: str):
    """Set a configuration as active"""
    try:
        set_active_configuration(config_id)
        return {"message": "Configuration activated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/configurations/{config_id}")
async def delete_configuration(config_id: str):
    """Delete a configuration"""
    config = get_configuration(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM configurations WHERE id = ?", (config_id,))
    conn.commit()
    conn.close()

    return {"message": "Configuration deleted successfully"}


@app.post("/api/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline(request: PipelineRunRequest, background_tasks: BackgroundTasks):
    """Run the pipeline with specified phases"""
    run_id = str(uuid.uuid4())

    # Validate phases
    valid_phases = ["phase1", "phase2", "phase3a", "phase3b", "phase4", "phase5"]
    for phase in request.phases:
        if phase not in valid_phases:
            raise HTTPException(status_code=400, detail=f"Invalid phase: {phase}")

    # Get config_id
    config_id = request.config_id
    if not config_id:
        # Use active configuration
        active = get_active_configuration("business_rules")
        config_id = active["id"] if active else None

    # Save initial run record
    save_pipeline_run(run_id, config_id, ",".join(request.phases), JobStatus.PENDING.value)

    # Prepare file selection dict
    file_selection_dict = None
    if request.file_selection:
        file_selection_dict = {
            'n1_files': request.file_selection.n1_files,
            'n10_files': request.file_selection.n10_files,
            'n2_files': request.file_selection.n2_files,
            'n3_files': request.file_selection.n3_files
        }

    # Start background task
    background_tasks.add_task(run_pipeline_background, run_id, request.phases, config_id, file_selection_dict)

    return PipelineRunResponse(
        id=run_id,
        config_id=config_id,
        phase=",".join(request.phases),
        status=JobStatus.PENDING,
        started_at=datetime.now().isoformat(),
        completed_at=None,
        error_message=None,
        output_path=None,
        metrics=None
    )


@app.get("/api/pipeline/runs/{run_id}", response_model=PipelineRunResponse)
async def get_pipeline_run_status(run_id: str):
    """Get pipeline run status"""
    run = get_pipeline_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    metrics = json.loads(run["metrics"]) if run["metrics"] else None

    return PipelineRunResponse(
        id=run["id"],
        config_id=run["config_id"],
        phase=run["phase"],
        status=JobStatus(run["status"]),
        started_at=run["started_at"],
        completed_at=run["completed_at"],
        error_message=run["error_message"],
        output_path=run["output_path"],
        metrics=metrics
    )


@app.get("/api/pipeline/runs", response_model=List[PipelineRunResponse])
async def list_pipeline_runs(limit: int = 50):
    """List recent pipeline runs"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()

    return [
        PipelineRunResponse(
            id=row["id"],
            config_id=row["config_id"],
            phase=row["phase"],
            status=JobStatus(row["status"]),
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            error_message=row["error_message"],
            output_path=row["output_path"],
            metrics=json.loads(row["metrics"]) if row["metrics"] else None
        )
        for row in rows
    ]


@app.get("/api/pipeline/runs/{run_id}/logs")
async def get_pipeline_logs(run_id: str):
    """Get logs for a pipeline run"""
    run = get_pipeline_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    return {
        "run_id": run_id,
        "logs": run["logs"] or "No logs available"
    }


@app.get("/api/data/files")
async def list_data_files(folder: Optional[str] = None):
    """List available CSV files in data folders. If folder not specified, lists all folders."""
    try:
        import glob
        import re

        all_folders = ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8", "N10"]

        # If specific folder requested
        if folder:
            if folder not in all_folders:
                raise HTTPException(status_code=400, detail=f"Invalid folder. Must be one of: {all_folders}")

            folder_path = BASE_DIR / "data" / folder
            if not folder_path.exists():
                return {"folder": folder, "files": [], "message": f"Folder not found: {folder_path}"}

            # Get all CSV files
            pattern = str(folder_path / f"{folder}_*.csv")
            files = sorted(glob.glob(pattern))

            file_info = []
            for file_path in files:
                p = Path(file_path)
                size_mb = p.stat().st_size / (1024 * 1024)
                match = re.search(r'(\d{6})', p.name)
                month = match.group(1) if match else "unknown"

                file_info.append({
                    "path": file_path,
                    "name": p.name,
                    "month": month,
                    "size_mb": round(size_mb, 2),
                    "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat()
                })

            return {
                "folder": folder,
                "folder_path": str(folder_path),
                "files": file_info,
                "count": len(file_info)
            }

        # List all folders with their files
        result = {}
        for folder_name in all_folders:
            folder_path = BASE_DIR / "data" / folder_name
            if not folder_path.exists():
                result[folder_name] = {"exists": False, "files": [], "count": 0}
                continue

            pattern = str(folder_path / f"{folder_name}_*.csv")
            files = sorted(glob.glob(pattern))

            file_info = []
            for file_path in files:
                p = Path(file_path)
                size_mb = p.stat().st_size / (1024 * 1024)
                match = re.search(r'(\d{6})', p.name)
                month = match.group(1) if match else "unknown"

                file_info.append({
                    "path": file_path,
                    "name": p.name,
                    "month": month,
                    "size_mb": round(size_mb, 2),
                    "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat()
                })

            result[folder_name] = {
                "exists": True,
                "folder_path": str(folder_path),
                "files": file_info,
                "count": len(file_info)
            }

        return {"folders": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system/status")
async def get_system_status():
    """Get system status and statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Count configurations
    cursor.execute("SELECT config_type, COUNT(*) as count FROM configurations GROUP BY config_type")
    config_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # Count pipeline runs by status
    cursor.execute("SELECT status, COUNT(*) as count FROM pipeline_runs GROUP BY status")
    run_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # Get latest successful run
    cursor.execute("""
        SELECT * FROM pipeline_runs
        WHERE status = 'completed'
        ORDER BY completed_at DESC LIMIT 1
    """)
    latest_run = cursor.fetchone()

    conn.close()

    return {
        "configurations": config_counts,
        "pipeline_runs": run_counts,
        "latest_successful_run": dict(latest_run) if latest_run else None,
        "database_path": str(DB_PATH),
        "base_directory": str(BASE_DIR)
    }


@app.get("/api/results/phase1")
async def get_phase1_results():
    """Get Phase 1 (Data Loading) results and statistics"""
    try:
        # Try to load from cache first
        summary_file = BASE_DIR / "output/summaries/phase1_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                return json.load(f)

        # Fallback: generate on-the-fly (slow)
        master_file = BASE_DIR / "output/datasets/master_full_202503-202508.parquet"
        if not master_file.exists():
            raise HTTPException(status_code=404, detail="Phase 1 output file not found. Please run Phase 5 to generate summaries.")

        raise HTTPException(status_code=503, detail="Summary not available. Please run Phase 5 (Generate Summaries) first.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results/phase2")
async def get_phase2_results():
    """Get Phase 2 (Feature Engineering) results"""
    try:
        summary_file = BASE_DIR / "output/summaries/phase2_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                return json.load(f)
        raise HTTPException(status_code=503, detail="Summary not available. Please run Phase 5 (Generate Summaries) first.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results/phase3a")
async def get_phase3a_results():
    """Get Phase 3A (Clustering) results"""
    try:
        summary_file = BASE_DIR / "output/summaries/phase3a_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                return json.load(f)
        raise HTTPException(status_code=503, detail="Summary not available. Please run Phase 5 (Generate Summaries) first.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results/phase3b")
async def get_phase3b_results():
    """Get Phase 3B (Business Rules) results"""
    try:
        summary_file = BASE_DIR / "output/summaries/phase3b_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                return json.load(f)
        raise HTTPException(status_code=503, detail="Summary not available. Please run Phase 5 (Generate Summaries) first.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results/phase4")
async def get_phase4_results():
    """Get Phase 4 (Bad Debt Filter) results"""
    try:
        summary_file = BASE_DIR / "output/summaries/phase4_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                return json.load(f)
        raise HTTPException(status_code=503, detail="Summary not available. Please run Phase 5 (Generate Summaries) first.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== SUBSCRIBERS ENDPOINTS ==========

# Cache for fast lookup
_monthly_summary_cache = None
_profile_360_cache = None

def get_monthly_summary_df():
    """Load monthly summary with caching"""
    global _monthly_summary_cache
    if _monthly_summary_cache is None:
        summary_file = BASE_DIR / "output/subscriber_monthly_summary.parquet"
        if summary_file.exists():
            _monthly_summary_cache = pd.read_parquet(summary_file)
        else:
            _monthly_summary_cache = pd.DataFrame()
    return _monthly_summary_cache

def get_profile_360_df():
    """Load 360 profile with caching"""
    global _profile_360_cache
    if _profile_360_cache is None:
        profile_file = BASE_DIR / "output/subscriber_360_profile.parquet"
        if profile_file.exists():
            _profile_360_cache = pd.read_parquet(profile_file)
        else:
            _profile_360_cache = pd.DataFrame()
    return _profile_360_cache

def get_subscriber_monthly_data(isdn: str):
    """Get monthly data for a specific subscriber"""
    try:
        df_monthly = get_monthly_summary_df()
        if len(df_monthly) == 0:
            return []

        subscriber_monthly = df_monthly[df_monthly['isdn'] == isdn]

        if len(subscriber_monthly) > 0:
            # Sort by month
            subscriber_monthly = subscriber_monthly.sort_values('data_month')
            return subscriber_monthly.to_dict('records')
        return []
    except Exception as e:
        print(f"Warning: Could not load monthly data: {e}")
        return []

@app.get("/api/subscribers/list")
async def get_subscribers_list(
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    service_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    search: Optional[str] = None
):
    """Get list of subscribers from final filtered recommendations with search support"""
    try:
        recommendations_file = BASE_DIR / "output/recommendations/recommendations_final_filtered_typeupdate.csv"

        if not recommendations_file.exists():
            raise HTTPException(
                status_code=404,
                detail="Recommendations file not found. Please run the pipeline first."
            )

        # Read CSV with pandas
        df = pd.read_csv(recommendations_file)

        # Apply search filter (search in ISDN column)
        if search and search.strip():
            df = df[df['isdn'].astype(str).str.contains(search.strip(), case=False, na=False)]

        # Apply service type filter
        if service_type and service_type != 'all':
            df = df[df['service_type'] == service_type]

        # Apply risk level filter
        if risk_level and risk_level != 'all':
            df = df[df['bad_debt_risk'] == risk_level]

        # Get total count after filters but before pagination
        total_count = len(df)

        # Apply pagination
        df_paginated = df.iloc[offset:offset+limit]

        # Convert to dict
        subscribers = df_paginated.to_dict('records')

        return {
            "subscribers": subscribers,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading subscribers: {str(e)}")


@app.get("/api/subscribers/detail/{isdn}")
async def get_subscriber_detail(isdn: str):
    """Get detailed information for a specific subscriber"""
    try:
        recommendations_file = BASE_DIR / "output/recommendations/recommendations_final_filtered_typeupdate.csv"

        if not recommendations_file.exists():
            raise HTTPException(
                status_code=404,
                detail="Recommendations file not found. Please run the pipeline first."
            )

        # Read CSV
        df = pd.read_csv(recommendations_file)

        # Find subscriber
        subscriber_df = df[df['isdn'] == isdn]

        if len(subscriber_df) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Subscriber {isdn} not found in recommendations"
            )

        # Convert to dict
        subscriber = subscriber_df.iloc[0].to_dict()

        return subscriber

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading subscriber detail: {str(e)}")


@app.get("/api/subscribers/profile")
async def get_subscriber_profile(isdn: str):
    """Get complete 360 profile for a specific subscriber"""
    try:
        # Load 360 profile from cache
        df_profile = get_profile_360_df()

        if len(df_profile) == 0:
            raise HTTPException(
                status_code=404,
                detail="360 profile file not found. Please run generate_subscriber_360_profile script."
            )

        # Find subscriber
        subscriber_profile = df_profile[df_profile['isdn'] == isdn]

        if len(subscriber_profile) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Subscriber {isdn} not found in 360 profile"
            )

        # Get profile data
        profile_data = subscriber_profile.iloc[0].to_dict()

        # Get monthly ARPU trend data
        monthly_data = get_subscriber_monthly_data(isdn)

        return {
            "profile": profile_data,
            "monthly_arpu": monthly_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading 360 profile: {str(e)}")


@app.get("/api/subscribers/stats")
async def get_subscribers_stats():
    """Get statistics about subscribers"""
    try:
        recommendations_file = BASE_DIR / "output/recommendations/recommendations_final_filtered_typeupdate.csv"

        if not recommendations_file.exists():
            raise HTTPException(
                status_code=404,
                detail="Recommendations file not found. Please run the pipeline first."
            )

        df = pd.read_csv(recommendations_file)

        stats = {
            "total_subscribers": len(df),
            "by_service_type": df['service_type'].value_counts().to_dict(),
            "by_risk_level": df['bad_debt_risk'].value_counts().to_dict(),
            "total_advance_amount": float(df['advance_amount'].sum()),
            "total_revenue": float(df['revenue_per_advance'].sum()),
            "avg_advance_amount": float(df['advance_amount'].mean()),
            "avg_revenue": float(df['revenue_per_advance'].mean()),
            "avg_arpu": float(df['arpu'].mean())
        }

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
