"""
Entry point do Worker CorrigeProvas.

Inicia o consumidor de fila e processa jobs de correção.
"""

import logging
import signal
import sys

from .config import WorkerConfig
from .queue_consumer import QueueConsumer

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


def main():
    """Função principal do worker."""
    logger.info("Iniciando CorrigeProvas Worker...")
    
    try:
        config = WorkerConfig.from_env()
        logger.info(f"Configuração carregada: queue={config.queue_name}, poll_interval={config.poll_interval}s")
    except ValueError as e:
        logger.error(f"Erro de configuração: {e}")
        sys.exit(1)
    
    consumer = QueueConsumer(config)
    
    # Handler para shutdown graceful
    def signal_handler(signum, frame):
        logger.info("Recebido sinal de shutdown, finalizando...")
        consumer.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        consumer.start()
    except Exception as e:
        logger.error(f"Erro fatal no worker: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
