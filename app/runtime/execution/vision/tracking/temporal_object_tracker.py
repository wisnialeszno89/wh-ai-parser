from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)
from app.runtime.execution.vision.models.vision_object_observation import (
    VisionObjectObservation,
)


class TemporalObjectTracker:
    def __init__(
        self,
        match_iou_threshold: float = 0.5,
        max_missing_frames: int = 3,
    ) -> None:
        self.match_iou_threshold = match_iou_threshold
        self.max_missing_frames = max_missing_frames

        self._tracks: list[TrackedObject] = []
        self._next_track_number = 1
        self._frame_index = 0

    def update(
        self,
        observations: list[
            LogicalObject | VisionObjectObservation
        ],
    ) -> list[TrackedObject]:
        self._frame_index += 1

        if not self._tracks:
            for observation in observations:
                self._tracks.append(
                    self._create_track(observation)
                )

            return list(self._tracks)

        matched_track_indices: set[int] = set()
        updated_tracks: list[TrackedObject] = []

        for observation in observations:
            logical_object = self._logical_object(observation)

            best_track_index: int | None = None
            best_iou = 0.0

            for index, track in enumerate(self._tracks):
                if index in matched_track_indices:
                    continue

                if track.status is TrackedObjectStatus.LOST:
                    continue

                iou = self._calculate_iou(
                    track.object,
                    logical_object,
                )

                if (
                    iou >= self.match_iou_threshold
                    and iou > best_iou
                ):
                    best_iou = iou
                    best_track_index = index

            if best_track_index is None:
                updated_tracks.append(
                    self._create_track(observation)
                )
                continue

            matched_track_indices.add(best_track_index)

            track = self._tracks[best_track_index]
            previous_object = track.object

            moved = (
                previous_object.bounds.x
                != logical_object.bounds.x
                or previous_object.bounds.y
                != logical_object.bounds.y
            )

            track.object = logical_object
            self._apply_semantics(track, observation)

            track.last_seen = self._frame_index
            track.observation_count += 1
            track.consecutive_observations += 1
            track.consecutive_missed_frames = 0

            track.status = (
                TrackedObjectStatus.MOVED
                if moved
                else TrackedObjectStatus.STABLE
            )

            track.stability = best_iou

            updated_tracks.append(track)

        for index, track in enumerate(self._tracks):
            if index in matched_track_indices:
                continue

            track.consecutive_missed_frames += 1
            track.consecutive_observations = 0

            if (
                track.consecutive_missed_frames
                >= self.max_missing_frames
            ):
                track.status = TrackedObjectStatus.LOST

            updated_tracks.append(track)

        self._tracks = updated_tracks

        return list(self._tracks)

    def _create_track(
        self,
        observation: LogicalObject | VisionObjectObservation,
    ) -> TrackedObject:
        logical_object = self._logical_object(observation)

        track = TrackedObject(
            id=f"TO-{self._next_track_number:04d}",
            object=logical_object,
            first_seen=self._frame_index,
            last_seen=self._frame_index,
            observation_count=1,
            consecutive_observations=1,
            consecutive_missed_frames=0,
            status=TrackedObjectStatus.NEW,
            stability=1.0,
        )

        self._apply_semantics(track, observation)

        self._next_track_number += 1

        return track

    @staticmethod
    def _logical_object(
        observation: LogicalObject | VisionObjectObservation,
    ) -> LogicalObject:
        if isinstance(observation, VisionObjectObservation):
            return observation.logical_object

        return observation

    @staticmethod
    def _apply_semantics(
        track: TrackedObject,
        observation: LogicalObject | VisionObjectObservation,
    ) -> None:
        if not isinstance(observation, VisionObjectObservation):
            return

        track.control_type = observation.control_type
        track.confidence = observation.confidence

    @staticmethod
    def _calculate_iou(
        first: LogicalObject,
        second: LogicalObject,
    ) -> float:
        a = first.bounds
        b = second.bounds

        intersection_left = max(a.left, b.left)
        intersection_top = max(a.top, b.top)
        intersection_right = min(a.right, b.right)
        intersection_bottom = min(a.bottom, b.bottom)

        intersection_width = max(
            0,
            intersection_right - intersection_left,
        )
        intersection_height = max(
            0,
            intersection_bottom - intersection_top,
        )

        intersection_area = (
            intersection_width * intersection_height
        )

        if intersection_area <= 0:
            return 0.0

        union_area = (
            a.area
            + b.area
            - intersection_area
        )

        if union_area <= 0:
            return 0.0

        return intersection_area / union_area
