# Design Document - Security Module Refactor

## Overview

Este documento descreve o design para refatorar o módulo de segurança atual, integrando bibliotecas robustas e testadas como `pathvalidate` e `werkzeug`, mantendo compatibilidade com a API existente e adicionando configurabilidade para diferentes ambientes.

## Architecture

### Arquitetura em Camadas

```
┌─────────────────────────────────────────┐
│           Public API Layer             │  ← Mantém compatibilidade
├─────────────────────────────────────────┤
│         Configuration Layer            │  ← Configuração flexível
├─────────────────────────────────────────┤
│          Provider Layer                │  ← Múltiplas implementações
│  ┌─────────────┬─────────────┬─────────┐ │
│  │ PathValidate│  Werkzeug   │ Custom  │ │
│  │  Provider   │  Provider   │Provider │ │
│  └─────────────┴─────────────┴─────────┘ │
├─────────────────────────────────────────┤
│           Fallback Layer               │  ← Graceful degradation
└─────────────────────────────────────────┘
```

### Componentes Principais

1. **SecurityManager**: Classe principal que coordena validações
2. **ValidationProvider**: Interface para diferentes implementações
3. **SecurityConfig**: Configuração centralizada
4. **FallbackHandler**: Gerencia fallbacks quando bibliotecas não estão disponíveis

## Components and Interfaces

### 1. SecurityManager

```python
class SecurityManager:
    """Gerenciador principal de segurança com múltiplos providers."""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.provider = self._get_provider()
    
    def sanitize_filename(self, filename: str, **kwargs) -> str:
        """API pública - mantém compatibilidade."""
        
    def validate_storage_path(self, path: str) -> Tuple[str, str]:
        """API pública - mantém compatibilidade."""
        
    def is_safe_path(self, basedir: str, path: str) -> bool:
        """Nova funcionalidade - validação robusta de path traversal."""
```

### 2. ValidationProvider Interface

```python
from abc import ABC, abstractmethod

class ValidationProvider(ABC):
    """Interface para diferentes implementações de validação."""
    
    @abstractmethod
    def sanitize_filename(self, filename: str, **kwargs) -> str:
        """Sanitiza nome de arquivo."""
        
    @abstractmethod
    def validate_filename(self, filename: str, **kwargs) -> None:
        """Valida nome de arquivo (raise exception se inválido)."""
        
    @abstractmethod
    def is_valid_filename(self, filename: str, **kwargs) -> bool:
        """Verifica se nome de arquivo é válido."""
```

### 3. Implementações Específicas

#### PathValidateProvider

```python
class PathValidateProvider(ValidationProvider):
    """Provider usando biblioteca pathvalidate."""
    
    def __init__(self, platform: str = 'universal'):
        try:
            import pathvalidate
            self.pathvalidate = pathvalidate
            self.platform = platform
            self.available = True
        except ImportError:
            self.available = False
    
    def sanitize_filename(self, filename: str, **kwargs) -> str:
        if not self.available:
            raise ImportError("pathvalidate not available")
            
        return self.pathvalidate.sanitize_filename(
            filename,
            platform=self.platform,
            max_len=kwargs.get('max_length', 255),
            replacement_text=kwargs.get('replacement', '_')
        )
```

#### WerkzeugProvider

```python
class WerkzeugProvider(ValidationProvider):
    """Provider usando werkzeug.utils.secure_filename."""
    
    def __init__(self):
        try:
            from werkzeug.utils import secure_filename
            self.secure_filename = secure_filename
            self.available = True
        except ImportError:
            self.available = False
    
    def sanitize_filename(self, filename: str, **kwargs) -> str:
        if not self.available:
            raise ImportError("werkzeug not available")
            
        sanitized = self.secure_filename(filename)
        
        # Aplicar max_length se especificado
        max_length = kwargs.get('max_length', 255)
        if len(sanitized) > max_length:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:max_length-len(ext)] + ext
            
        return sanitized
```

#### CustomProvider

```python
class CustomProvider(ValidationProvider):
    """Provider usando implementação atual (fallback)."""
    
    def sanitize_filename(self, filename: str, **kwargs) -> str:
        # Implementação atual melhorada
        return _sanitize_filename_custom(filename, **kwargs)
```

### 4. SecurityConfig

```python
@dataclass
class SecurityConfig:
    """Configuração centralizada do módulo de segurança."""
    
    # Provider preferido
    preferred_provider: str = 'pathvalidate'  # 'pathvalidate', 'werkzeug', 'custom'
    
    # Configurações de validação
    validation_level: str = 'strict'  # 'strict', 'normal', 'permissive'
    platform: str = 'universal'  # 'universal', 'windows', 'posix'
    max_filename_length: int = 255
    
    # Configurações de path traversal
    allowed_buckets: Set[str] = field(default_factory=lambda: {
        'uploads', 'results', 'templates', 'exports'
    })
    
    # Configurações de fallback
    enable_fallback: bool = True
    log_provider_usage: bool = True
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """Cria configuração a partir de variáveis de ambiente."""
        return cls(
            preferred_provider=os.getenv('SECURITY_PROVIDER', 'pathvalidate'),
            validation_level=os.getenv('SECURITY_LEVEL', 'strict'),
            platform=os.getenv('SECURITY_PLATFORM', 'universal'),
        )
```

