# Court detection and mapping module
# Migrated from Good-Badminton project
from .reference import BadmintonCourtReference
from .reference import (
    BADMINTON_COURT_WIDTH,
    BADMINTON_COURT_LENGTH,
    BADMINTON_SINGLES_MARGIN,
    BADMINTON_BACK_SERVICE_OFFSET,
    BADMINTON_SERVICE_LINE_FROM_NET,
)
from .detector import auto_detect_court_corners, render_auto_court_preview
from .mapper import CourtMapper, compute_expanded_roi, resolve_court_corners, auto_detect_preview