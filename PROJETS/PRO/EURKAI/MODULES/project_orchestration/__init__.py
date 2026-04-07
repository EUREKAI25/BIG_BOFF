"""
project_orchestration — EURKAI Core Orchestration Layer

v1.0 — Planning:
    ProjectDefinitionScenario   — brief → definition → execution_plan
    ProjectDefinition           — structured project output
    ExecutionPlan               — ordered module calls (flat)
    ExecutionStep               — one step (module_name, inputs, dependencies)
    ParsedBrief                 — structured brief output
    Need                        — single identified project need

v1.1 — Execution:
    ProjectBuildScenario        — execution_plan → chains → deliverables
    ChainStep                   — one module call within a chain
    ExecutionChain              — ordered steps for one need
    BuildResult                 — structured build output

Usage:
    from project_orchestration import ProjectDefinitionScenario, ProjectBuildScenario

    plan   = ProjectDefinitionScenario().run(brief="...")
    result = ProjectBuildScenario().run(plan["execution_plan"], initial_context={...})
"""
from .project_definition_scenario import (
    ProjectDefinitionScenario,
    ProjectDefinition,
    ExecutionPlan,
    ExecutionStep,
    ParsedBrief,
    Need,
)
from .project_build_scenario import (
    ProjectBuildScenario,
    ExecutionChain,
    ChainStep,
    BuildResult,
)

__version__ = "1.1.0"

__all__ = [
    # v1.0 — planning
    "ProjectDefinitionScenario",
    "ProjectDefinition",
    "ExecutionPlan",
    "ExecutionStep",
    "ParsedBrief",
    "Need",
    # v1.1 — execution
    "ProjectBuildScenario",
    "ExecutionChain",
    "ChainStep",
    "BuildResult",
]
