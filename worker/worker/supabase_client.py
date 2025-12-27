"""
Cliente Supabase para o Worker.

Encapsula operações de banco de dados, storage e fila.
"""

import logging
from datetime import datetime
from typing import Any, List, Optional

from supabase import Client, create_client

from .config import WorkerConfig
from .models import (
    AnswerKey,
    CorrectionItem,
    CorrectionJob,
    JobStatus,
    QueueMessage,
    Template,
)

logger = logging.getLogger(__name__)


class SupabaseWorkerClient:
    """Cliente Supabase para operações do worker."""
    
    def __init__(self, config: WorkerConfig):
        """
        Inicializa o cliente Supabase.
        
        Args:
            config: Configuração do worker com URL e service role key.
        """
        self.config = config
        self.client: Client = create_client(
            config.supabase_url,
            config.supabase_service_role_key
        )
    
    # =========================================================================
    # Queue Operations
    # =========================================================================
    
    def read_queue_message(self) -> Optional[QueueMessage]:
        """
        Lê uma mensagem da fila de correções.
        
        Returns:
            QueueMessage se houver mensagem disponível, None caso contrário.
        """
        try:
            result = self.client.rpc(
                "pgmq_read",
                {
                    "queue_name": self.config.queue_name,
                    "vt": self.config.visibility_timeout,
                    "qty": 1
                }
            ).execute()
            
            if result.data and len(result.data) > 0:
                msg = result.data[0]
                return QueueMessage(
                    msg_id=msg["msg_id"],
                    read_ct=msg["read_ct"],
                    enqueued_at=datetime.fromisoformat(msg["enqueued_at"].replace("Z", "+00:00")),
                    vt=datetime.fromisoformat(msg["vt"].replace("Z", "+00:00")),
                    job_id=msg["message"]["job_id"]
                )
            return None
        except Exception as e:
            logger.error(f"Erro ao ler mensagem da fila: {e}")
            raise
    
    def delete_queue_message(self, msg_id: int) -> bool:
        """
        Remove uma mensagem da fila após processamento bem-sucedido.
        
        Args:
            msg_id: ID da mensagem a ser removida.
            
        Returns:
            True se removida com sucesso.
        """
        try:
            result = self.client.rpc(
                "pgmq_delete",
                {
                    "queue_name": self.config.queue_name,
                    "msg_id": msg_id
                }
            ).execute()
            return result.data is True
        except Exception as e:
            logger.error(f"Erro ao deletar mensagem {msg_id}: {e}")
            raise
    
    def archive_queue_message(self, msg_id: int) -> bool:
        """
        Arquiva uma mensagem da fila (para histórico).
        
        Args:
            msg_id: ID da mensagem a ser arquivada.
            
        Returns:
            True se arquivada com sucesso.
        """
        try:
            result = self.client.rpc(
                "pgmq_archive",
                {
                    "queue_name": self.config.queue_name,
                    "msg_id": msg_id
                }
            ).execute()
            return result.data is True
        except Exception as e:
            logger.error(f"Erro ao arquivar mensagem {msg_id}: {e}")
            raise
    
    # =========================================================================
    # Job Operations
    # =========================================================================
    
    def get_job(self, job_id: str) -> Optional[CorrectionJob]:
        """
        Busca um job de correção pelo ID.
        
        Args:
            job_id: ID do job.
            
        Returns:
            CorrectionJob se encontrado, None caso contrário.
        """
        try:
            result = self.client.table("correction_jobs").select("*").eq("id", job_id).single().execute()
            
            if result.data:
                data = result.data
                return CorrectionJob(
                    id=data["id"],
                    owner_user_id=data["owner_user_id"],
                    institution_id=data.get("institution_id"),
                    answer_key_id=data["answer_key_id"],
                    template_id=data["template_id"],
                    status=JobStatus(data["status"]),
                    total_items=data["total_items"],
                    success_items=data["success_items"],
                    error_items=data["error_items"],
                    elapsed_ms=data.get("elapsed_ms"),
                    xlsx_storage_path=data.get("xlsx_storage_path"),
                    created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                    started_at=datetime.fromisoformat(data["started_at"].replace("Z", "+00:00")) if data.get("started_at") else None,
                    finished_at=datetime.fromisoformat(data["finished_at"].replace("Z", "+00:00")) if data.get("finished_at") else None,
                )
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar job {job_id}: {e}")
            raise
    
    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        elapsed_ms: Optional[int] = None,
        xlsx_storage_path: Optional[str] = None,
        success_items: Optional[int] = None,
        error_items: Optional[int] = None,
    ) -> bool:
        """
        Atualiza o status de um job.
        
        Args:
            job_id: ID do job.
            status: Novo status.
            started_at: Timestamp de início (opcional).
            finished_at: Timestamp de fim (opcional).
            elapsed_ms: Tempo decorrido em ms (opcional).
            xlsx_storage_path: Caminho do XLSX gerado (opcional).
            success_items: Número de itens processados com sucesso (opcional).
            error_items: Número de itens com erro (opcional).
            
        Returns:
            True se atualizado com sucesso.
        """
        try:
            update_data: dict[str, Any] = {"status": status.value}
            
            if started_at is not None:
                update_data["started_at"] = started_at.isoformat()
            if finished_at is not None:
                update_data["finished_at"] = finished_at.isoformat()
            if elapsed_ms is not None:
                update_data["elapsed_ms"] = elapsed_ms
            if xlsx_storage_path is not None:
                update_data["xlsx_storage_path"] = xlsx_storage_path
            if success_items is not None:
                update_data["success_items"] = success_items
            if error_items is not None:
                update_data["error_items"] = error_items
            
            self.client.table("correction_jobs").update(update_data).eq("id", job_id).execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar job {job_id}: {e}")
            raise
    
    # =========================================================================
    # Item Operations
    # =========================================================================
    
    def get_job_items(self, job_id: str) -> List[CorrectionItem]:
        """
        Busca todos os itens de um job.
        
        Args:
            job_id: ID do job.
            
        Returns:
            Lista de CorrectionItem.
        """
        try:
            result = self.client.table("correction_items").select("*").eq("job_id", job_id).order("index").execute()
            
            items = []
            for data in result.data:
                items.append(CorrectionItem(
                    id=data["id"],
                    job_id=data["job_id"],
                    index=data["index"],
                    original_storage_path=data["original_storage_path"],
                    marked_storage_path=data.get("marked_storage_path"),
                    identifier=data.get("identifier"),
                    detected_answers=data.get("detected_answers"),
                    correct_count=data.get("correct_count"),
                    error_code=data.get("error_code"),
                    error_message=data.get("error_message"),
                ))
            return items
        except Exception as e:
            logger.error(f"Erro ao buscar itens do job {job_id}: {e}")
            raise
    
    def update_item_result(
        self,
        item_id: str,
        marked_storage_path: Optional[str] = None,
        identifier: Optional[str] = None,
        detected_answers: Optional[str] = None,
        correct_count: Optional[int] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Atualiza o resultado de um item processado.
        
        Args:
            item_id: ID do item.
            marked_storage_path: Caminho da imagem marcada.
            identifier: Identificador lido (QR code).
            detected_answers: Respostas detectadas.
            correct_count: Número de acertos.
            error_code: Código de erro (se houver).
            error_message: Mensagem de erro (se houver).
            
        Returns:
            True se atualizado com sucesso.
        """
        try:
            update_data: dict[str, Any] = {}
            
            if marked_storage_path is not None:
                update_data["marked_storage_path"] = marked_storage_path
            if identifier is not None:
                update_data["identifier"] = identifier
            if detected_answers is not None:
                update_data["detected_answers"] = detected_answers
            if correct_count is not None:
                update_data["correct_count"] = correct_count
            if error_code is not None:
                update_data["error_code"] = error_code
            if error_message is not None:
                update_data["error_message"] = error_message
            
            self.client.table("correction_items").update(update_data).eq("id", item_id).execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar item {item_id}: {e}")
            raise
    
    # =========================================================================
    # Template & Answer Key Operations
    # =========================================================================
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """
        Busca um template pelo ID.
        
        Args:
            template_id: ID do template.
            
        Returns:
            Template se encontrado, None caso contrário.
        """
        try:
            result = self.client.table("templates").select("*").eq("id", template_id).single().execute()
            
            if result.data:
                data = result.data
                return Template(
                    id=data["id"],
                    name=data["name"],
                    question_count=data["question_count"],
                    alternatives_count=data["alternatives_count"],
                    version=data["version"],
                    template_storage_path=data["template_storage_path"],
                    is_active=data["is_active"],
                )
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar template {template_id}: {e}")
            raise
    
    def get_answer_key(self, answer_key_id: str) -> Optional[AnswerKey]:
        """
        Busca um gabarito pelo ID.
        
        Args:
            answer_key_id: ID do gabarito.
            
        Returns:
            AnswerKey se encontrado, None caso contrário.
        """
        try:
            result = self.client.table("answer_keys").select("*").eq("id", answer_key_id).single().execute()
            
            if result.data:
                data = result.data
                return AnswerKey(
                    id=data["id"],
                    owner_user_id=data["owner_user_id"],
                    template_id=data["template_id"],
                    answers_string=data["answers_string"],
                )
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar gabarito {answer_key_id}: {e}")
            raise
    
    # =========================================================================
    # Storage Operations
    # =========================================================================
    
    def download_file(self, bucket: str, path: str) -> bytes:
        """
        Faz download de um arquivo do Storage.
        
        Args:
            bucket: Nome do bucket.
            path: Caminho do arquivo no bucket.
            
        Returns:
            Conteúdo do arquivo em bytes.
        """
        try:
            from .security import SecurityError, validate_bucket_name
            
            # Validate bucket name
            if not validate_bucket_name(bucket):
                raise SecurityError(f"Invalid bucket name: {bucket}")
            
            # Validate path doesn't contain traversal sequences
            if '..' in path or path.startswith('/') or '\\' in path:
                raise SecurityError(f"Invalid path: {path}")
            
            response = self.client.storage.from_(bucket).download(path)
            return response
        except Exception as e:
            logger.error(f"Erro ao baixar arquivo {bucket}/{path}: {e}")
            raise
    
    def upload_file(self, bucket: str, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """
        Faz upload de um arquivo para o Storage.
        
        Args:
            bucket: Nome do bucket.
            path: Caminho de destino no bucket.
            data: Conteúdo do arquivo em bytes.
            content_type: Tipo MIME do arquivo.
            
        Returns:
            Caminho do arquivo no storage.
        """
        try:
            from .security import SecurityError, validate_bucket_name
            
            # Validate bucket name
            if not validate_bucket_name(bucket):
                raise SecurityError(f"Invalid bucket name: {bucket}")
            
            # Validate path doesn't contain traversal sequences
            if '..' in path or path.startswith('/') or '\\' in path:
                raise SecurityError(f"Invalid path: {path}")
            
            # Validate content type
            allowed_types = {
                'image/jpeg', 'image/png', 'image/webp', 'image/tiff',
                'application/pdf', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            if content_type not in allowed_types:
                raise SecurityError(f"Invalid content type: {content_type}")
            
            self.client.storage.from_(bucket).upload(
                path,
                data,
                file_options={"content-type": content_type}
            )
            return path
        except Exception as e:
            logger.error(f"Erro ao fazer upload para {bucket}/{path}: {e}")
            raise
    
    # =========================================================================
    # Realtime Broadcast
    # =========================================================================
    
    def broadcast_job_update(self, job_id: str, status: JobStatus, success_items: int, error_items: int) -> None:
        """
        Envia atualização de job via Realtime broadcast.
        
        Args:
            job_id: ID do job.
            status: Status atual.
            success_items: Itens processados com sucesso.
            error_items: Itens com erro.
        """
        # Nota: O broadcast é feito automaticamente pelo Supabase Realtime
        # quando atualizamos a tabela correction_jobs, desde que o cliente
        # frontend esteja inscrito nas mudanças da tabela.
        # Esta função é um placeholder para broadcast manual se necessário.
        logger.debug(f"Job {job_id} atualizado: status={status.value}, success={success_items}, errors={error_items}")
