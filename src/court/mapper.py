import cv2
import numpy as np

from .reference import (
    BADMINTON_BACK_SERVICE_OFFSET,
    BADMINTON_COURT_LENGTH,
    BADMINTON_COURT_WIDTH,
    BADMINTON_SERVICE_LINE_FROM_NET,
    BADMINTON_SINGLES_MARGIN,
)
from .detector import auto_detect_court_corners, render_auto_court_preview


class CourtMapper:
    """Handles perspective transformation between image and court coordinates."""

    def __init__(self, image_court_corners):
        image_court_corners = np.array(image_court_corners, dtype=np.float32)
        court_points = np.array(
            [
                [0, 0],
                [BADMINTON_COURT_WIDTH, 0],
                [BADMINTON_COURT_WIDTH, BADMINTON_COURT_LENGTH],
                [0, BADMINTON_COURT_LENGTH],
            ],
            dtype=np.float32,
        )
        self.matrix = cv2.getPerspectiveTransform(image_court_corners, court_points)
        self.inv_matrix = cv2.getPerspectiveTransform(court_points, image_court_corners)

    def image_to_court(self, point):
        point = np.array([point], dtype=np.float32).reshape(-1, 1, 2)
        transformed = cv2.perspectiveTransform(point, self.matrix)
        return transformed[0][0]

    def court_to_image(self, point):
        point = np.array([point], dtype=np.float32).reshape(-1, 1, 2)
        transformed = cv2.perspectiveTransform(point, self.inv_matrix)
        return transformed[0][0]


def compute_expanded_roi(corners, image_shape, top_padding_ratio=0.18, bottom_padding_ratio=0.08, side_padding_ratio=0.09):
    height, width = image_shape[:2]
    top_left, top_right, bottom_right, bottom_left = corners
    top_y = min(top_left[1], top_right[1])
    bottom_y = max(bottom_left[1], bottom_right[1])
    left_x = min(top_left[0], bottom_left[0])
    right_x = max(top_right[0], bottom_right[0])
    court_height = bottom_y - top_y
    court_width = right_x - left_x

    top_padding = court_height * top_padding_ratio
    bottom_padding = court_height * bottom_padding_ratio
    side_padding = court_width * side_padding_ratio

    roi_x1 = max(0, int(left_x - side_padding))
    roi_y1 = max(0, int(top_y - top_padding))
    roi_x2 = min(width, int(right_x + side_padding))
    roi_y2 = min(height, int(bottom_y + bottom_padding))
    return (roi_x1, roi_y1), (roi_x2, roi_y2)


def resolve_court_corners(image, manual_corners=None):
    if manual_corners is not None and len(manual_corners) == 4:
        corners = [(int(point[0]), int(point[1])) for point in manual_corners]
        return np.array(corners, dtype=np.float32), None, None

    corners, mask, debug = auto_detect_court_corners(image)
    if corners is None:
        return None, mask, debug

    return np.array(corners, dtype=np.float32), mask, debug


def auto_detect_preview(image, manual_corners=None):
    corners, mask, debug = auto_detect_court_corners(image)
    roi_corners = None
    if corners is not None:
        roi_corners = compute_expanded_roi(corners, image.shape)
    return render_auto_court_preview(image, corners, roi_corners, debug)