"""Local JSON persistence for approved NaviMind experience episodes."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from app.agent.experience.experience_models import ExperienceEpisode


class ExperienceStore:
    """Persist only operator-approved episodes in isolated scope files."""

    MAX_EPISODES_PER_SCOPE = 500

    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir).expanduser()

    @staticmethod
    def _scope_digest(
        tenant_id: str,
        operator_id: str,
        application_id: str,
    ) -> str:
        normalized = "\0".join(
            value.strip().casefold()
            for value in (tenant_id, operator_id, application_id)
        )
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _path_for(
        self,
        tenant_id: str,
        operator_id: str,
        application_id: str,
    ) -> Path:
        digest = self._scope_digest(tenant_id, operator_id, application_id)
        return self.root_dir / f"{digest}.json"

    def list_approved(
        self,
        *,
        tenant_id: str,
        operator_id: str,
        application_id: str,
    ) -> tuple[ExperienceEpisode, ...]:
        path = self._path_for(tenant_id, operator_id, application_id)
        if not path.exists():
            return ()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("experience_store_read_failed") from exc
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise RuntimeError("experience_store_schema_invalid")
        records = payload.get("episodes")
        if not isinstance(records, list):
            raise RuntimeError("experience_store_records_invalid")

        episodes = []
        for record in records:
            try:
                episode = ExperienceEpisode.from_storage_dict(record)
            except (TypeError, ValueError) as exc:
                raise RuntimeError("experience_store_record_invalid") from exc
            if (
                episode.approved_by_operator
                and episode.tenant_id == tenant_id.strip().casefold()
                and episode.operator_id == operator_id.strip().casefold()
                and episode.application_id == application_id.strip().casefold()
            ):
                episodes.append(episode)
        return tuple(episodes)

    def save_approved(self, episode: ExperienceEpisode) -> ExperienceEpisode:
        if not isinstance(episode, ExperienceEpisode):
            raise TypeError("experience_episode_invalid")
        if not episode.approved_by_operator:
            raise ValueError("experience_episode_requires_operator_approval")

        path = self._path_for(
            episode.tenant_id,
            episode.operator_id,
            episode.application_id,
        )
        self.root_dir.mkdir(parents=True, exist_ok=True)
        existing = list(
            self.list_approved(
                tenant_id=episode.tenant_id,
                operator_id=episode.operator_id,
                application_id=episode.application_id,
            )
        )
        if any(item.episode_id == episode.episode_id for item in existing):
            raise ValueError("experience_episode_duplicate")
        existing.append(episode)
        existing = existing[-self.MAX_EPISODES_PER_SCOPE :]

        payload = {
            "schema_version": 1,
            "episodes": [item.to_storage_dict() for item in existing],
        }
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=self.root_dir,
                prefix=f".{path.stem}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                temporary_path = Path(handle.name)
            os.replace(temporary_path, path)
        except OSError as exc:
            raise RuntimeError("experience_store_write_failed") from exc
        finally:
            if temporary_path is not None and temporary_path.exists():
                try:
                    temporary_path.unlink()
                except OSError:
                    pass
        return episode
