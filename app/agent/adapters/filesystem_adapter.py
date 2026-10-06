from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from shutil import copy2, move
from typing import Iterable


@dataclass(frozen=True)
class FileEntry:
    path: str
    name: str
    is_file: bool
    is_directory: bool
    size_bytes: int | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "path": self.path,
            "name": self.name,
            "is_file": self.is_file,
            "is_directory": self.is_directory,
            "size_bytes": self.size_bytes,
        }


class FileSystemAdapter:
    """
    Semantic filesystem adapter with explicit allowed roots.

    The adapter exposes business-level file operations without depending on a
    desktop UI. Every path is resolved and checked against the configured
    roots before access. Destructive deletion is intentionally not part of
    this first contract.
    """

    adapter_id = "filesystem"

    def __init__(
        self,
        *,
        allowed_roots: Iterable[str | Path],
    ) -> None:
        roots = tuple(
            Path(root).expanduser().resolve()
            for root in allowed_roots
        )

        if not roots:
            raise ValueError(
                "At least one allowed filesystem root is required."
            )

        self._roots = roots

    @property
    def descriptor(self):
        from app.agent.adapters.application_adapter import AdapterDescriptor

        return AdapterDescriptor(
            adapter_id=self.adapter_id,
            application="FileSystem",
            capabilities=(
                "list",
                "read",
                "write",
                "copy",
                "move",
                "exists",
            ),
            description=(
                "Semantic access to files and folders inside explicitly "
                "allowed roots."
            ),
        )

    def is_available(self) -> bool:
        return all(root.exists() and root.is_dir() for root in self._roots)

    @property
    def allowed_roots(self) -> tuple[Path, ...]:
        return self._roots

    def exists(self, path: str | Path) -> bool:
        return self._resolve_for_access(path).exists()

    def list(
        self,
        directory: str | Path,
    ) -> tuple[FileEntry, ...]:
        directory_path = self._resolve_for_access(directory)

        if not directory_path.exists():
            raise FileNotFoundError(str(directory_path))
        if not directory_path.is_dir():
            raise NotADirectoryError(str(directory_path))

        entries: list[FileEntry] = []

        for child in sorted(
            directory_path.iterdir(),
            key=lambda item: item.name.casefold(),
        ):
            entries.append(
                FileEntry(
                    path=str(child),
                    name=child.name,
                    is_file=child.is_file(),
                    is_directory=child.is_dir(),
                    size_bytes=(
                        child.stat().st_size
                        if child.is_file()
                        else None
                    ),
                )
            )

        return tuple(entries)

    def read_text(
        self,
        path: str | Path,
        *,
        encoding: str = "utf-8",
    ) -> str:
        file_path = self._resolve_for_access(path)

        if not file_path.exists():
            raise FileNotFoundError(str(file_path))
        if not file_path.is_file():
            raise IsADirectoryError(str(file_path))

        return file_path.read_text(encoding=encoding)

    def write_text(
        self,
        path: str | Path,
        content: str,
        *,
        encoding: str = "utf-8",
        overwrite: bool = False,
    ) -> Path:
        file_path = self._resolve_for_create(path)

        if file_path.exists() and not overwrite:
            raise FileExistsError(str(file_path))

        file_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = file_path.with_name(
            f".{file_path.name}.agent-tmp"
        )
        temporary.write_text(
            content,
            encoding=encoding,
        )
        temporary.replace(file_path)

        return file_path

    def copy(
        self,
        source: str | Path,
        destination: str | Path,
        *,
        overwrite: bool = False,
    ) -> Path:
        source_path = self._resolve_for_access(source)
        destination_path = self._resolve_for_create(destination)

        if not source_path.is_file():
            raise ValueError(
                "Filesystem copy currently supports files only."
            )

        if destination_path.exists() and not overwrite:
            raise FileExistsError(str(destination_path))

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        copy2(
            source_path,
            destination_path,
        )
        return destination_path

    def move(
        self,
        source: str | Path,
        destination: str | Path,
        *,
        overwrite: bool = False,
    ) -> Path:
        source_path = self._resolve_for_access(source)
        destination_path = self._resolve_for_create(destination)

        if destination_path.exists() and not overwrite:
            raise FileExistsError(str(destination_path))

        destination_path.parent.mkdir(parents=True, exist_ok=True)

        if overwrite:
            destination_path.unlink()

        moved = move(
            str(source_path),
            str(destination_path),
        )
        return Path(moved).resolve()

    def _resolve_for_access(self, path: str | Path) -> Path:
        resolved = Path(path).expanduser().resolve(strict=False)

        if not resolved.exists() and self._root_match_is_required(path):
            self._assert_under_allowed_root(resolved)
        else:
            self._assert_under_allowed_root(resolved)

        return resolved

    def _resolve_for_create(self, path: str | Path) -> Path:
        resolved = Path(path).expanduser().resolve(strict=False)
        self._assert_under_allowed_root(resolved)
        return resolved

    @staticmethod
    def _root_match_is_required(path: str | Path) -> bool:
        del path
        return True

    def _assert_under_allowed_root(self, path: Path) -> None:
        for root in self._roots:
            try:
                path.relative_to(root)
                return
            except ValueError:
                continue

        raise PermissionError(
            f"Path '{path}' is outside all allowed filesystem roots."
        )
