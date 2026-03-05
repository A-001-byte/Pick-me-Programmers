"""
SORT (Simple Online and Realtime Tracking) Algorithm
Implements Kalman-filter-based single-object trackers and the full
SORT multi-object tracking pipeline with Hungarian assignment.
"""

import numpy as np
from filterpy.kalman import KalmanFilter
from scipy.optimize import linear_sum_assignment


# ---------------------------------------------------------------------------
# Helper: vectorised IoU
# ---------------------------------------------------------------------------

def iou_batch(bb_test, bb_gt):
    """
    Compute IoU between two sets of bounding boxes.

    Parameters
    ----------
    bb_test : np.ndarray, shape (N, 4) – [x1, y1, x2, y2]
    bb_gt   : np.ndarray, shape (M, 4) – [x1, y1, x2, y2]

    Returns
    -------
    iou_matrix : np.ndarray, shape (N, M)
    """
    bb_test = np.atleast_2d(bb_test).astype(float)
    bb_gt = np.atleast_2d(bb_gt).astype(float)

    xx1 = np.maximum(bb_test[:, 0:1], bb_gt[:, 0])  # (N, M)
    yy1 = np.maximum(bb_test[:, 1:2], bb_gt[:, 1])
    xx2 = np.minimum(bb_test[:, 2:3], bb_gt[:, 2])
    yy2 = np.minimum(bb_test[:, 3:4], bb_gt[:, 3])

    w = np.maximum(0.0, xx2 - xx1)
    h = np.maximum(0.0, yy2 - yy1)
    intersection = w * h

    area_test = (bb_test[:, 2] - bb_test[:, 0]) * (bb_test[:, 3] - bb_test[:, 1])
    area_gt = (bb_gt[:, 2] - bb_gt[:, 0]) * (bb_gt[:, 3] - bb_gt[:, 1])

    union = area_test[:, np.newaxis] + area_gt[np.newaxis, :] - intersection
    iou_matrix = np.where(union > 0, intersection / union, 0.0)
    return iou_matrix


def convert_bbox_to_z(bbox):
    """Convert [x1, y1, x2, y2] to [x_center, y_center, area, aspect_ratio]."""
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = bbox[0] + w / 2.0
    y = bbox[1] + h / 2.0
    s = w * h          # area
    r = w / float(h) if h > 0 else 0.0  # aspect ratio
    return np.array([x, y, s, r]).reshape((4, 1))


def convert_x_to_bbox(x):
    """Convert [x_center, y_center, area, aspect_ratio] back to [x1, y1, x2, y2]."""
    w = np.sqrt(max(x[2] * x[3], 0.0))
    h = x[2] / w if w > 0 else 0.0
    return np.array([
        x[0] - w / 2.0,
        x[1] - h / 2.0,
        x[0] + w / 2.0,
        x[1] + h / 2.0,
    ]).flatten()


# ---------------------------------------------------------------------------
# Kalman Box Tracker
# ---------------------------------------------------------------------------

class KalmanBoxTracker:
    """
    Single-object tracker using a Kalman filter.

    State vector: [x_center, y_center, area, aspect_ratio, vx, vy, va]
    """

    _id_counter = 0

    def __init__(self, bbox):
        """
        Parameters
        ----------
        bbox : array-like, shape (4,) or (5,)
            [x1, y1, x2, y2] (confidence ignored if present).
        """
        self.kf = KalmanFilter(dim_x=7, dim_z=4)

        # State transition matrix (constant velocity model)
        self.kf.F = np.array([
            [1, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1],
        ], dtype=float)

        # Measurement matrix
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
        ], dtype=float)

        # Covariance matrices
        self.kf.R[2:, 2:] *= 10.0       # measurement noise
        self.kf.P[4:, 4:] *= 1000.0     # high initial uncertainty for velocities
        self.kf.P *= 10.0
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01

        # Initialise state with the first detection
        self.kf.x[:4] = convert_bbox_to_z(bbox[:4])

        # Bookkeeping
        self.id = KalmanBoxTracker._id_counter
        KalmanBoxTracker._id_counter += 1

        self.time_since_update = 0
        self.hit_streak = 0
        self.age = 0
        self.history = []

    # ---- public API --------------------------------------------------------

    def predict(self):
        """Advance the state vector and return the predicted bbox."""
        # Prevent negative area
        if self.kf.x[6] + self.kf.x[2] <= 0:
            self.kf.x[6] *= 0.0

        self.kf.predict()
        self.age += 1

        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1

        predicted_bbox = convert_x_to_bbox(self.kf.x)
        self.history.append(predicted_bbox)
        return predicted_bbox

    def update(self, bbox):
        """Update the state with an observed bbox [x1, y1, x2, y2, ...]."""
        self.time_since_update = 0
        self.hit_streak += 1
        self.history = []
        self.kf.update(convert_bbox_to_z(bbox[:4]))

    def get_state(self):
        """Return the current bounding box estimate [x1, y1, x2, y2]."""
        return convert_x_to_bbox(self.kf.x)


