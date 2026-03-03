"""Unifier module for MAGI.

Standardizes classifier outputs into a unified feature matrix and
applies normalization.
"""

from magi.unifier.standardize import standardize_outputs
from magi.unifier.matrix import build_feature_matrix
from magi.unifier.normalize import normalize

__all__ = ["standardize_outputs", "build_feature_matrix", "normalize"]
