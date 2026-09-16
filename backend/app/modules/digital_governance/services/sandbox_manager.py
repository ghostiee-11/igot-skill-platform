"""Cybersecurity Sandbox Session Manager & CTFd Evaluation Bridge (SQLAlchemy Persisted).

Manages isolated Marimo notebook instances, dynamically allocated ephemeral ports,
live session TTLs, flag submission verification, locked hint deductions, and
competency matrix accounting stored directly in the SQLAlchemy database.
"""

import os
import sys
import uuid
import json
import base64
import shutil
import socket
import logging
import asyncio
import datetime
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.modules.digital_governance.models import (
    CyberSandboxChallenge,
    CyberSandboxSession,
    UserCyberCompetency,
)
from app.modules.digital_governance.schemas import (
    SandboxChallengeSummary,
    SandboxSessionResponse,
    SandboxFlagSubmitResponse,
    SandboxHintUnlockResponse,
    UserCompetencyRadar,
)
from app.modules.digital_governance.services.content_pipeline import content_pipeline

logger = logging.getLogger("digital_governance.sandbox")

REPO_ROOT = Path(__file__).resolve().parents[5]
SCRATCH_BASE_DIR = Path(tempfile.gettempdir()) / "karmayogi_sandboxes"


class ActiveSession:
    def __init__(
        self,
        session_id: str,
        challenge_id: str,
        title: str,
        category: str,
        difficulty: str,
        base_points: int,
        flag: str,
        hints: List[Dict[str, Any]],
        objectives: List[str],
        scenario_md: str,
        competency_id: str,
        assigned_port: int,
        scratch_dir: Path,
        duration_minutes: int = 45,
        process: Optional[subprocess.Popen] = None,
    ):
        self.session_id = session_id
        self.challenge_id = challenge_id
        self.title = title
        self.category = category
        self.difficulty = difficulty
        self.base_points = base_points
        self.flag = flag.strip()
        self.hints = hints
        self.objectives = objectives
        self.scenario_md = scenario_md
        self.competency_id = competency_id
        self.assigned_port = assigned_port
        self.scratch_dir = scratch_dir
        self.created_at = datetime.datetime.now(datetime.timezone.utc)
        self.expires_at = self.created_at + datetime.timedelta(minutes=duration_minutes)
        self.process = process
        self.log_file = None
        self.status = "running"
        self.unlocked_hint_ids: List[int] = []
        self.total_penalties = 0
        self.is_solved = False
        self.solved_at: Optional[datetime.datetime] = None

    @property
    def remaining_seconds(self) -> int:
        now = datetime.datetime.now(datetime.timezone.utc)
        delta = (self.expires_at - now).total_seconds()
        return max(0, int(delta))

    @property
    def current_points(self) -> int:
        return max(10, self.base_points - self.total_penalties)


