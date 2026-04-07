"""
design_pipeline — pipeline design v2 à milestones stricts.

Exports publics :
  run_pipeline_v2(brief, seed, palette, **kwargs) → dict
  PIPELINE_MILESTONES — séquence ordonnée des milestones
  MilestoneError — exception de pipeline
"""

from .pipeline_v2 import run_pipeline_v2
from .milestones import PIPELINE_MILESTONES
from .milestone_runner import MilestoneError

__all__ = ["run_pipeline_v2", "PIPELINE_MILESTONES", "MilestoneError"]
