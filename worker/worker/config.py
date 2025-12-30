"""
Configuração do Worker.

Carrega variáveis de ambiente e define configurações padrão.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class WorkerConfig:
    """Configuração do worker."""

    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # Queue
    queue_name: str = "corrections"
    visibility_timeout: int = 300  # 5 minutes
    poll_interval: int = 5  # seconds
    max_retries: int = 3

    # Processing
    batch_size: int = 1

    @classmethod
    def from_env(cls) -> "WorkerConfig":
        """Cria configuração a partir de variáveis de ambiente."""
        supabase_url = os.getenv("SUPABASE_URL")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not service_role_key:
            raise ValueError(
                "SUPABASE_SERVICE_ROLE_KEY environment variable is required"
            )

        return cls(
            supabase_url=supabase_url,
            supabase_service_role_key=service_role_key,
            queue_name=os.getenv("QUEUE_NAME", "corrections"),
            visibility_timeout=int(os.getenv("VISIBILITY_TIMEOUT", "300")),
            poll_interval=int(os.getenv("POLL_INTERVAL", "5")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            batch_size=int(os.getenv("BATCH_SIZE", "1")),
        )
