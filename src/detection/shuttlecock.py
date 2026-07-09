import numpy as np


class ShuttlecockTracker:
    """Track the shuttlecock across frames using YOLO detection with multi-stage filtering."""

    def __init__(
        self,
        yolo_ball_model,
        trajectory_length=30,
        max_jump_pixels=220,
        prediction_gate_pixels=260,
        max_missing_frames=5,
    ):
        self.yolo_ball = yolo_ball_model
        self.trajectory_length = trajectory_length
        self.max_jump_pixels = max_jump_pixels
        self.prediction_gate_pixels = prediction_gate_pixels
        self.max_missing_frames = max_missing_frames

        self.trajectory = []
        self.missing_frames = 0

    def detect_ball(self, frame, roi_corners=None, target_class=None):
        height, width = frame.shape[:2]
        results = self.yolo_ball(frame, verbose=False, conf=0.15, iou=0.3)

        if results is None or len(results) == 0 or results[0].boxes is None:
            return None

        boxes = results[0].boxes
        if boxes.xywh is None or len(boxes.xywh) == 0:
            return None

        candidates = []
        for idx in range(len(boxes.xywh)):
            conf = float(boxes.conf[idx]) if boxes.conf is not None else 0.0
            cls = int(boxes.cls[idx]) if boxes.cls is not None else -1
            if target_class is not None and cls != target_class:
                continue

            x, y, w, h = [float(val) for val in boxes.xywh[idx]]
            area = w * h
            aspect_ratio = w / max(h, 1e-6)
            if area < 4 or area > width * height * 0.12:
                continue
            if aspect_ratio < 0.3 or aspect_ratio > 3.0:
                continue

            if roi_corners is not None:
                (rx1, ry1), (rx2, ry2) = roi_corners
                if x < rx1 or x > rx2 or y < ry1 or y > ry2:
                    continue

            candidates.append((conf, x, y))

        if not candidates:
            return None

        if self.trajectory:
            candidates.sort(key=lambda item: item[0], reverse=True)
            best_conf = candidates[0][0]
            candidates = [item for item in candidates if best_conf - item[0] <= 0.15]

        if len(candidates) == 1:
            return candidates[0][1:]

        if self.trajectory:
            pred = self._predict_next_position()
            if pred is not None:
                candidates.sort(key=lambda item: np.hypot(item[1] - pred[0], item[2] - pred[1]))
                return candidates[0][1:]

        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1:]

    def update_trajectory(self, ball_position, roi_corners=None):
        if ball_position is None:
            self.missing_frames += 1
            if self.missing_frames > self.max_missing_frames:
                self.trajectory = []
                self.missing_frames = 0
            return

        x, y = ball_position

        if roi_corners is not None:
            (rx1, ry1), (rx2, ry2) = roi_corners
            if x < rx1 or x > rx2 or y < ry1 or y > ry2:
                if self.trajectory:
                    pred = self._predict_next_position()
                    if pred is not None:
                        pred_x, pred_y = pred
                        if rx1 <= pred_x <= rx2 and ry1 <= pred_y <= ry2:
                            self.trajectory.append(pred)
                            self.missing_frames = 0
                            return
                self.missing_frames += 1
                if self.missing_frames > self.max_missing_frames:
                    self.trajectory = []
                    self.missing_frames = 0
                return

        if self.trajectory:
            last = self.trajectory[-1]
            distance = np.hypot(x - last[0], y - last[1])
            if distance > self.max_jump_pixels:
                pred = self._predict_next_position()
                if pred is not None:
                    pred_distance = np.hypot(x - pred[0], y - pred[1])
                    if pred_distance > self.prediction_gate_pixels:
                        self.missing_frames += 1
                        if self.missing_frames > self.max_missing_frames:
                            self.trajectory = []
                            self.missing_frames = 0
                        return
                    else:
                        self.trajectory.append(pred)
                        self.missing_frames = 0
                        return

        self.trajectory.append((x, y))
        self.missing_frames = 0

        if len(self.trajectory) > self.trajectory_length:
            self.trajectory = self.trajectory[-self.trajectory_length :]

    def handle_visualization(self, frame):
        if len(self.trajectory) < 2:
            return

        for idx in range(1, len(self.trajectory)):
            prev = self.trajectory[idx - 1]
            curr = self.trajectory[idx]
            prev_pt = (int(prev[0]), int(prev[1]))
            curr_pt = (int(curr[0]), int(curr[1]))
            alpha = (idx + 10) / (len(self.trajectory) + 10)
            if self.missing_frames > 0 and idx == len(self.trajectory) - 1:
                color = (0, 150, 255)
            else:
                color = (int(60 * (1 - alpha)), int(180 * alpha), int(255 * alpha))
            cv2 = __import__("cv2")
            cv2.line(frame, prev_pt, curr_pt, color, 2, cv2.LINE_AA)

    def _predict_next_position(self):
        if len(self.trajectory) < 2:
            return None

        prev = self.trajectory[-2]
        curr = self.trajectory[-1]
        dx = curr[0] - prev[0]
        dy = curr[1] - prev[1]
        return (curr[0] + dx, curr[1] + dy)