"""
Modelos de dados do Worker.

Define as estruturas de dados usadas pelo worker para processamento.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class JobStatus(Enum):
    """Status de um job de correção."""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class ErrorCode(Enum):
    """Códigos de erro para processamento de itens."""
    ALIGN_TRIANGLES_NOT_FOUND = "ALIGN_TRIANGLES_NOT_FOUND"
    QR_DECODE_FAILED = "QR_DECODE_FAILED"
    MARK_DETECTION_FAILED = "MARK_DETECTION_FAILED"
    STORAGE_DOWNLOAD_FAILED = "STORAGE_DOWNLOAD_FAILED"
    STORAGE_UPLOAD_FAILED = "STORAGE_UPLOAD_FAILED"
    TEMPLATE_MISMATCH = "TEMPLATE_MISMATCH"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class Template:
    """Modelo de template de folha de resposta."""
    id: str
    name: str
    question_count: int
    alternatives_count: int
    version: int
    template_storage_path: str
    is_active: bool


@dataclass
class AnswerKey:
    """Gabarito com respostas corretas."""
    id: str
    owner_user_id: str
    template_id: str
    answers_string: str


@dataclass
class CorrectionJob:
    """Job de correção."""
    id: str
    owner_user_id: str
    institution_id: Optional[str]
    answer_key_id: str
    template_id: str
    status: JobStatus
    total_items: int
    success_items: int
    error_items: int
    elapsed_ms: Optional[int]
    xlsx_storage_path: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


@dataclass
class CorrectionItem:
    """Item individual de correção (uma folha de resposta)."""
    id: str
    job_id: str
    index: int
    original_storage_path: str
    marked_storage_path: Optional[str] = None
    identifier: Optional[str] = None
    detected_answers: Optional[str] = None
    correct_count: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ProcessedItem:
    """Resultado do processamento de um item."""
    item_id: str
    identifier: Optional[str]
    detected_answers: str
    correct_count: int
    total_questions: int
    marked_image_path: str
    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class QueueMessage:
    """Mensagem da fila de correções."""
    msg_id: int
    read_ct: int
    enqueued_at: datetime
    vt: datetime
    job_id: str
