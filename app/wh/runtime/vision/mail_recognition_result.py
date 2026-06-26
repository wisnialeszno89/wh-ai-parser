from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.mail_metadata import (
    MailMetadata
)


@dataclass
class MailRecognitionResult:

    metadata: MailMetadata

    subject: str

    body: str