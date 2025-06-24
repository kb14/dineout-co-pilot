"""
Evaluation framework for the Dineout GenAI Co-Pilot.

This module provides various evaluators to assess the quality and correctness
of generated restaurant performance reports.
"""

from .evaluators.structural import StructuralEvaluator

__all__ = ['StructuralEvaluator']