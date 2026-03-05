"""
Public SORT Tracker API.
Thin wrapper around SortAlgorithm that returns structured dicts
suitable for the behavior analysis engine.
"""

import numpy as np
from tracking.sort_algorithm import SortAlgorithm


class SortTracker:
    """
    High-level SORT tracker.

    Parameters
    ----------
    max_age       : int   – frames before a lost track is removed (default 30).
    min_hits      : int   – minimum consecutive hits to start reporting (default 3).
    iou_threshold : float – IoU threshold for data association (default 0.3).
    """

    def __init__(self, max_age=30, min_hits=3, iou_threshold=0.3):
        self.sort = SortAlgorithm(
            max_age=max_age,
            min_hits=min_hits,
            iou_threshold=iou_threshold,
        )

    def update(self, detections):
        """
        Parameters
        ----------
        detections : list[list[float]]
            Each element: [x1, y1, x2, y2, confidence].

        Returns
        -------
        list[dict]
            Each dict: {"id": int, "bbox": [x1, y1, x2, y2]}.
        """
        if detections is None or len(detections) == 0:
            raw = self.sort.update(np.empty((0, 5)))
        else:
            raw = self.sort.update(np.array(detections, dtype=float))

        tracked_objects = []
        for row in raw:
            tracked_objects.append({
                "id": int(row[4]),
                "bbox": [float(row[0]), float(row[1]), float(row[2]), float(row[3])],
            })
        return tracked_objects
