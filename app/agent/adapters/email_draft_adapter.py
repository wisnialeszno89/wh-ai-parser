from __future__ import annotations

from dataclasses import dataclass
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path
import mimetypes
from typing import Iterable, Sequence

from app.agent.adapters.application_adapter import (
    AdapterDescriptor,
    ApplicationAdapter,
)


@dataclass(frozen=True)
class EmailDraftSummary:
    """Model-safe description of one local email draft."""

    path: str
    to: tuple[str, ...]
    cc: tuple[str, ...]
    bcc: tuple[str, ...]
    subject: str
    body: str
    attachments: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "path": self.path,
            "to": self.to,
            "cc": self.cc,
            "bcc": self.bcc,
            "subject": self.subject,
            "body": self.body,
            "attachments": self.attachments,
        }


class EmailDraftAdapter(ApplicationAdapter):
    """Semantic local email-draft adapter.

    The first email layer deliberately creates and reads .eml drafts only.
    It does not send network mail. Sending can later be attached to an
    explicit transport/connector with its own approval policy.
    """

    adapter_id = "email_draft"

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
                "At least one allowed email draft root is required."
            )

        self._roots = roots

    @property
    def descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            adapter_id=self.adapter_id,
            application="Email",
            capabilities=(
                "exists",
                "create_draft",
                "read_draft",
            ),
            description=(
                "Semantic creation and inspection of local .eml drafts "
                "inside explicitly allowed filesystem roots; sending is "
                "not performed by this adapter."
            ),
        )

    def is_available(self) -> bool:
        return all(
            root.exists() and root.is_dir()
            for root in self._roots
        )

    def exists(self, path: str | Path) -> bool:
        return self._resolve_for_access(path).exists()

    def create_draft(
        self,
        path: str | Path,
        *,
        to: Sequence[str],
        subject: str,
        body: str,
        cc: Sequence[str] = (),
        bcc: Sequence[str] = (),
        attachments: Sequence[str | Path] = (),
        overwrite: bool = False,
    ) -> EmailDraftSummary:
        draft_path = self._resolve_for_create(path)

        if draft_path.exists() and not overwrite:
            raise FileExistsError(str(draft_path))

        message = EmailMessage()
        message["To"] = self._join_addresses(to)
        if cc:
            message["Cc"] = self._join_addresses(cc)
        if bcc:
            message["Bcc"] = self._join_addresses(bcc)
        message["Subject"] = self._require_text(
            subject,
            "Email subject",
        )
        message.set_content(
            self._require_text(
                body,
                "Email body",
            )
        )

        attachment_names: list[str] = []

        for attachment in attachments:
            attachment_path = self._resolve_for_access(
                attachment
            )

            if not attachment_path.exists():
                raise FileNotFoundError(str(attachment_path))
            if not attachment_path.is_file():
                raise IsADirectoryError(str(attachment_path))

            data = attachment_path.read_bytes()
            mime_type, _ = mimetypes.guess_type(
                attachment_path.name
            )
            maintype, subtype = (
                mime_type.split("/", 1)
                if mime_type and "/" in mime_type
                else ("application", "octet-stream")
            )

            message.add_attachment(
                data,
                maintype=maintype,
                subtype=subtype,
                filename=attachment_path.name,
            )
            attachment_names.append(
                attachment_path.name
            )

        draft_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = draft_path.with_name(
            f".{draft_path.name}.agent-tmp.eml"
        )
        temporary.write_bytes(
            message.as_bytes(policy=policy.default)
        )
        temporary.replace(draft_path)

        return EmailDraftSummary(
            path=str(draft_path),
            to=self._split_addresses(message.get_all("To", [])),
            cc=self._split_addresses(message.get_all("Cc", [])),
            bcc=self._split_addresses(message.get_all("Bcc", [])),
            subject=str(message.get("Subject") or ""),
            body=str(message.get_body(preferencelist=("plain",)).get_content()),
            attachments=tuple(attachment_names),
        )

    def read_draft(
        self,
        path: str | Path,
    ) -> EmailDraftSummary:
        draft_path = self._resolve_for_existing(path)

        with draft_path.open("rb") as handle:
            message = BytesParser(
                policy=policy.default
            ).parse(handle)

        body_part = message.get_body(
            preferencelist=("plain",)
        )
        body = (
            body_part.get_content()
            if body_part is not None
            else ""
        )

        attachments = tuple(
            part.get_filename()
            for part in message.iter_attachments()
            if part.get_filename()
        )

        return EmailDraftSummary(
            path=str(draft_path),
            to=self._split_addresses(
                message.get_all("To", [])
            ),
            cc=self._split_addresses(
                message.get_all("Cc", [])
            ),
            bcc=self._split_addresses(
                message.get_all("Bcc", [])
            ),
            subject=str(message.get("Subject") or ""),
            body=str(body),
            attachments=attachments,
        )

    def _resolve_for_access(
        self,
        path: str | Path,
    ) -> Path:
        resolved = Path(path).expanduser().resolve(
            strict=False
        )
        self._assert_under_allowed_root(resolved)
        return resolved

    def _resolve_for_existing(
        self,
        path: str | Path,
    ) -> Path:
        resolved = self._resolve_for_access(path)

        if resolved.suffix.casefold() != ".eml":
            raise ValueError(
                "EmailDraftAdapter requires a .eml path."
            )
        if not resolved.exists():
            raise FileNotFoundError(str(resolved))
        if not resolved.is_file():
            raise IsADirectoryError(str(resolved))

        return resolved

    def _resolve_for_create(
        self,
        path: str | Path,
    ) -> Path:
        resolved = self._resolve_for_access(path)

        if resolved.suffix.casefold() != ".eml":
            raise ValueError(
                "EmailDraftAdapter requires a .eml path."
            )

        return resolved

    @staticmethod
    def _require_text(
        value: str,
        label: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{label} must not be empty."
            )
        return value

    @staticmethod
    def _join_addresses(
        addresses: Sequence[str],
    ) -> str:
        normalized = tuple(
            item.strip()
            for item in addresses
            if isinstance(item, str) and item.strip()
        )

        if not normalized:
            raise ValueError(
                "At least one email recipient is required."
            )

        return ", ".join(normalized)

    @staticmethod
    def _split_addresses(
        values,
    ) -> tuple[str, ...]:
        addresses: list[str] = []

        for value in values:
            if not isinstance(value, str):
                continue
            addresses.extend(
                item.strip()
                for item in value.split(",")
                if item.strip()
            )

        return tuple(addresses)

    def _assert_under_allowed_root(
        self,
        path: Path,
    ) -> None:
        for root in self._roots:
            try:
                path.relative_to(root)
                return
            except ValueError:
                continue

        raise PermissionError(
            f"Path '{path}' is outside all allowed email draft roots."
        )
