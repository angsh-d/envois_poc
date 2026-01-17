"""
Database Service for Clinical Intelligence Platform.

Provides SQLite persistence for onboarding sessions and other application data.
"""
import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Database file location
DB_PATH = Path(os.getenv("DATABASE_PATH", "data/cip_sessions.db"))


class DatabaseService:
    """
    SQLite database service for session persistence.

    Tables:
    - onboarding_sessions: Product onboarding session data
    - conversation_history: Chat conversation history
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database service."""
        self.db_path = db_path or DB_PATH
        self._ensure_db_directory()
        self._init_database()

    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Onboarding sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS onboarding_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT DEFAULT NULL,
                    product_name TEXT NOT NULL,
                    category TEXT DEFAULT '',
                    indication TEXT DEFAULT '',
                    study_phase TEXT DEFAULT '',
                    protocol_id TEXT NOT NULL,
                    technologies TEXT DEFAULT '[]',
                    current_phase TEXT DEFAULT 'context_capture',
                    phase_progress TEXT DEFAULT '{}',
                    discovery_results TEXT DEFAULT '{}',
                    recommendations TEXT DEFAULT '{}',
                    research_reports TEXT DEFAULT '{}',
                    intelligence_brief TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)

            # Add user_id column if it doesn't exist (migration for existing DBs)
            try:
                cursor.execute("ALTER TABLE onboarding_sessions ADD COLUMN user_id TEXT DEFAULT NULL")
            except sqlite3.OperationalError:
                pass  # Column already exists

            # Create index for faster user-based lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id
                ON onboarding_sessions(user_id)
            """)

            # Conversation history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES onboarding_sessions(session_id)
                )
            """)

            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_session
                ON conversation_history(session_id)
            """)

            # Research jobs table for background processing
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_jobs (
                    job_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    current_stage TEXT,
                    stages TEXT DEFAULT '[]',
                    error_message TEXT,
                    result_data TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES onboarding_sessions(session_id)
                )
            """)

            # Create indexes for research jobs
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_research_jobs_session
                ON research_jobs(session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_research_jobs_status
                ON research_jobs(status)
            """)

            logger.info(f"Database initialized at {self.db_path}")

    # ==================== Onboarding Session Methods ====================

    def save_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Save or update an onboarding session.

        Args:
            session_data: Session data dictionary

        Returns:
            Success status
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Serialize complex fields to JSON
            session_id = session_data.get("session_id")
            user_id = session_data.get("user_id")
            technologies = json.dumps(session_data.get("technologies", []))
            phase_progress = json.dumps(session_data.get("phase_progress", {}))
            discovery_results = json.dumps(session_data.get("discovery_results", {}))
            recommendations = json.dumps(session_data.get("recommendations", {}))
            research_reports = json.dumps(session_data.get("research_reports", {}))
            intelligence_brief = json.dumps(session_data.get("intelligence_brief", {}))

            cursor.execute("""
                INSERT OR REPLACE INTO onboarding_sessions (
                    session_id, user_id, product_name, category, indication, study_phase,
                    protocol_id, technologies, current_phase, phase_progress,
                    discovery_results, recommendations, research_reports,
                    intelligence_brief, created_at, updated_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                user_id,
                session_data.get("product_name", ""),
                session_data.get("category", ""),
                session_data.get("indication", ""),
                session_data.get("study_phase", ""),
                session_data.get("protocol_id", ""),
                technologies,
                session_data.get("current_phase", "context_capture"),
                phase_progress,
                discovery_results,
                recommendations,
                research_reports,
                intelligence_brief,
                session_data.get("created_at", datetime.utcnow().isoformat()),
                datetime.utcnow().isoformat(),
                session_data.get("completed_at"),
            ))

            logger.debug(f"Saved session {session_id}")
            return True

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an onboarding session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM onboarding_sessions WHERE session_id = ?
            """, (session_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_session(row)

    def _row_to_session(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert database row to session dictionary."""
        # Handle both old (without user_id) and new schema
        row_dict = dict(row)
        return {
            "session_id": row_dict["session_id"],
            "user_id": row_dict.get("user_id"),
            "product_name": row_dict["product_name"],
            "category": row_dict["category"],
            "indication": row_dict["indication"],
            "study_phase": row_dict["study_phase"],
            "protocol_id": row_dict["protocol_id"],
            "technologies": json.loads(row_dict["technologies"] or "[]"),
            "current_phase": row_dict["current_phase"],
            "phase_progress": json.loads(row_dict["phase_progress"] or "{}"),
            "discovery_results": json.loads(row_dict["discovery_results"] or "{}"),
            "recommendations": json.loads(row_dict["recommendations"] or "{}"),
            "research_reports": json.loads(row_dict["research_reports"] or "{}"),
            "intelligence_brief": json.loads(row_dict["intelligence_brief"] or "{}"),
            "created_at": row_dict["created_at"],
            "updated_at": row_dict["updated_at"],
            "completed_at": row_dict["completed_at"],
        }

    def verify_session_ownership(self, session_id: str, user_id: str) -> bool:
        """
        Verify that a session belongs to a specific user.

        Args:
            session_id: Session identifier
            user_id: User identifier to check ownership

        Returns:
            True if user owns the session, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id FROM onboarding_sessions WHERE session_id = ?
            """, (session_id,))

            row = cursor.fetchone()
            if not row:
                return False

            session_user_id = row["user_id"]

            # If session has no user_id, allow access (legacy sessions)
            if session_user_id is None:
                return True

            return session_user_id == user_id

    def list_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all onboarding sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session summaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, product_name, current_phase,
                       created_at, completed_at
                FROM onboarding_sessions
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit,))

            return [
                {
                    "session_id": row["session_id"],
                    "product_name": row["product_name"],
                    "current_phase": row["current_phase"],
                    "created_at": row["created_at"],
                    "completed_at": row["completed_at"],
                }
                for row in cursor.fetchall()
            ]

    def delete_session(self, session_id: str) -> bool:
        """
        Delete an onboarding session.

        Args:
            session_id: Session identifier

        Returns:
            Success status
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Delete conversation history first
            cursor.execute("""
                DELETE FROM conversation_history WHERE session_id = ?
            """, (session_id,))

            # Delete session
            cursor.execute("""
                DELETE FROM onboarding_sessions WHERE session_id = ?
            """, (session_id,))

            return cursor.rowcount > 0

    # ==================== Conversation History Methods ====================

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add a message to conversation history.

        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata

        Returns:
            Message ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversation_history (session_id, role, content, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                session_id,
                role,
                content,
                json.dumps(metadata or {}),
            ))

            return cursor.lastrowid

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages

        Returns:
            List of messages
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, role, content, metadata, created_at
                FROM conversation_history
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ?
            """, (session_id, limit))

            return [
                {
                    "id": row["id"],
                    "role": row["role"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"] or "{}"),
                    "created_at": row["created_at"],
                }
                for row in cursor.fetchall()
            ]


    # ==================== Research Job Methods ====================

    def create_research_job(
        self,
        job_id: str,
        session_id: str,
        product_id: str,
        stages: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Create a new research job.

        Args:
            job_id: Unique job identifier
            session_id: Associated onboarding session ID
            product_id: Product being researched
            stages: Initial stage definitions

        Returns:
            Success status
        """
        default_stages = stages or [
            {"name": "data_ingestion", "status": "pending", "progress": 0, "label": "Data Ingestion"},
            {"name": "competitive_landscape", "status": "pending", "progress": 0, "label": "Competitive Analysis"},
            {"name": "sota_analysis", "status": "pending", "progress": 0, "label": "State of the Art"},
            {"name": "regulatory_analysis", "status": "pending", "progress": 0, "label": "Regulatory Intelligence"},
            {"name": "report_generation", "status": "pending", "progress": 0, "label": "Report Generation"},
        ]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO research_jobs (
                    job_id, session_id, product_id, status, progress,
                    current_stage, stages, created_at
                ) VALUES (?, ?, ?, 'pending', 0, 'data_ingestion', ?, ?)
            """, (
                job_id,
                session_id,
                product_id,
                json.dumps(default_stages),
                datetime.utcnow().isoformat(),
            ))
            logger.debug(f"Created research job {job_id} for session {session_id}")
            return True

    def update_research_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        current_stage: Optional[str] = None,
        stages: Optional[List[Dict[str, Any]]] = None,
        error_message: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a research job's status and progress.

        Args:
            job_id: Job identifier
            status: New status (pending, running, ingesting, researching, generating, complete, failed)
            progress: Overall progress percentage (0-100)
            current_stage: Name of current stage being processed
            stages: Updated stage list with individual progress
            error_message: Error message if failed
            result_data: Result data when complete

        Returns:
            Success status
        """
        updates = []
        params = []

        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if progress is not None:
            updates.append("progress = ?")
            params.append(progress)
        if current_stage is not None:
            updates.append("current_stage = ?")
            params.append(current_stage)
        if stages is not None:
            updates.append("stages = ?")
            params.append(json.dumps(stages))
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)
        if result_data is not None:
            updates.append("result_data = ?")
            params.append(json.dumps(result_data))

        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())

        if status == "complete":
            updates.append("completed_at = ?")
            params.append(datetime.utcnow().isoformat())

        params.append(job_id)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE research_jobs
                SET {', '.join(updates)}
                WHERE job_id = ?
            """, params)
            return cursor.rowcount > 0

    def get_research_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a research job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job data or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM research_jobs WHERE job_id = ?
            """, (job_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_job(row)

    def get_research_job_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent research job for a session.

        Args:
            session_id: Onboarding session ID

        Returns:
            Job data or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM research_jobs
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (session_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_job(row)

    def _row_to_job(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert database row to job dictionary."""
        row_dict = dict(row)
        return {
            "job_id": row_dict["job_id"],
            "session_id": row_dict["session_id"],
            "product_id": row_dict["product_id"],
            "status": row_dict["status"],
            "progress": row_dict["progress"],
            "current_stage": row_dict["current_stage"],
            "stages": json.loads(row_dict["stages"] or "[]"),
            "error_message": row_dict.get("error_message"),
            "result_data": json.loads(row_dict["result_data"] or "{}"),
            "created_at": row_dict["created_at"],
            "updated_at": row_dict["updated_at"],
            "completed_at": row_dict.get("completed_at"),
        }

    def list_pending_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List pending research jobs.

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of pending jobs
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM research_jobs
                WHERE status IN ('pending', 'running')
                ORDER BY created_at ASC
                LIMIT ?
            """, (limit,))

            return [self._row_to_job(row) for row in cursor.fetchall()]


# Singleton pattern
_db_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get singleton database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
