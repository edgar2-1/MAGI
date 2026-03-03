"""Classification module for MAGI.

Provides kingdom-specific taxonomic classification for bacteria,
fungi, and viruses.
"""

from magi.classify.bacteriome import classify_bacteriome
from magi.classify.mycobiome import classify_mycobiome
from magi.classify.virome import classify_virome

__all__ = ["classify_bacteriome", "classify_mycobiome", "classify_virome"]