# ---------------------------------------------------------------------------
# SORT Algorithm
# ---------------------------------------------------------------------------

class SortAlgorithm:
    """
    SORT: Simple Online and Realtime Tracking.

    Parameters
    ----------
    max_age       : int – frames before a track is deleted (default 30).
    min_hits      : int – minimum hits before a track is reported (default 3).
    iou_threshold : float – IoU threshold for assignment (default 0.3).
    """

    def __init__(self, max_age=30, min_hits=3, iou_threshold=0.3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.trackers: list[KalmanBoxTracker] = []
        self.frame_count = 0

    # ---- public API --------------------------------------------------------

    def update(self, detections=None):
        """
        Parameters
        ----------
        detections : np.ndarray, shape (N, 5)
            Each row: [x1, y1, x2, y2, confidence].
            Use empty array for no detections.

        Returns
        -------
        np.ndarray, shape (M, 5)
            Each row: [x1, y1, x2, y2, track_id].
        """
        self.frame_count += 1

        if detections is None or len(detections) == 0:
            detections = np.empty((0, 5))
        else:
            detections = np.atleast_2d(np.array(detections, dtype=float))

        # 1. Predict existing trackers' new positions
        predicted_boxes = []
        to_delete = []
        for i, trk in enumerate(self.trackers):
            pos = trk.predict()
            if np.any(np.isnan(pos)):
                to_delete.append(i)
            else:
                predicted_boxes.append(pos)
        for i in reversed(to_delete):
            self.trackers.pop(i)

        predicted_boxes = (
            np.array(predicted_boxes) if predicted_boxes else np.empty((0, 4))
        )

        # 2. Associate detections to trackers via IoU + Hungarian
        matched, unmatched_dets, unmatched_trks = self._associate(
            detections, predicted_boxes
        )

        # 3. Update matched trackers with assigned detections
        for det_idx, trk_idx in matched:
            self.trackers[trk_idx].update(detections[det_idx])

        # 4. Create new trackers for unmatched detections
        for det_idx in unmatched_dets:
            self.trackers.append(KalmanBoxTracker(detections[det_idx]))

        # 5. Remove dead trackers
        self.trackers = [
            t for t in self.trackers if t.time_since_update <= self.max_age
        ]

        # 6. Build output (only tracks that have been seen enough)
        results = []
        for trk in self.trackers:
            bbox = trk.get_state()
            if (
                trk.time_since_update < 1
                and (trk.hit_streak >= self.min_hits or self.frame_count <= self.min_hits)
            ):
                results.append(np.concatenate([bbox, [trk.id]]))

        return np.array(results) if results else np.empty((0, 5))

    # ---- internal ----------------------------------------------------------

    def _associate(self, detections, predicted_boxes):
        """Hungarian-based assignment using IoU cost matrix."""
        if len(predicted_boxes) == 0:
            return (
                np.empty((0, 2), dtype=int),
                np.arange(len(detections)),
                np.empty(0, dtype=int),
            )
        if len(detections) == 0:
            return (
                np.empty((0, 2), dtype=int),
                np.empty(0, dtype=int),
                np.arange(len(predicted_boxes)),
            )

        iou_matrix = iou_batch(detections[:, :4], predicted_boxes)

        # Solve with scipy (minimise → use negative IoU)
        row_indices, col_indices = linear_sum_assignment(-iou_matrix)

        matched = []
        unmatched_dets = list(range(len(detections)))
        unmatched_trks = list(range(len(predicted_boxes)))

        for r, c in zip(row_indices, col_indices):
            if iou_matrix[r, c] < self.iou_threshold:
                continue
            matched.append([r, c])
            if r in unmatched_dets:
                unmatched_dets.remove(r)
            if c in unmatched_trks:
                unmatched_trks.remove(c)

        return (
            np.array(matched) if matched else np.empty((0, 2), dtype=int),
            np.array(unmatched_dets, dtype=int),
            np.array(unmatched_trks, dtype=int),
        )
