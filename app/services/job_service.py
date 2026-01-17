"""
Job Service for Background Research Processing.

Manages asynchronous background jobs for deep research pipeline.
Uses asyncio tasks with database-backed state for persistence.
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from app.services.database_service import get_database_service

logger = logging.getLogger(__name__)


class JobStage(BaseModel):
    """Represents a stage in the research pipeline."""
    name: str
    status: str = "pending"  # pending, running, complete, failed
    progress: int = 0
    label: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class ResearchJob(BaseModel):
    """Represents a background research job."""
    job_id: str
    session_id: str
    product_id: str
    status: str = "pending"  # pending, running, complete, failed
    progress: int = 0
    current_stage: Optional[str] = None
    stages: List[JobStage] = Field(default_factory=list)
    error_message: Optional[str] = None
    result_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    completed_at: Optional[str] = None


class JobService:
    """
    Background job service for research pipeline.

    Manages:
    - Job creation and enqueueing
    - Background task execution via asyncio
    - Progress tracking and status updates
    - Job state persistence to database
    """

    def __init__(self):
        """Initialize job service."""
        self._db = get_database_service()
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._pipeline_callback: Optional[Callable] = None

    def set_pipeline_callback(self, callback: Callable):
        """
        Set the pipeline execution callback.

        Args:
            callback: Async function to execute the research pipeline.
                      Signature: async def callback(job_id: str, session_id: str, product_id: str) -> Dict
        """
        self._pipeline_callback = callback

    async def create_job(
        self,
        session_id: str,
        product_id: str,
        stages: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Create a new research job and start background processing.

        Args:
            session_id: Onboarding session ID
            product_id: Product being researched
            stages: Optional custom stage definitions

        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())

        # Default stages for research pipeline
        default_stages = stages or [
            {"name": "data_ingestion", "status": "pending", "progress": 0, "label": "Data Ingestion"},
            {"name": "competitive_landscape", "status": "pending", "progress": 0, "label": "Competitive Analysis"},
            {"name": "sota_analysis", "status": "pending", "progress": 0, "label": "State of the Art"},
            {"name": "regulatory_analysis", "status": "pending", "progress": 0, "label": "Regulatory Intelligence"},
            {"name": "report_generation", "status": "pending", "progress": 0, "label": "Report Generation"},
        ]

        # Create job in database
        self._db.create_research_job(job_id, session_id, product_id, default_stages)

        logger.info(f"Created research job {job_id} for session {session_id}")

        # Start background task
        task = asyncio.create_task(self._run_pipeline(job_id, session_id, product_id))
        self._running_tasks[job_id] = task

        # Add callback to clean up when done
        task.add_done_callback(lambda t: self._cleanup_task(job_id))

        return job_id

    def _cleanup_task(self, job_id: str):
        """Remove task from running tasks dict."""
        if job_id in self._running_tasks:
            del self._running_tasks[job_id]
            logger.debug(f"Cleaned up task for job {job_id}")

    async def _run_pipeline(
        self,
        job_id: str,
        session_id: str,
        product_id: str,
    ):
        """
        Execute the research pipeline in background.

        Args:
            job_id: Job identifier
            session_id: Onboarding session ID
            product_id: Product being researched
        """
        try:
            logger.info(f"Starting research pipeline for job {job_id}")

            # Update status to running
            await self.update_job_status(job_id, status="running", progress=0, current_stage="data_ingestion")

            # Execute pipeline callback if set
            if self._pipeline_callback:
                result = await self._pipeline_callback(job_id, session_id, product_id)
                if result.get("success"):
                    await self.update_job_status(
                        job_id,
                        status="complete",
                        progress=100,
                        current_stage=None,
                        result_data=result.get("data", {}),
                    )
                else:
                    await self.update_job_status(
                        job_id,
                        status="failed",
                        error_message=result.get("error", "Pipeline failed"),
                    )
            else:
                # Run default pipeline stages
                await self._run_default_pipeline(job_id, session_id, product_id)

        except asyncio.CancelledError:
            logger.warning(f"Job {job_id} was cancelled")
            await self.update_job_status(job_id, status="failed", error_message="Job cancelled")
            raise
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            await self.update_job_status(job_id, status="failed", error_message=str(e))

    async def _run_default_pipeline(
        self,
        job_id: str,
        session_id: str,
        product_id: str,
    ):
        """
        Run the default research pipeline stages.

        This is called if no custom pipeline callback is set.
        """
        # Import here to avoid circular imports
        from app.services.deep_research_service import get_deep_research_service
        from app.services.data_ingestion_service import get_data_ingestion_service
        from app.services.vector_service import get_vector_service
        from app.services.onboarding_service import get_onboarding_service

        onboarding_service = get_onboarding_service()
        deep_research_service = get_deep_research_service()
        data_ingestion_service = get_data_ingestion_service()
        vector_service = get_vector_service()

        # Get session data
        session_data = onboarding_service.get_session_status(session_id)
        if not session_data.get("success"):
            raise ValueError(f"Session {session_id} not found")

        product_info = {
            "product_name": session_data.get("product_name", ""),
            "category": session_data.get("category", ""),
            "indication": session_data.get("indication", ""),
            "protocol_id": session_data.get("protocol_id", ""),
        }

        recommendations = session_data.get("recommendations", {})
        discovery_results = session_data.get("discovery_results", {})

        stages = self.get_job(job_id).get("stages", [])
        result_data = {}

        # Stage 1: Data Ingestion (0-20%)
        await self._update_stage(job_id, "data_ingestion", "running", 0)
        try:
            ingestion_result = await data_ingestion_service.ingest_approved_sources(
                session_id=session_id,
                product_id=product_id,
                recommendations=recommendations,
            )
            result_data["data_ingestion"] = ingestion_result
            await self._update_stage(job_id, "data_ingestion", "complete", 100)
            await self.update_job_status(job_id, progress=20, current_stage="competitive_landscape")
        except Exception as e:
            logger.error(f"Data ingestion failed: {e}")
            await self._update_stage(job_id, "data_ingestion", "failed", 0, str(e))
            # Continue with other stages even if ingestion fails partially

        # Stage 2: Competitive Landscape (20-40%)
        await self._update_stage(job_id, "competitive_landscape", "running", 0)
        try:
            competitive_result = await deep_research_service.research_competitive_landscape(
                product_info=product_info,
                discovery_results=discovery_results,
                recommendations=recommendations,
            )
            result_data["competitive_landscape"] = competitive_result
            await self._update_stage(job_id, "competitive_landscape", "complete", 100)
            await self.update_job_status(job_id, progress=40, current_stage="sota_analysis")
        except Exception as e:
            logger.error(f"Competitive research failed: {e}")
            await self._update_stage(job_id, "competitive_landscape", "failed", 0, str(e))

        # Stage 3: State of the Art (40-60%)
        await self._update_stage(job_id, "sota_analysis", "running", 0)
        try:
            sota_result = await deep_research_service.research_state_of_the_art(
                product_info=product_info,
                discovery_results=discovery_results,
                recommendations=recommendations,
            )
            result_data["sota_analysis"] = sota_result
            await self._update_stage(job_id, "sota_analysis", "complete", 100)
            await self.update_job_status(job_id, progress=60, current_stage="regulatory_analysis")
        except Exception as e:
            logger.error(f"SOTA research failed: {e}")
            await self._update_stage(job_id, "sota_analysis", "failed", 0, str(e))

        # Stage 4: Regulatory Analysis (60-80%)
        await self._update_stage(job_id, "regulatory_analysis", "running", 0)
        try:
            regulatory_result = await deep_research_service.research_regulatory_precedents(
                product_info=product_info,
                discovery_results=discovery_results,
                recommendations=recommendations,
            )
            result_data["regulatory_analysis"] = regulatory_result
            await self._update_stage(job_id, "regulatory_analysis", "complete", 100)
            await self.update_job_status(job_id, progress=80, current_stage="report_generation")
        except Exception as e:
            logger.error(f"Regulatory research failed: {e}")
            await self._update_stage(job_id, "regulatory_analysis", "failed", 0, str(e))

        # Stage 5: Report Generation (80-100%)
        await self._update_stage(job_id, "report_generation", "running", 0)
        try:
            reports_result = await deep_research_service.generate_intelligence_brief(
                product_info=product_info,
                research_results={
                    "competitive_landscape": result_data.get("competitive_landscape", {}),
                    "sota_analysis": result_data.get("sota_analysis", {}),
                    "regulatory_analysis": result_data.get("regulatory_analysis", {}),
                },
            )
            result_data["reports"] = reports_result
            result_data["intelligence_brief"] = reports_result.get("intelligence_brief", {})
            await self._update_stage(job_id, "report_generation", "complete", 100)
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            await self._update_stage(job_id, "report_generation", "failed", 0, str(e))

        # Update onboarding session with results
        try:
            await self._update_session_with_results(session_id, result_data)
        except Exception as e:
            logger.error(f"Failed to update session with results: {e}")

        # Mark job as complete
        await self.update_job_status(
            job_id,
            status="complete",
            progress=100,
            current_stage=None,
            result_data=result_data,
        )

        logger.info(f"Research pipeline completed for job {job_id}")

    async def _update_session_with_results(self, session_id: str, result_data: Dict[str, Any]):
        """Update the onboarding session with research results."""
        from app.services.onboarding_service import get_onboarding_service

        onboarding_service = get_onboarding_service()

        # Load session directly from database
        session = onboarding_service._load_session(session_id)
        if session:
            # Update research reports
            session.research_reports = {
                "competitive_landscape": result_data.get("competitive_landscape", {}),
                "sota_analysis": result_data.get("sota_analysis", {}),
                "regulatory_analysis": result_data.get("regulatory_analysis", {}),
            }
            session.intelligence_brief = result_data.get("intelligence_brief", {})

            # Mark deep research phase as complete
            from app.services.onboarding_service import OnboardingPhase
            session.phase_progress[OnboardingPhase.DEEP_RESEARCH.value] = {
                "completed": True,
                "progress": 100,
            }
            session.current_phase = OnboardingPhase.COMPLETE
            session.completed_at = datetime.utcnow()

            onboarding_service._save_session(session)
            logger.info(f"Updated session {session_id} with research results")

    async def _update_stage(
        self,
        job_id: str,
        stage_name: str,
        status: str,
        progress: int,
        error: Optional[str] = None,
    ):
        """Update a specific stage's status."""
        job = self.get_job(job_id)
        if not job:
            return

        stages = job.get("stages", [])
        now = datetime.utcnow().isoformat()

        for stage in stages:
            if stage["name"] == stage_name:
                stage["status"] = status
                stage["progress"] = progress
                if status == "running" and not stage.get("started_at"):
                    stage["started_at"] = now
                if status in ("complete", "failed"):
                    stage["completed_at"] = now
                if error:
                    stage["error"] = error
                break

        self._db.update_research_job(job_id, stages=stages)

    async def update_job_status(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        current_stage: Optional[str] = None,
        error_message: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update job status and progress.

        Args:
            job_id: Job identifier
            status: New status
            progress: Progress percentage (0-100)
            current_stage: Current stage name
            error_message: Error message if failed
            result_data: Result data when complete

        Returns:
            Success status
        """
        return self._db.update_research_job(
            job_id=job_id,
            status=status,
            progress=progress,
            current_stage=current_stage,
            error_message=error_message,
            result_data=result_data,
        )

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job data or None
        """
        return self._db.get_research_job(job_id)

    def get_job_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent job for a session.

        Args:
            session_id: Onboarding session ID

        Returns:
            Job data or None
        """
        return self._db.get_research_job_by_session(session_id)

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get detailed job status with stage information.

        Args:
            job_id: Job identifier

        Returns:
            Formatted status response
        """
        job = self.get_job(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}

        # Calculate current stage label
        current_stage_label = ""
        for stage in job.get("stages", []):
            if stage["name"] == job.get("current_stage"):
                current_stage_label = stage.get("label", stage["name"])
                break

        return {
            "success": True,
            "job_id": job["job_id"],
            "session_id": job["session_id"],
            "product_id": job["product_id"],
            "status": job["status"],
            "progress": job["progress"],
            "current_stage": job.get("current_stage"),
            "current_stage_label": current_stage_label,
            "stages": job.get("stages", []),
            "error_message": job.get("error_message"),
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at"),
            "completed_at": job.get("completed_at"),
        }

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Job identifier

        Returns:
            Success status
        """
        if job_id in self._running_tasks:
            task = self._running_tasks[job_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            return True

        # Update status in database even if task not found
        return self._db.update_research_job(
            job_id,
            status="failed",
            error_message="Job cancelled by user",
        )

    def is_job_running(self, job_id: str) -> bool:
        """Check if a job is currently running."""
        return job_id in self._running_tasks and not self._running_tasks[job_id].done()


# Singleton instance
_job_service: Optional[JobService] = None


def get_job_service() -> JobService:
    """Get singleton job service instance."""
    global _job_service
    if _job_service is None:
        _job_service = JobService()
    return _job_service