class SandboxManager:
    """Manages active sandbox sessions, catalog metadata, flag scoring, and process lifecycle."""

    def __init__(self):
        self._sessions: Dict[str, ActiveSession] = {}
        self._user_competencies: Dict[str, UserCompetencyRadar] = {}
        self._generated_challenges: Dict[str, Dict[str, Any]] = {}
        SCRATCH_BASE_DIR.mkdir(parents=True, exist_ok=True)

    def _find_available_port(self, start_port: int = 8085, end_port: int = 8999) -> int:
        """Find an open TCP port on 127.0.0.1."""
        used_ports = {s.assigned_port for s in self._sessions.values() if s.status == "running"}
        for port in range(start_port, end_port):
            if port in used_ports:
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("127.0.0.1", port)) != 0:
                    return port
        return 8088

    @staticmethod
    def _is_port_listening(port: int) -> bool:
        """Return whether a local service has bound the assigned sandbox port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            return sock.connect_ex(("127.0.0.1", port)) == 0

    def list_challenges(self, db: Optional[Session] = None) -> List[SandboxChallengeSummary]:
        """Returns catalog of challenges directly from the SQLAlchemy database."""
        items: List[SandboxChallengeSummary] = []

        if db is not None:
            try:
                db_challenges = db.query(CyberSandboxChallenge).order_by(CyberSandboxChallenge.id.asc()).all()
                for c in db_challenges:
                    tags = json.loads(c.tags_json) if c.tags_json else []
                    mitre = json.loads(c.mitre_techniques_json) if c.mitre_techniques_json else []
                    objectives = json.loads(c.objectives_json) if c.objectives_json else []
                    items.append(
                        SandboxChallengeSummary(
                            id=c.id,
                            title=c.title,
                            category=c.category,
                            difficulty=c.difficulty,
                            points=c.points,
                            duration_minutes=c.duration_minutes,
                            is_flagship=c.is_flagship,
                            solved=any(s.is_solved for s in self._sessions.values() if s.challenge_id == c.id),
                            competency_id=c.competency_id,
                            tags=tags,
                            mitre_techniques=mitre,
                            objectives=objectives,
                        )
                    )
            except Exception as e:
                logger.warning(f"Error reading challenges from DB: {e}")

        # Add dynamically generated challenges registered in runtime memory
        for cid, gen in self._generated_challenges.items():
            if not any(item.id == cid for item in items):
                items.append(
                    SandboxChallengeSummary(
                        id=cid,
                        title=gen.get("title", cid),
                        category=gen.get("category", "Procedural CTF"),
                        difficulty=gen.get("difficulty", "Intermediate"),
                        points=gen.get("points", 120),
                        duration_minutes=45,
                        is_flagship=False,
                        solved=any(s.is_solved for s in self._sessions.values() if s.challenge_id == cid),
                        competency_id="procedural_investigation",
                        tags=gen.get("tags", []),
                        mitre_techniques=gen.get("mitre_techniques", []),
                        objectives=gen.get("objectives", []),
                    )
                )

        return items

    async def generate_from_transcript(
        self, transcript_text: str, student_id: str = "officer_1", db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Runs the Content Generation Pipeline on a video transcript and registers the challenge in DB."""
        gen_dir = SCRATCH_BASE_DIR / "generated"
        res = await content_pipeline.generate_challenge_package(
            transcript_text=transcript_text,
            output_dir=gen_dir,
            student_id=student_id,
        )
        self._generated_challenges[res["challenge_id"]] = res

        # If DB session provided, save to cyber_sandbox_challenges table
        if db is not None:
            try:
                cid = res["challenge_id"]
                existing = db.query(CyberSandboxChallenge).filter_by(id=cid).first()
                if not existing:
                    pkg_path = Path(res["package_path"])
                    artifacts: Dict[str, str] = {}
                    data_dir = pkg_path / "data"
                    if data_dir.exists():
                        for f in data_dir.iterdir():
                            if f.is_file():
                                try:
                                    artifacts[f.name] = f.read_text(encoding="utf-8")
                                except UnicodeDecodeError:
                                    artifacts[f.name] = "base64:" + base64.b64encode(f.read_bytes()).decode("ascii")

                    nb_path = pkg_path / "marimo" / "challenge.py"
                    nb_code = nb_path.read_text(encoding="utf-8") if nb_path.exists() else ""

                    chal_obj = CyberSandboxChallenge(
                        id=cid,
                        title=res["title"],
                        category=res["category"],
                        difficulty=res["difficulty"],
                        points=res["points"],
                        duration_minutes=45,
                        competency_id=res.get("competency_id", "procedural_investigation"),
                        is_flagship=False,
                        tags_json=json.dumps(res.get("extracted_meta", {}).get("tags", [])),
                        mitre_techniques_json=json.dumps(res.get("extracted_meta", {}).get("mitre_techniques", [])),
                        objectives_json=json.dumps(res.get("objectives", [])),
                        scenario_markdown=res.get("scenario_md", ""),
                        flag=res.get("flag", "FLAG{procedural_ctf}"),
                        hints_json=json.dumps(res.get("hints", [])),
                        artifacts_json=json.dumps(artifacts),
                        notebook_code=nb_code,
                    )
                    db.add(chal_obj)
                    db.commit()
            except Exception as e:
                logger.warning(f"Failed to persist generated challenge to database: {e}")

        return res

    async def start_session(
        self,
        challenge_id: str,
        duration_minutes: int = 45,
        db: Optional[Session] = None,
        user_id: Optional[int] = None,
    ) -> SandboxSessionResponse:
        """Launches an isolated Marimo instance, materializing artifacts and notebook from the database."""
        session_id = f"sess_{uuid.uuid4().hex[:10]}"
        assigned_port = self._find_available_port()
        scratch_dir = SCRATCH_BASE_DIR / session_id
        scratch_dir.mkdir(parents=True, exist_ok=True)
        (scratch_dir / "data").mkdir(parents=True, exist_ok=True)
        (scratch_dir / "marimo").mkdir(parents=True, exist_ok=True)

        title = "Cyber Incident Sandbox"
        category = "SOC Investigation"
        difficulty = "Beginner"
        points = 100
        flag = "FLAG{test_defense_2026}"
        hints: List[Dict[str, Any]] = []
        objectives: List[str] = []
        scenario_md = "Analyze telemetry and solve the crisis."
        competency_id = "soc_investigation"
        artifacts_dict: Dict[str, str] = {}
        notebook_code = ""

        # 1. Query challenge from database
        db_chal = None
        if db is not None:
            db_chal = db.query(CyberSandboxChallenge).filter_by(id=challenge_id).first()

        if db_chal:
            title = db_chal.title
            category = db_chal.category
            difficulty = db_chal.difficulty
            points = db_chal.points
            duration_minutes = db_chal.duration_minutes or duration_minutes
            flag = db_chal.flag
            hints = json.loads(db_chal.hints_json) if db_chal.hints_json else []
            objectives = json.loads(db_chal.objectives_json) if db_chal.objectives_json else []
            scenario_md = db_chal.scenario_markdown
            competency_id = db_chal.competency_id
            artifacts_dict = json.loads(db_chal.artifacts_json) if db_chal.artifacts_json else {}
            notebook_code = db_chal.notebook_code or ""
        elif challenge_id in self._generated_challenges:
            gen_info = self._generated_challenges[challenge_id]
            title = gen_info.get("title", title)
            category = gen_info.get("category", category)
            difficulty = gen_info.get("difficulty", difficulty)
            points = gen_info.get("points", points)
            flag = gen_info.get("flag", flag)
            hints = gen_info.get("hints", [])
            objectives = gen_info.get("objectives", [])
            scenario_md = gen_info.get("scenario_md", scenario_md)
            competency_id = gen_info.get("competency_id", competency_id)

            pkg_path = Path(gen_info["package_path"])
            data_src = pkg_path / "data"
            if data_src.exists():
                shutil.copytree(data_src, scratch_dir / "data", dirs_exist_ok=True)
            nb_src = pkg_path / "marimo" / "challenge.py"
            if nb_src.exists():
                notebook_code = nb_src.read_text(encoding="utf-8")

        # 2. Materialize evidence telemetry artifacts into scratch data directory
        for fname, val in artifacts_dict.items():
            out_file = scratch_dir / "data" / fname
            out_file.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(val, str) and val.startswith("base64:"):
                out_file.write_bytes(base64.b64decode(val[7:]))
            else:
                out_file.write_text(val if isinstance(val, str) else json.dumps(val), encoding="utf-8")

        # 3. Materialize interactive Marimo notebook
        marimo_script = scratch_dir / "marimo" / "challenge.py"
        if notebook_code:
            marimo_script.write_text(notebook_code, encoding="utf-8")
        else:
            marimo_script.write_text(f'''import marimo
app = marimo.App(width="full", app_title="{title}")
@app.cell
def __(mo):
    mo.md("# 🛡️ {title}\\nInvestigate data in `data/` and submit flag.")
''')

        # 4. Configure Marimo dark theme
        # 4. Configure Marimo dark theme and autorun
        config_dir = scratch_dir / ".config" / "marimo"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "marimo.toml").write_text('[display]\ntheme = "dark"\ndataframes = "rich"\n')
        marimo_config_content = (
            '[display]\n'
            'theme = "dark"\n'
            'dataframes = "rich"\n\n'
            '[runtime]\n'
            'auto_instantiate = true\n'
            'on_cell_change = "autorun"\n\n'
            '[server]\n'
            'browser = false\n'
        )
        (config_dir / "marimo.toml").write_text(marimo_config_content)
        # Also write .marimo.toml in the working directory where marimo runs
        (scratch_dir / ".marimo.toml").write_text(marimo_config_content)

        # 5. Spawn isolated Marimo run process (app mode: code hidden, analysis console visible)
        # Always launch Marimo with the backend interpreter. This guarantees that
        # the child uses the same project-local venv on every platform and avoids
        # accidentally selecting a stale global or .venv executable.
        cmd = [
            sys.executable,
            "-m",
            "marimo",
            "run",
            str(marimo_script.resolve()),
            "--host",
            "127.0.0.1",
            "--port",
            str(assigned_port),
            "--no-token",
            "--headless",
            "--no-skew-protection",
            "--allow-origins",
            "*",
        ]

        env = dict(os.environ)
        env["PYTHONUNBUFFERED"] = "1"
        env["_MARIMO_CONFIG_OVERLOAD_RUNTIME_AUTO_INSTANTIATE"] = "true"
        env["XDG_CONFIG_HOME"] = str(scratch_dir / ".config")
        current_pp = env.get("PYTHONPATH", "")
        sys_paths = [p for p in sys.path if p]
        env["PYTHONPATH"] = os.pathsep.join(sys_paths) + (f"{os.pathsep}{current_pp}" if current_pp else "")
        if "HOME" not in env or not env["HOME"]:
            env["HOME"] = os.path.expanduser("~")

        proc = None
        bound = False
        launch_error = ""
        try:
            popen_kwargs: Dict[str, Any] = {}
            if sys.platform == "win32":
                popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            # Uvicorn's Windows reload loop may use a SelectorEventLoop, whose
            # asyncio subprocess transport raises NotImplementedError. Popen is
            # portable here; creation runs in a worker so the API loop stays free.
            proc = await asyncio.to_thread(
                subprocess.Popen,
                cmd,
                cwd=str(scratch_dir),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                **popen_kwargs,
            )
            # A cold Marimo start can take several seconds, so wait up to 15 seconds for the port.
            for _ in range(150):
                if proc.poll() is not None:
                    break
                await asyncio.sleep(0.1)
                if self._is_port_listening(assigned_port):
                    bound = True
                    break
        except Exception as e:
            launch_error = f"{type(e).__name__}: {e}"
            logger.exception("Could not spawn Marimo process")

        if not bound:
            if proc is not None:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        await asyncio.to_thread(proc.wait, 2.0)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        await asyncio.to_thread(proc.wait)
                if proc.stderr is not None:
                    stderr = proc.stderr.read().strip()
                    if stderr:
                        launch_error = stderr
                        logger.warning("Marimo launch failed: %s", stderr[-1000:])
                    proc.stderr.close()
            shutil.rmtree(scratch_dir, ignore_errors=True)
            raise RuntimeError(
                "The Marimo analyst console could not start on the server. "
                f"Launch details: {launch_error[-300:] or 'Marimo exited before binding a port.'}"
            )

        session = ActiveSession(
            session_id=session_id,
            challenge_id=challenge_id,
            title=title,
            category=category,
            difficulty=difficulty,
            base_points=points,
            flag=flag,
            hints=hints,
            objectives=objectives,
            scenario_md=scenario_md,
            competency_id=competency_id,
            assigned_port=assigned_port,
            scratch_dir=scratch_dir,
            duration_minutes=duration_minutes,
            process=proc,
        )
        session.log_file = None
        self._sessions[session_id] = session

        # 6. Record session in database if db is available
        if db is not None and db_chal is not None:
            try:
                db_sess = CyberSandboxSession(
                    id=session_id,
                    user_id=user_id,
                    challenge_id=challenge_id,
                    status="running",
                    assigned_port=assigned_port,
                    flag=flag,
                    unlocked_hints_json="[]",
                    total_penalties=0,
                    final_score=0,
                    is_solved=False,
                    expires_at=session.expires_at,
                )
                db.add(db_sess)
                db.commit()
            except Exception as e:
                logger.warning(f"Could not persist session to DB: {e}")

        # Form public marimo url
        marimo_url = f"http://127.0.0.1:{assigned_port}"

        # Sanitized hints for client (locked)
        client_hints = [
            {"id": h.get("id", i + 1), "penalty": h.get("penalty", 15), "unlocked": False}
            for i, h in enumerate(hints)
        ]

        return SandboxSessionResponse(
            session_id=session_id,
            challenge_id=challenge_id,
            title=title,
            category=category,
            difficulty=difficulty,
            points=points,
            expires_at=session.expires_at.isoformat(),
            remaining_seconds=session.remaining_seconds,
            status="running",
            assigned_port=assigned_port,
            marimo_url=marimo_url,
            hints=client_hints,
            scenario_md=scenario_md,
            objectives=objectives,
            solved=False,
        )

    def _restore_session_from_db(
        self, session_id: str, db: Optional[Session]
    ) -> Optional[ActiveSession]:
        if db is None:
            return None
        try:
            db_sess = db.query(CyberSandboxSession).filter_by(id=session_id).first()
            if not db_sess:
                return None
            db_chal = db.query(CyberSandboxChallenge).filter_by(id=db_sess.challenge_id).first()
            if not db_chal:
                return None

            hints = json.loads(db_chal.hints_json) if db_chal.hints_json else []
            objectives = json.loads(db_chal.objectives_json) if db_chal.objectives_json else []
            scratch_dir = SCRATCH_BASE_DIR / session_id

            session = ActiveSession(
                session_id=session_id,
                challenge_id=db_chal.id,
                title=db_chal.title,
                category=db_chal.category,
                difficulty=db_chal.difficulty,
                base_points=db_chal.points,
                flag=db_sess.flag,
                hints=hints,
                objectives=objectives,
                scenario_md=db_chal.scenario_markdown or "",
                competency_id=db_chal.competency_id or "soc_investigation",
                assigned_port=db_sess.assigned_port,
                scratch_dir=scratch_dir,
            )
            if db_sess.expires_at:
                exp = db_sess.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=datetime.timezone.utc)
                session.expires_at = exp
            session.unlocked_hint_ids = (
                json.loads(db_sess.unlocked_hints_json)
                if db_sess.unlocked_hints_json
                else []
            )
            session.total_penalties = db_sess.total_penalties or 0
            session.is_solved = bool(db_sess.is_solved)
            session.status = db_sess.status

            self._sessions[session_id] = session
            return session
        except Exception as e:
            logger.warning(f"Error restoring session {session_id} from DB: {e}")
            return None

    def get_session(
        self, session_id: str, db: Optional[Session] = None
    ) -> Optional[SandboxSessionResponse]:
        session = self._sessions.get(session_id)
        if not session and db is not None:
            session = self._restore_session_from_db(session_id, db)
        if not session:
            return None

        if session.remaining_seconds <= 0:
            session.status = "expired"

        client_hints = []
        for h in session.hints:
            hid = h.get("id", 1)
            is_unlocked = hid in session.unlocked_hint_ids
            client_hints.append({
                "id": hid,
                "penalty": h.get("penalty", 15),
                "unlocked": is_unlocked,
                "content": h.get("content", "") if is_unlocked else None,
            })

        return SandboxSessionResponse(
            session_id=session.session_id,
            challenge_id=session.challenge_id,
            title=session.title,
            category=session.category,
            difficulty=session.difficulty,
            points=session.current_points,
            expires_at=session.expires_at.isoformat(),
            remaining_seconds=session.remaining_seconds,
            status=session.status,
            assigned_port=session.assigned_port,
            marimo_url=f"http://127.0.0.1:{session.assigned_port}",
            hints=client_hints,
            scenario_md=session.scenario_md,
            objectives=session.objectives,
            solved=session.is_solved,
        )

    async def stop_session(self, session_id: str, db: Optional[Session] = None) -> bool:
        session = self._sessions.get(session_id)
        if not session and db is not None:
            session = self._restore_session_from_db(session_id, db)
        if not session:
            if db is not None:
                db_sess = db.query(CyberSandboxSession).filter_by(id=session_id).first()
                if db_sess:
                    db_sess.status = "stopped"
                    db.commit()
                    return True
            return False
        if session.process:
            try:
                if session.process.poll() is None:
                    session.process.terminate()
                    try:
                        await asyncio.to_thread(session.process.wait, 2.0)
                    except subprocess.TimeoutExpired:
                        session.process.kill()
                        await asyncio.to_thread(session.process.wait)
                if session.process.stderr is not None:
                    session.process.stderr.close()
            except Exception:
                logger.exception("Could not stop Marimo process for session %s", session_id)
        if session.log_file:
            try:
                session.log_file.close()
            except Exception:
                pass
        session.status = "stopped"

        # Update database record
        if db is not None:
            try:
                db_sess = db.query(CyberSandboxSession).filter_by(id=session_id).first()
                if db_sess:
                    db_sess.status = "stopped"
                    db.commit()
            except Exception as e:
                logger.warning(f"Error stopping session in DB: {e}")

        # Clean ephemeral scratch files
        try:
            if session.scratch_dir.exists():
                shutil.rmtree(session.scratch_dir, ignore_errors=True)
        except Exception:
            pass

        return True

    def submit_flag(
        self,
        session_id: str,
        flag_attempt: str,
        db: Optional[Session] = None,
        user_id: Optional[int] = None,
        challenge_id: Optional[str] = None,
    ) -> SandboxFlagSubmitResponse:
        session = self._sessions.get(session_id)
        if not session and db is not None:
            session = self._restore_session_from_db(session_id, db)

        if not session:
            # Fallback check directly against database challenge record
            if db is not None:
                db_chal = None
                if challenge_id:
                    db_chal = db.query(CyberSandboxChallenge).filter_by(id=challenge_id).first()
                if not db_chal and not session_id.startswith("sim_"):
                    db_chal = db.query(CyberSandboxChallenge).filter_by(id=session_id).first()
                if db_chal and db_chal.flag:
                    if flag_attempt.strip().lower() == db_chal.flag.strip().lower():
                        return SandboxFlagSubmitResponse(
                            correct=True,
                            message="🎯 CONGRATULATIONS! Incident Flag Verified. Threat neutralized and points recorded.",
                            points_awarded=db_chal.points,
                            competency_id=db_chal.competency_id or "soc_investigation",
                            competency_score=db_chal.points,
                        )

            return SandboxFlagSubmitResponse(
                correct=False,
                message="Session not found or already terminated.",
                points_awarded=0,
                competency_id="unknown",
                competency_score=0,
            )

        if session.remaining_seconds <= 0:
            session.status = "expired"
            return SandboxFlagSubmitResponse(
                correct=False,
                message="Session has expired. Please launch a new sandbox.",
                points_awarded=0,
                competency_id=session.competency_id,
                competency_score=0,
            )

        clean_attempt = flag_attempt.strip()
        expected = session.flag.strip()

        # Validation comparison (case-insensitive flag check)
        if clean_attempt.lower() == expected.lower():
            session.is_solved = True
            session.solved_at = datetime.datetime.now(datetime.timezone.utc)
            points_awarded = session.current_points

            # Map competency_id to radar
            field = "soc_investigation"
            if "phishing" in session.competency_id:
                field = "phishing_analysis"
            elif "cloud" in session.competency_id:
                field = "cloud_security"
            elif "dpi" in session.competency_id:
                field = "dpi_security"
            elif "forensics" in session.competency_id or "linux" in session.competency_id:
                field = "digital_forensics"

            # In-memory tracking
            user_key = str(user_id) if user_id else "current_user"
            if user_key not in self._user_competencies:
                self._user_competencies[user_key] = UserCompetencyRadar()
            comp = self._user_competencies[user_key]
            current_val = getattr(comp, field, 0)
            setattr(comp, field, current_val + points_awarded)
            comp.total_score += points_awarded
            comp.solved_challenges_count += 1

            # Database tracking
            if db is not None:
                try:
                    db_sess = db.query(CyberSandboxSession).filter_by(id=session_id).first()
                    if db_sess:
                        db_sess.is_solved = True
                        db_sess.status = "solved"
                        db_sess.solved_at = datetime.datetime.utcnow()
                        db_sess.final_score = points_awarded

                    if user_id:
                        user_comp = db.query(UserCyberCompetency).filter_by(user_id=user_id).first()
                        if not user_comp:
                            user_comp = UserCyberCompetency(user_id=user_id)
                            db.add(user_comp)
                        c_val = getattr(user_comp, field, 0) or 0
                        setattr(user_comp, field, c_val + points_awarded)
                        user_comp.total_score = (user_comp.total_score or 0) + points_awarded
                        user_comp.solved_challenges_count = (user_comp.solved_challenges_count or 0) + 1
                    db.commit()
                except Exception as e:
                    logger.warning(f"Error persisting flag victory to DB: {e}")

            return SandboxFlagSubmitResponse(
                correct=True,
                message="🎯 CONGRATULATIONS! Incident Flag Verified. Threat neutralized and points recorded.",
                points_awarded=points_awarded,
                competency_id=session.competency_id,
                competency_score=getattr(comp, field),
            )

        return SandboxFlagSubmitResponse(
            correct=False,
            message="❌ INCORRECT FLAG. Check evidence telemetry, decode artifacts, and try again.",
            points_awarded=0,
            competency_id=session.competency_id,
            competency_score=0,
        )

    def unlock_hint(
        self,
        session_id: str,
        hint_id: int,
        db: Optional[Session] = None,
        challenge_id: Optional[str] = None,
    ) -> SandboxHintUnlockResponse:
        session = self._sessions.get(session_id)
        if not session and db is not None:
            session = self._restore_session_from_db(session_id, db)

        if not session:
            # Fallback lookup directly against challenge in DB or templates
            db_chal = None
            if db is not None:
                if challenge_id:
                    db_chal = db.query(CyberSandboxChallenge).filter_by(id=challenge_id).first()
                if not db_chal and not session_id.startswith("sim_"):
                    db_chal = db.query(CyberSandboxChallenge).filter_by(id=session_id).first()
                if not db_chal:
                    db_chal = db.query(CyberSandboxChallenge).first()

            if db_chal and db_chal.hints_json:
                try:
                    hints = json.loads(db_chal.hints_json)
                    matching = next((h for h in hints if h.get("id") == hint_id), None)
                    if matching:
                        penalty = matching.get("penalty", 15)
                        content = matching.get("content", "Follow evidence telemetry to locate the flag.")
                        return SandboxHintUnlockResponse(
                            hint_id=hint_id,
                            content=content,
                            penalty=penalty,
                            remaining_points=max(10, db_chal.points - penalty),
                        )
                except Exception as e:
                    logger.warning(f"Error parsing hints from challenge: {e}")

            if challenge_id and challenge_id in self._templates:
                tmpl = self._templates[challenge_id]
                slots = tmpl.generate_random_slots(seed=f"seed_{challenge_id}")
                hints = tmpl.generate_hints(slots)
                matching = next((h for h in hints if h.get("id") == hint_id), None)
                if matching:
                    penalty = matching.get("penalty", 15)
                    return SandboxHintUnlockResponse(
                        hint_id=hint_id,
                        content=matching.get("content", ""),
                        penalty=penalty,
                        remaining_points=max(10, tmpl.base_points - penalty),
                    )

            return SandboxHintUnlockResponse(
                hint_id=hint_id,
                content="Session not found.",
                penalty=0,
                remaining_points=0,
            )

        matching = next((h for h in session.hints if h.get("id") == hint_id), None)
        if not matching:
            return SandboxHintUnlockResponse(
                hint_id=hint_id,
                content="Hint ID not found for this challenge.",
                penalty=0,
                remaining_points=session.current_points,
            )

        if hint_id not in session.unlocked_hint_ids:
            penalty = matching.get("penalty", 15)
            session.unlocked_hint_ids.append(hint_id)
            session.total_penalties += penalty

            if db is not None:
                try:
                    db_sess = db.query(CyberSandboxSession).filter_by(id=session_id).first()
                    if db_sess:
                        db_sess.unlocked_hints_json = json.dumps(session.unlocked_hint_ids)
                        db_sess.total_penalties = session.total_penalties
                        db.commit()
                except Exception as e:
                    logger.warning(f"Error persisting unlocked hint to DB: {e}")

        return SandboxHintUnlockResponse(
            hint_id=hint_id,
            content=matching.get("content", ""),
            penalty=matching.get("penalty", 15),
            remaining_points=session.current_points,
        )

    def get_competencies(
        self,
        user_key: str = "current_user",
        db: Optional[Session] = None,
        user_id: Optional[int] = None,
    ) -> UserCompetencyRadar:
        if db is not None and user_id is not None:
            try:
                user_comp = db.query(UserCyberCompetency).filter_by(user_id=user_id).first()
                if user_comp:
                    return UserCompetencyRadar(
                        soc_investigation=user_comp.soc_investigation or 0,
                        phishing_analysis=user_comp.phishing_analysis or 0,
                        cloud_security=user_comp.cloud_security or 0,
                        dpi_security=user_comp.dpi_security or 0,
                        digital_forensics=user_comp.digital_forensics or 0,
                        total_score=user_comp.total_score or 0,
                        solved_challenges_count=user_comp.solved_challenges_count or 0,
                    )
            except Exception as e:
                logger.warning(f"Error fetching competencies from DB: {e}")

        if user_key not in self._user_competencies:
            self._user_competencies[user_key] = UserCompetencyRadar()
        return self._user_competencies[user_key]


sandbox_manager = SandboxManager()
