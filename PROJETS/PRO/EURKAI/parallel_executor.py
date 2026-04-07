#!/usr/bin/env python3
"""
parallel_executor.py — EURKAI ParallelExecutionLayer
──────────────────────────────────────────────────────
Runs multiple pipeline projects in parallel.
The internal pipeline (pipeline.run_pipeline) is called unchanged
in each worker process. No shared state. Zero modifications to pipeline.py.

Architecture:
    project_queue  → list[ProjectConfig]
    worker_pool    → ProcessPoolExecutor(max_workers=N)
    dispatcher     → submits one future per project
    result_collector → aggregates ExecutionResult → batch_summary.json

Usage — as library:
    from parallel_executor import run_batch, ProjectConfig

    results = run_batch([
        ProjectConfig("VectorStack",    "SaaS devops platform..."),
        ProjectConfig("Atelier Noir",   "Luxury editorial brand..."),
        ProjectConfig("CandleSpark",    "Artisan candle brand..."),
    ], workers=3)

Usage — as CLI:
    python parallel_executor.py --workers 3 --project vectorstack
    python parallel_executor.py --workers 4 --all
    python parallel_executor.py --workers 2 --briefs briefs.json
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed, Future
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ─── Paths ────────────────────────────────────────────────────────────────────

SCRIPT_DIR  = Path(__file__).parent
OUTPUT_DIR  = SCRIPT_DIR / "output"
MODULES_DIR = SCRIPT_DIR / "MODULES"


# ─── Schema ───────────────────────────────────────────────────────────────────

@dataclass
class ProjectConfig:
    """
    Input configuration for one pipeline run.
    Fully serializable (picklable) — safe to send to worker processes.
    """
    name:            str
    brief:           str
    seed:            int    = 42
    harmony:         str    = "complementary"
    site_family:     str    = ""
    enable_capture:  bool   = False   # off by default in batch (no display needed)
    enable_audit:    bool   = False   # off by default in batch (speed)
    enable_learning: bool   = True
    output_dir:      str    = ""      # "" → uses pipeline default (OUTPUT_DIR/slug)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("ProjectConfig.name must not be empty")
        if not self.brief.strip():
            raise ValueError("ProjectConfig.brief must not be empty")


@dataclass
class ExecutionResult:
    """
    Output of one pipeline run.
    Serializable. Aggregated by result_collector into batch summary.
    """
    project_name:   str
    success:        bool
    status:         str         # "success" | "failure" | "timeout"
    duration_s:     float
    output_path:    Optional[str]
    final_score:    int         # vision audit score (0 if audit disabled)
    attempts:       int         # plan validation attempts
    fix_iterations: int         # auto-fix iterations
    error:          Optional[str]
    worker_pid:     int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BatchSummary:
    """Aggregated result of a full batch execution."""
    batch_id:       str
    started_at:     str
    finished_at:    str
    total_duration_s: float
    workers_used:   int
    total:          int
    succeeded:      int
    failed:         int
    results:        list[dict]

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Worker function (top-level — required for pickling) ─────────────────────

def _worker(config: ProjectConfig) -> ExecutionResult:
    """
    Entry point for each worker process.
    Imports pipeline fresh (process isolation), runs it, returns a result.
    Must be defined at module top level for ProcessPoolExecutor to pickle it.
    """
    t0  = time.monotonic()
    pid = os.getpid()

    # ── Path setup (each process builds its own sys.path) ────────────────────
    script_dir  = Path(__file__).parent
    modules_dir = script_dir / "MODULES"
    for mod in sorted(modules_dir.iterdir()):
        if mod.is_dir() and not mod.name.startswith(("_", ".")):
            p = str(mod)
            if p not in sys.path:
                sys.path.insert(0, p)
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

    # ── Import pipeline (happens once per process) ────────────────────────────
    try:
        from pipeline import run_pipeline  # type: ignore
    except ImportError as e:
        return ExecutionResult(
            project_name=config.name,
            success=False,
            status="failure",
            duration_s=round(time.monotonic() - t0, 2),
            output_path=None,
            final_score=0,
            attempts=0,
            fix_iterations=0,
            error=f"Import error: {e}",
            worker_pid=pid,
        )

    # ── Run pipeline ──────────────────────────────────────────────────────────
    try:
        kwargs: dict = dict(
            brief=config.brief,
            project_name=config.name,
            seed=config.seed,
            harmony=config.harmony,
            site_family=config.site_family,
            enable_capture=config.enable_capture,
            enable_audit=config.enable_audit,
            enable_learning=config.enable_learning,
            verbose=False,           # suppress per-line output in batch mode
        )
        if config.output_dir:
            kwargs["output_dir"] = config.output_dir

        result = run_pipeline(**kwargs)

        return ExecutionResult(
            project_name=config.name,
            success=(result.status == "success"),
            status=result.status,
            duration_s=round(time.monotonic() - t0, 2),
            output_path=result.output_path,
            final_score=result.final_score,
            attempts=result.attempts,
            fix_iterations=result.fix_iterations,
            error=result.error,
            worker_pid=pid,
        )

    except Exception:
        return ExecutionResult(
            project_name=config.name,
            success=False,
            status="failure",
            duration_s=round(time.monotonic() - t0, 2),
            output_path=None,
            final_score=0,
            attempts=0,
            fix_iterations=0,
            error=traceback.format_exc(limit=6),
            worker_pid=pid,
        )


# ─── ParallelExecutor ─────────────────────────────────────────────────────────

class ParallelExecutor:
    """
    Execution layer over the EURKAI pipeline.
    Submits projects to a worker pool. Collects and writes results.

    Does NOT modify pipeline.py. It calls run_pipeline() as a black box.

    Example:
        executor = ParallelExecutor(workers=4, timeout_s=300)
        summary  = executor.run([config1, config2, config3])
    """

    def __init__(
        self,
        workers:    int  = 3,
        timeout_s:  int  = 300,     # per-project timeout in seconds
        output_dir: Path = OUTPUT_DIR,
        verbose:    bool = True,
    ) -> None:
        if not 1 <= workers <= 10:
            raise ValueError(f"workers must be 1–10, got {workers}")
        self.workers    = workers
        self.timeout_s  = timeout_s
        self.output_dir = Path(output_dir)
        self.verbose    = verbose

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self, projects: list[ProjectConfig]) -> BatchSummary:
        """
        Dispatch all projects to the worker pool.
        Returns a BatchSummary when all are complete.
        """
        if not projects:
            raise ValueError("projects list is empty")

        batch_id   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        started_at = datetime.now(timezone.utc).isoformat()
        t0_wall    = time.monotonic()

        effective_workers = min(self.workers, len(projects))
        results: list[ExecutionResult] = []

        self._print(
            f"\n{'═' * 62}\n"
            f"  EURKAI Parallel Executor\n"
            f"  {len(projects)} project(s) · {effective_workers} worker(s)\n"
            f"{'═' * 62}"
        )

        # ── Dispatch ──────────────────────────────────────────────────────────
        future_to_config: dict[Future, ProjectConfig] = {}

        with ProcessPoolExecutor(max_workers=effective_workers) as pool:

            # Submit all tasks
            for config in projects:
                future = pool.submit(_worker, config)
                future_to_config[future] = config
                self._print(f"  → queued  {config.name}")

            self._print(f"\n  Running…\n")

            # Collect as they complete
            for future in as_completed(future_to_config, timeout=self.timeout_s * len(projects)):
                config = future_to_config[future]
                try:
                    result: ExecutionResult = future.result(timeout=self.timeout_s)
                except TimeoutError:
                    result = ExecutionResult(
                        project_name=config.name,
                        success=False,
                        status="timeout",
                        duration_s=float(self.timeout_s),
                        output_path=None,
                        final_score=0,
                        attempts=0,
                        fix_iterations=0,
                        error=f"Timed out after {self.timeout_s}s",
                        worker_pid=-1,
                    )
                except Exception as e:
                    result = ExecutionResult(
                        project_name=config.name,
                        success=False,
                        status="failure",
                        duration_s=0.0,
                        output_path=None,
                        final_score=0,
                        attempts=0,
                        fix_iterations=0,
                        error=f"Executor error: {e}",
                        worker_pid=-1,
                    )

                results.append(result)
                self._log_result(result)

        # ── Assemble summary ──────────────────────────────────────────────────
        finished_at  = datetime.now(timezone.utc).isoformat()
        total_s      = round(time.monotonic() - t0_wall, 2)
        succeeded    = sum(1 for r in results if r.success)
        failed       = len(results) - succeeded

        summary = BatchSummary(
            batch_id=batch_id,
            started_at=started_at,
            finished_at=finished_at,
            total_duration_s=total_s,
            workers_used=effective_workers,
            total=len(results),
            succeeded=succeeded,
            failed=failed,
            results=[r.to_dict() for r in results],
        )

        self._write_summary(summary, batch_id)
        self._print_summary(summary)

        return summary

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _print(self, msg: str) -> None:
        if self.verbose:
            print(msg, flush=True)

    def _log_result(self, r: ExecutionResult) -> None:
        if not self.verbose:
            return
        icon  = "✅" if r.success else "❌"
        score = f"  score={r.final_score}" if r.final_score else ""
        print(
            f"  {icon}  {r.project_name:<28s}  "
            f"{r.duration_s:6.1f}s  "
            f"pid={r.worker_pid}{score}",
            flush=True,
        )
        if r.error and not r.success:
            # First line only — full trace is in the summary JSON
            first_line = r.error.strip().splitlines()[-1]
            print(f"      ↳ {first_line}", flush=True)

    def _write_summary(self, summary: BatchSummary, batch_id: str) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / f"batch_summary_{batch_id}.json"
        path.write_text(
            json.dumps(summary.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        # Also overwrite a stable "latest" pointer
        latest = self.output_dir / "batch_summary_latest.json"
        latest.write_text(
            json.dumps(summary.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        if self.verbose:
            print(f"\n  📄 Summary → {path}", flush=True)

    def _print_summary(self, s: BatchSummary) -> None:
        self._print(
            f"\n{'─' * 62}\n"
            f"  {s.succeeded}/{s.total} succeeded  "
            f"· {s.failed} failed  "
            f"· {s.total_duration_s:.1f}s wall time\n"
            f"{'═' * 62}\n"
        )


# ─── Convenience function ─────────────────────────────────────────────────────

def run_batch(
    projects:   list[ProjectConfig],
    workers:    int  = 3,
    timeout_s:  int  = 300,
    output_dir: Path = OUTPUT_DIR,
    verbose:    bool = True,
) -> BatchSummary:
    """
    One-call API.  Equivalent to ParallelExecutor(...).run(projects).

    Example:
        from parallel_executor import run_batch, ProjectConfig
        summary = run_batch([
            ProjectConfig("VectorStack", "devops saas..."),
            ProjectConfig("Atelier Noir", "luxury editorial..."),
        ], workers=2)
    """
    return ParallelExecutor(
        workers=workers,
        timeout_s=timeout_s,
        output_dir=output_dir,
        verbose=verbose,
    ).run(projects)


# ─── Test briefs (mirrors generate_brand_charter.py defaults) ─────────────────

_TEST_PROJECTS: list[ProjectConfig] = [
    ProjectConfig(
        name="VectorStack",
        brief=(
            "B2B SaaS platform for DevOps infrastructure automation. "
            "Target audience: CTOs and senior engineers. Core values: "
            "reliability, precision, structured. Tone: professional, modern. "
            "Keywords: automation, orchestration, data infrastructure, developer tools."
        ),
        seed=100,
    ),
    ProjectConfig(
        name="Atelier Nocturne",
        brief=(
            "Luxury editorial brand — art books, photography, slow living. "
            "Inspired by Japanese minimalism and French editorial design. "
            "Audience: aesthetes, collectors, cultural professionals. "
            "Tone: refined, quiet, timeless. Avoid: playful colors, gradients."
        ),
        seed=200,
    ),
    ProjectConfig(
        name="CandleSpark",
        brief=(
            "Artisan candle brand — hand-poured, natural wax, premium scents. "
            "Warm, cozy, wellness-oriented. Target: women 25-45, gifting context. "
            "Tone: organic, premium craft, authentic. Values: quality, nature, ritual."
        ),
        seed=300,
    ),
]


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _load_briefs_from_json(path: str) -> list[ProjectConfig]:
    """
    Load a list of ProjectConfig from a JSON file.

    Expected format:
        [
          {"name": "...", "brief": "...", "seed": 42},
          ...
        ]
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    configs = []
    for item in data:
        if "name" not in item or "brief" not in item:
            raise ValueError(f"Each item must have 'name' and 'brief': {item}")
        configs.append(ProjectConfig(**{
            k: v for k, v in item.items()
            if k in ProjectConfig.__dataclass_fields__
        }))
    return configs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="EURKAI Parallel Executor — run multiple projects in parallel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python parallel_executor.py --all --workers 3
  python parallel_executor.py --project vectorstack --workers 1
  python parallel_executor.py --briefs briefs.json --workers 4
        """,
    )
    parser.add_argument("--workers",  type=int, default=3, help="Number of parallel workers (1–10)")
    parser.add_argument("--timeout",  type=int, default=300, help="Per-project timeout in seconds")
    parser.add_argument("--all",      action="store_true", help="Run all 3 default test projects")
    parser.add_argument("--project",  metavar="NAME", help="Run a single test project by name")
    parser.add_argument("--briefs",   metavar="FILE", help="Load projects from a JSON file")
    parser.add_argument("--no-capture", action="store_true", help="Disable screenshot capture")
    parser.add_argument("--no-audit",   action="store_true", help="Disable vision audit")
    parser.add_argument("--quiet",    action="store_true", help="Suppress progress output")
    args = parser.parse_args()

    # ── Select projects ───────────────────────────────────────────────────────
    if args.briefs:
        projects = _load_briefs_from_json(args.briefs)

    elif args.project:
        name_lower = args.project.lower()
        projects = [
            p for p in _TEST_PROJECTS
            if name_lower in p.name.lower()
               or name_lower in p.name.lower().replace(" ", "")
        ]
        if not projects:
            print(f"❌ No test project matching '{args.project}'.")
            print(f"   Available: {[p.name for p in _TEST_PROJECTS]}")
            sys.exit(1)

    else:
        # Default: --all
        projects = _TEST_PROJECTS

    # Apply CLI flags to all configs
    projects = [
        ProjectConfig(
            name=p.name,
            brief=p.brief,
            seed=p.seed,
            harmony=p.harmony,
            site_family=p.site_family,
            enable_capture=not args.no_capture,
            enable_audit=not args.no_audit,
            enable_learning=p.enable_learning,
        )
        for p in projects
    ]

    run_batch(
        projects=projects,
        workers=args.workers,
        timeout_s=args.timeout,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    # Required on macOS (spawn start method) and safe on Linux
    import multiprocessing
    multiprocessing.set_start_method("spawn", force=True)
    main()
