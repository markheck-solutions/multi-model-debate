"""Review phases for the adversarial critique workflow."""

from multi_model_debate.phases.base import Phase, PhaseArtifact
from multi_model_debate.phases.baseline import BaselinePhase
from multi_model_debate.phases.debate import DebatePhase
from multi_model_debate.phases.defense import DefensePhase
from multi_model_debate.phases.final_position import FinalPositionPhase
from multi_model_debate.phases.judge import JudgePhase
from multi_model_debate.phases.synthesis import PeerReviewPhase

__all__ = [
    # Base
    "Phase",
    "PhaseArtifact",
    # Phases
    "BaselinePhase",
    "DebatePhase",
    "JudgePhase",
    "PeerReviewPhase",
    "DefensePhase",
    "FinalPositionPhase",
]
