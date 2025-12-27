"""
Processador de jobs de correção.

Orquestra o fluxo completo: download → processamento → upload → atualização.
"""

import logging
import time
from datetime import datetime
from typing import List, Optional

from .image_processor import ImageProcessor
from .models import (
    AnswerKey,
    CorrectionItem,
    CorrectionJob,
    ErrorCode,
    JobStatus,
    ProcessedItem,
    Template,
)
from .supabase_client import SupabaseWorkerClient
from .xlsx_generator import XLSXGenerator

logger = logging.getLogger(__name__)


class JobProcessor:
    """Processador de jobs de correção."""
    
    def __init__(self, client: SupabaseWorkerClient):
        """
        Inicializa o processador.
        
        Args:
            client: Cliente Supabase para operações de banco e storage.
        """
        self.client = client
        self.xlsx_generator = XLSXGenerator()
    
    def process_job(self, job: CorrectionJob) -> bool:
        """
        Processa um job completo de correção.
        
        Fluxo:
        1. Busca template e gabarito
        2. Processa cada item (download → correção → upload)
        3. Gera e faz upload do XLSX
        4. Atualiza status do job
        
        Args:
            job: Job a ser processado.
            
        Returns:
            True se processado com sucesso, False caso contrário.
        """
        start_time = time.time()
        logger.info(f"Iniciando processamento do job {job.id}")
        
        try:
            # Busca template e gabarito
            template = self.client.get_template(job.template_id)
            answer_key = self.client.get_answer_key(job.answer_key_id)
            
            if not template:
                logger.error(f"Template {job.template_id} não encontrado")
                self._mark_job_failed(job.id, "Template não encontrado")
                return False
            
            if not answer_key:
                logger.error(f"Gabarito {job.answer_key_id} não encontrado")
                self._mark_job_failed(job.id, "Gabarito não encontrado")
                return False
            
            # Busca itens do job
            items = self.client.get_job_items(job.id)
            
            if not items:
                logger.error(f"Nenhum item encontrado para o job {job.id}")
                self._mark_job_failed(job.id, "Nenhum item para processar")
                return False
            
            # Inicializa processador de imagem
            image_processor = ImageProcessor(template)
            
            # Processa cada item
            processed_items: List[ProcessedItem] = []
            success_count = 0
            error_count = 0
            
            for item in items:
                logger.info(f"Processando item {item.index + 1}/{len(items)}: {item.id}")
                
                processed_item = self._process_item(
                    item=item,
                    job=job,
                    template=template,
                    answer_key=answer_key,
                    image_processor=image_processor
                )
                
                processed_items.append(processed_item)
                
                if processed_item.success:
                    success_count += 1
                else:
                    error_count += 1
                
                # Atualiza progresso
                self.client.update_job_status(
                    job_id=job.id,
                    status=JobStatus.PROCESSING,
                    success_items=success_count,
                    error_items=error_count
                )
                
                # Broadcast de progresso (via Realtime)
                self.client.broadcast_job_update(
                    job_id=job.id,
                    status=JobStatus.PROCESSING,
                    success_items=success_count,
                    error_items=error_count
                )
            
            # Gera XLSX com resultados
            xlsx_path = self._generate_and_upload_xlsx(
                job=job,
                processed_items=processed_items,
                answer_key=answer_key
            )
            
            # Calcula tempo decorrido
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            # Atualiza job como concluído
            final_status = JobStatus.DONE if error_count < len(items) else JobStatus.FAILED
            
            self.client.update_job_status(
                job_id=job.id,
                status=final_status,
                finished_at=datetime.utcnow(),
                elapsed_ms=elapsed_ms,
                xlsx_storage_path=xlsx_path,
                success_items=success_count,
                error_items=error_count
            )
            
            # Broadcast final
            self.client.broadcast_job_update(
                job_id=job.id,
                status=final_status,
                success_items=success_count,
                error_items=error_count
            )
            
            logger.info(
                f"Job {job.id} concluído: {success_count} OK, {error_count} erros, "
                f"{elapsed_ms}ms"
            )
            
            return final_status == JobStatus.DONE
            
        except Exception as e:
            logger.error(f"Erro fatal no processamento do job {job.id}: {e}")
            self._mark_job_failed(job.id, str(e))
            return False
    
    def _process_item(
        self,
        item: CorrectionItem,
        job: CorrectionJob,
        template: Template,
        answer_key: AnswerKey,
        image_processor: ImageProcessor
    ) -> ProcessedItem:
        """
        Processa um item individual.
        
        Args:
            item: Item a ser processado.
            job: Job pai.
            template: Template de folha de resposta.
            answer_key: Gabarito.
            image_processor: Processador de imagem.
            
        Returns:
            ProcessedItem com resultados.
        """
        try:
            # Download da imagem
            image_bytes = self._download_image(item.original_storage_path)
            
            if not image_bytes:
                return self._create_error_item(
                    item.id,
                    template.question_count,
                    ErrorCode.STORAGE_DOWNLOAD_FAILED,
                    "Falha ao baixar imagem"
                )
            
            # Processa a imagem
            processed_item, marked_image_bytes = image_processor.process(
                image_bytes=image_bytes,
                answers_string=answer_key.answers_string
            )
            
            # Atualiza item_id
            processed_item.item_id = item.id
            
            if not processed_item.success:
                # Atualiza item no banco com erro
                self.client.update_item_result(
                    item_id=item.id,
                    identifier=processed_item.identifier,
                    error_code=processed_item.error_code,
                    error_message=processed_item.error_message
                )
                return processed_item
            
            # Upload da imagem marcada
            marked_path = None
            if marked_image_bytes:
                marked_path = self._upload_marked_image(
                    job=job,
                    item=item,
                    image_bytes=marked_image_bytes
                )
                
                if not marked_path:
                    return self._create_error_item(
                        item.id,
                        template.question_count,
                        ErrorCode.STORAGE_UPLOAD_FAILED,
                        "Falha ao fazer upload da imagem marcada"
                    )
            
            processed_item.marked_image_path = marked_path or ""
            
            # Atualiza item no banco
            self.client.update_item_result(
                item_id=item.id,
                marked_storage_path=marked_path,
                identifier=processed_item.identifier,
                detected_answers=processed_item.detected_answers,
                correct_count=processed_item.correct_count
            )
            
            return processed_item
            
        except Exception as e:
            logger.error(f"Erro ao processar item {item.id}: {e}")
            return self._create_error_item(
                item.id,
                template.question_count,
                ErrorCode.UNKNOWN_ERROR,
                str(e)
            )
    
    def _download_image(self, storage_path: str) -> Optional[bytes]:
        """
        Faz download de uma imagem do Storage.
        
        Args:
            storage_path: Caminho no formato "bucket/path/to/file".
            
        Returns:
            Bytes da imagem ou None se falhar.
        """
        try:
            from .security import SecurityError, validate_storage_path
            
            # Validate and parse storage path securely
            try:
                bucket, path = validate_storage_path(storage_path)
            except SecurityError as e:
                logger.error(f"Security violation in storage path {storage_path}: {e}")
                return None
            
            return self.client.download_file(bucket, path)
        except Exception as e:
            logger.error(f"Erro ao baixar imagem {storage_path}: {e}")
            return None
    
    def _upload_marked_image(
        self,
        job: CorrectionJob,
        item: CorrectionItem,
        image_bytes: bytes
    ) -> Optional[str]:
        """
        Faz upload da imagem marcada para o Storage.
        
        Args:
            job: Job de correção.
            item: Item processado.
            image_bytes: Bytes da imagem marcada.
            
        Returns:
            Caminho no Storage ou None se falhar.
        """
        try:
            from .security import SecurityError, create_secure_path
            
            # Create secure path with validation
            try:
                filename = f"marked_{item.index:04d}.jpg"
                secure_path = create_secure_path(job.owner_user_id, job.id, filename)
            except SecurityError as e:
                logger.error(f"Security violation creating path for job {job.id}: {e}")
                return None
            
            self.client.upload_file(
                bucket="results",
                path=secure_path,
                data=image_bytes,
                content_type="image/jpeg"
            )
            
            return f"results/{secure_path}"
        except Exception as e:
            logger.error(f"Erro ao fazer upload da imagem marcada: {e}")
            return None
    
    def _generate_and_upload_xlsx(
        self,
        job: CorrectionJob,
        processed_items: List[ProcessedItem],
        answer_key: AnswerKey
    ) -> Optional[str]:
        """
        Gera e faz upload do relatório XLSX.
        
        Args:
            job: Job de correção.
            processed_items: Lista de itens processados.
            answer_key: Gabarito usado.
            
        Returns:
            Caminho no Storage ou None se falhar.
        """
        try:
            # Gera XLSX
            xlsx_bytes = self.xlsx_generator.generate(
                items=processed_items,
                answer_key=answer_key,
                job_id=job.id,
                job_created_at=job.created_at
            )
            
            # Upload
            path = f"{job.owner_user_id}/{job.id}/results.xlsx"
            
            self.client.upload_file(
                bucket="results",
                path=path,
                data=xlsx_bytes,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            return f"results/{path}"
        except Exception as e:
            logger.error(f"Erro ao gerar/fazer upload do XLSX: {e}")
            return None
    
    def _mark_job_failed(self, job_id: str, error_message: str) -> None:
        """
        Marca um job como falho.
        
        Args:
            job_id: ID do job.
            error_message: Mensagem de erro.
        """
        try:
            self.client.update_job_status(
                job_id=job_id,
                status=JobStatus.FAILED,
                finished_at=datetime.utcnow()
            )
            
            self.client.broadcast_job_update(
                job_id=job_id,
                status=JobStatus.FAILED,
                success_items=0,
                error_items=0
            )
        except Exception as e:
            logger.error(f"Erro ao marcar job {job_id} como falho: {e}")
    
    def _create_error_item(
        self,
        item_id: str,
        total_questions: int,
        error_code: ErrorCode,
        error_message: str
    ) -> ProcessedItem:
        """
        Cria um ProcessedItem com erro.
        
        Args:
            item_id: ID do item.
            total_questions: Total de questões.
            error_code: Código de erro.
            error_message: Mensagem de erro.
            
        Returns:
            ProcessedItem com erro.
        """
        return ProcessedItem(
            item_id=item_id,
            identifier=None,
            detected_answers="",
            correct_count=0,
            total_questions=total_questions,
            marked_image_path="",
            success=False,
            error_code=error_code.value,
            error_message=error_message
        )
