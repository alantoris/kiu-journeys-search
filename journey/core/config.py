"""
Journey Service Configuration

This module contains configuration constants for the journey service.
These values define business rules and limitations for different versions.
"""

# ==========================================
# VERSION 1.0 CONFIGURATION & LIMITATIONS
# ==========================================

# Journey constraints (v1.0 limitations)
MAX_FLIGHTS_PER_JOURNEY = 2  # Future versions will support more flights
MAX_JOURNEY_DURATION_HOURS = 24
MAX_CONNECTION_TIME_HOURS = 4

# Business rules
MIN_FLIGHTS_PER_JOURNEY = 1

# ==========================================
# FUTURE VERSION CONSIDERATIONS
# ==========================================

# TODO v2.0: Increase MAX_FLIGHTS_PER_JOURNEY to support multi-leg journeys
# TODO v2.0: Add configurable connection time limits per airport
# TODO v2.0: Add support for overnight connections
# TODO v2.0: Add support for different journey types (business, leisure, etc.)

# Version information
VERSION = "1.0"
VERSION_LIMITATIONS = [
    "Maximum 2 flights per journey",
    "No support for complex multi-leg journeys",
    "Fixed connection time limits (4 hours max)",
    "Fixed total journey duration (24 hours max)"
]
