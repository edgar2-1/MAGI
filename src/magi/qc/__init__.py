"""Quality control module for MAGI.

Provides read filtering, adapter trimming, and host removal.
"""

from magi.qc.filtering import filter_reads
from magi.qc.trimming import trim_adapters
from magi.qc.host_removal import remove_host

__all__ = ["filter_reads", "trim_adapters", "remove_host"]