## Data Models

### ValidationResult

```python
@dataclass
class ValidationResult:
    """Resultado de uma operação de validação."""
    
    is_valid: bool
    sanitized_value: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    provider_used: Optional[str] = None
```

### SecurityViolation

```python
@dataclass
class SecurityViolation:
    """Representa uma violação de segurança detectada."""
    
    violation_type: str  # 'path_traversal', 'invalid_filename', 'unauthorized_access'
    original_value: str
    detected_patterns: List[str]
    severity: str  # 'low', 'medium', 'high', 'critical'
    timestamp: datetime
    provider_used: str
```

## Correctness Properties

### Property 1: Provider Fallback Reliability
*For any* filename validation request, if the preferred provider is unavailable, the system should gracefully fall back to the next available provider without failing
**Validates: Requirements 3.4, 7.2**

### Property 2: API Backward Compatibility
*For any* existing function call to the security module, the refactored implementation should produce equivalent or more secure results
**Validates: Requirements 6.1, 6.3**

### Property 3: Path Traversal Detection Robustness
*For any* malicious path containing traversal sequences (including encoded variants), the enhanced validation should detect and block the attempt
**Validates: Requirements 4.1, 4.4**

### Property 4: Configuration Consistency
*For any* security configuration, all providers should respect the same validation level and produce consistent results within acceptable variance
**Validates: Requirements 7.1, 7.4**

### Property 5: Filename Sanitization Completeness
*For any* filename containing dangerous characters, the sanitization should remove or replace all dangerous characters while preserving valid content
**Validates: Requirements 2.1, 5.2**

### Property 6: Cross-Platform Compatibility
*For any* platform-specific validation (Windows/POSIX/Universal), the system should apply appropriate rules for that platform
**Validates: Requirements 2.4, 5.1**

### Property 7: Performance Degradation Bounds
*For any* validation operation, the performance impact of using external libraries should not exceed 2x the current implementation time
**Validates: Requirements 6.2, 6.4**

## Error Handling

### Estratégia de Error Handling

1. **Graceful Degradation**: Se biblioteca preferida não estiver disponível, usar fallback
2. **Logging Detalhado**: Log qual provider está sendo usado e por quê
3. **Validation Errors**: Manter compatibilidade com `SecurityError` atual
4. **Configuration Errors**: Validar configuração na inicialização

### Hierarquia de Exceptions

```python
class SecurityError(Exception):
    """Base exception - mantém compatibilidade."""
    pass

class ValidationError(SecurityError):
    """Erro de validação específico."""
    
    def __init__(self, message: str, violation: SecurityViolation = None):
        super().__init__(message)
        self.violation = violation

class ConfigurationError(SecurityError):
    """Erro de configuração do módulo."""
    pass

class ProviderUnavailableError(SecurityError):
    """Nenhum provider disponível."""
    pass
```

## Testing Strategy

### Testes de Compatibilidade

1. **Regression Tests**: Todos os testes existentes devem continuar passando
2. **API Compatibility**: Verificar que todas as funções públicas mantêm assinatura
3. **Behavior Compatibility**: Resultados devem ser equivalentes ou mais seguros

### Testes de Robustez

1. **Edge Cases**: Testar casos não cobertos pela implementação atual
2. **Cross-Provider**: Comparar resultados entre diferentes providers
3. **Fallback Scenarios**: Testar comportamento quando bibliotecas não estão disponíveis

### Testes de Performance

1. **Benchmark**: Comparar performance entre implementações
2. **Memory Usage**: Verificar uso de memória
3. **Scalability**: Testar com grande volume de validações

### Property-Based Tests

```python
@given(st.text())
def test_sanitization_safety(filename):
    """Qualquer filename sanitizado deve ser seguro."""
    result = security_manager.sanitize_filename(filename)
    assert not contains_dangerous_patterns(result)
    assert is_valid_filename(result)

@given(st.text(), st.text())
def test_path_traversal_detection(basedir, malicious_path):
    """Qualquer path malicioso deve ser detectado."""
    if contains_traversal_pattern(malicious_path):
        assert not security_manager.is_safe_path(basedir, malicious_path)
```

## Implementation Plan

### Fase 1: Infraestrutura Base
1. Criar interfaces e classes base
2. Implementar sistema de configuração
3. Criar testes de compatibilidade

### Fase 2: Implementação de Providers
1. Implementar PathValidateProvider
2. Implementar WerkzeugProvider
3. Refatorar implementação atual como CustomProvider

### Fase 3: Integração e Fallback
1. Implementar lógica de fallback
2. Adicionar logging e monitoramento
3. Testes de integração

### Fase 4: Melhorias de Segurança
1. Implementar validação robusta de path traversal
2. Adicionar detecção de casos edge
3. Testes de segurança abrangentes

### Fase 5: Otimização e Documentação
1. Otimização de performance
2. Documentação completa
3. Guia de migração