"""
Consumidor de fila para processamento de jobs de correção.

Implementa o loop principal de consumo da fila pgmq e orquestra
o processamento de cada job.
"""

import logging
import time
from datetime import datetime
from typing import Optional

from .config import WorkerConfig
from .models import JobStatus, QueueMessage, ErrorCode
from .supabase_client import SupabaseWorkerClient
from .job_processor import JobProcessor

logger = logging.getLogger(__name__)


class QueueConsumer:
    """Consumidor de fila de correções."""
    
    def __init__(self, config: WorkerConfig):
        """
        Inicializa o consumidor.
        
        Args:
            config: Configuração do worker.
        """
        self.config = config
        self.client = SupabaseWorkerClient(config)
        self.processor = JobProcessor(self.client)
        self._running = False
    
    def start(self) -> None:
        """
        Inicia o loop de consumo da fila.
        
        O loop continua até que stop() seja chamado.
        """
        self._running = True
        logger.info(f"Iniciando consumo da fila '{self.config.queue_name}'...")
        
        while self._running:
            try:
                message = self._poll_message()
                
                if message:
                    self._process_message(message)
                else:
                    # Sem mensagens, aguarda antes de tentar novamente
                    time.sleep(self.config.poll_interval)
                    
            except Exception as e:
                logger.error(f"Erro no loop de consumo: {e}")
                # Aguarda antes de tentar novamente após erro
                time.sleep(self.config.poll_interval)
    
    def stop(self) -> None:
        """Para o loop de consumo."""
        logger.info("Parando consumidor...")
        self._running = False
    
    def _poll_message(self) -> Optional[QueueMessage]:
        """
        Tenta ler uma mensagem da fila.
        
        Returns:
            QueueMessage se houver mensagem disponível, None caso contrário.
        """
        try:
            return self.client.read_queue_message()
        except Exception as e:
            logger.error(f"Erro ao ler mensagem da fila: {e}")
            return None
    
    def _process_message(self, message: QueueMessage) -> None:
        """
        Processa uma mensagem da fila.
        
        Args:
            message: Mensagem a ser processada.
        """
        job_id = message.job_id
        logger.info(f"Processando job {job_id} (msg_id={message.msg_id}, read_ct={message.read_ct})")
        
        # Verifica se excedeu número máximo de tentativas
        if message.read_ct > self.config.max_retries:
            logger.warning(f"Job {job_id} excedeu máximo de tentativas ({self.config.max_retries})")
            self._mark_job_failed(job_id, "Excedeu número máximo de tentativas")
            self._delete_message(message.msg_id)
            return
        
        try:
            # Busca o job
            job = self.client.get_job(job_id)
            
            if not job:
                logger.error(f"Job {job_id} não encontrado")
                self._delete_message(message.msg_id)
                return
            
            # Verifica se job já foi processado ou cancelado
            if job.status in [JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELED]:
                logger.info(f"Job {job_id} já está em status final: {job.status.value}")
                self._delete_message(message.msg_id)
                return
            
            # Atualiza status para PROCESSING
            start_time = datetime.utcnow()
            self.client.update_job_status(
                job_id=job_id,
                status=JobStatus.PROCESSING,
                started_at=start_time
            )
            
            # Processa o job
            success = self.processor.process_job(job)
            
            if success:
                logger.info(f"Job {job_id} processado com sucesso")
                self._archive_message(message.msg_id)
            else:
                logger.warning(f"Job {job_id} falhou no processamento")
                self._delete_message(message.msg_id)
                
        except Exception as e:
            logger.error(f"Erro ao processar job {job_id}: {e}")
            # Não deleta a mensagem para permitir retry
            # A mensagem voltará a ficar visível após o visibility timeout
    
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
            # Nota: O release_tokens é chamado pelo cron job ou pode ser
            # chamado aqui se necessário
        except Exception as e:
            logger.error(f"Erro ao marcar job {job_id} como falho: {e}")
    
    def _delete_message(self, msg_id: int) -> None:
        """
        Remove uma mensagem da fila.
        
        Args:
            msg_id: ID da mensagem.
        """
        try:
            self.client.delete_queue_message(msg_id)
        except Exception as e:
            logger.error(f"Erro ao deletar mensagem {msg_id}: {e}")
    
    def _archive_message(self, msg_id: int) -> None:
        """
        Arquiva uma mensagem da fila.
        
        Args:
            msg_id: ID da mensagem.
        """
        try:
            self.client.archive_queue_message(msg_id)
        except Exception as e:
            logger.error(f"Erro ao arquivar mensagem {msg_id}: {e}")
