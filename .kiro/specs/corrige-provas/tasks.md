# Implementation Plan: CorrigeProvas

## Overview

Este plano implementa o sistema CorrigeProvas com arquitetura Supabase-first. A implementação segue uma abordagem incremental: primeiro a infraestrutura de banco e autenticação, depois as Edge Functions, o Worker Python, e finalmente a integração no Frontend.

**Stack**:
- Frontend: React + Vite + TypeScript
- Backend: Supabase (Postgres, Auth, Storage, Realtime, Queues)
- Edge Functions: TypeScript/Deno
- Worker: Python + OpenCV
- Testes: Vitest, pytest + hypothesis, Playwright

## Tasks

- [x] 1. Setup inicial do projeto Supabase
  - [x] 1.1 Criar projeto Supabase e configurar ambiente local
    - Instalar Supabase CLI
    - Executar `supabase init` e `supabase start`
    - Configurar variáveis de ambiente (.env.local)
    - _Requirements: 11.1_

  - [x] 1.2 Criar schema do banco de dados
    - Criar migration com todas as tabelas: profiles, institutions, user_roles, templates, exams, exam_variants, answer_keys, correction_jobs, correction_items, plans, subscriptions, usage_ledger
    - Definir tipos enum para status, roles, reasons
    - Criar índices para queries frequentes
    - _Requirements: 2.5, 3.3, 5.2_

  - [x] 1.3 Implementar políticas RLS
    - Habilitar RLS em todas as tabelas com dados de usuário
    - Criar políticas SELECT/INSERT/UPDATE/DELETE baseadas em owner_user_id e institution_id
    - _Requirements: 11.1, 11.2, 11.3_

  - [ ]* 1.4 Escrever testes de propriedade para RLS
    - **Property 6: RLS Data Isolation**
    - **Validates: Requirements 3.4, 11.2, 11.3**

  - [x] 1.5 Criar funções SQL para tokens
    - Implementar `reserve_tokens(user_id, amount, job_id)`
    - Implementar `release_tokens(job_id)`
    - Implementar `get_balance(user_id)`
    - _Requirements: 9.1, 9.4_

  - [ ]* 1.6 Escrever testes de propriedade para token ledger
    - **Property 12: Token Ledger Consistency**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4**

  - [x] 1.7 Configurar Storage buckets
    - Criar buckets: templates, uploads, results, exports
    - Configurar políticas de acesso por bucket
    - _Requirements: 4.2, 11.6, 11.7_

  - [ ]* 1.8 Escrever testes de propriedade para Storage paths
    - **Property 14: Storage Path Enforcement**
    - **Validates: Requirements 11.6, 11.7**

- [x] 2. Checkpoint - Verificar infraestrutura
  - Executar `supabase db reset` e verificar migrations
  - Testar políticas RLS manualmente
  - Verificar buckets de Storage
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Implementar Edge Functions
  - [x] 3.1 Configurar estrutura de Edge Functions
    - Criar diretório `supabase/functions`
    - Configurar shared modules (supabase client, validation, errors)
    - Instalar dependências (zod)
    - _Requirements: 14.1_

  - [x] 3.2 Implementar get_upload_urls
    - Criar schema Zod para validação de entrada
    - Gerar signed URLs para upload direto ao Storage
    - Retornar paths e URLs com TTL curto
    - _Requirements: 4.1, 4.2_

  - [ ]* 3.3 Escrever testes de propriedade para get_upload_urls
    - **Property 7: Upload URL Generation**
    - **Validates: Requirements 4.1, 4.2, 4.4**

  - [x] 3.4 Implementar create_job
    - Criar schema Zod para validação de entrada
    - Validar ownership de answer_key via query
    - Chamar reserve_tokens transacionalmente
    - Criar correction_job e correction_items
    - Publicar mensagem na queue "corrections"
    - Implementar idempotency_key
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [ ]* 3.5 Escrever testes de propriedade para create_job
    - **Property 8: Job Creation Invariants**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7**

  - [x] 3.6 Implementar get_result_urls
    - Criar schema Zod para validação de entrada
    - Validar ownership do job
    - Gerar signed URLs para XLSX e imagens marcadas
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ]* 3.7 Escrever testes de propriedade para get_result_urls
    - **Property 11: Result URL Authorization**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

  - [x] 3.8 Implementar stripe_webhook
    - Validar assinatura do webhook Stripe
    - Processar eventos de subscription (created, updated, deleted)
    - Processar eventos de invoice (paid, payment_failed)
    - Garantir idempotência via event_id
    - _Requirements: 10.3, 10.4_

  - [ ]* 3.9 Escrever testes de propriedade para stripe_webhook
    - **Property 13: Subscription State Management**
    - **Validates: Requirements 10.2, 10.3, 10.4, 10.5**

  - [ ]* 3.10 Escrever testes de propriedade para validação de entrada
    - **Property 17: Input Validation**
    - **Validates: Requirements 14.1, 14.2, 14.4**

  - [x] 3.11 Escrever testes automatizados
    - Cada função do supabase functions serve deve ser testada
    - Executar `supabase functions serve` localmente
    - Executar testes

- [x] 4. Checkpoint - Verificar Edge Functions
  - Executar `supabase functions serve` localmente
  - Testar cada função com curl/httpie
  - Ensure all tests pass, ask the user if questions arise.

- [-] 5. Implementar Worker Python
  - [x] 5.1 Configurar projeto Python
    - Criar estrutura de diretórios (worker/, tests/)
    - Configurar pyproject.toml com dependências (opencv-python, supabase-py, openpyxl, hypothesis)
    - Configurar pytest e hypothesis
    - _Requirements: 6.1_

  - [x] 5.2 Implementar QueueConsumer
    - Conectar ao Supabase com service_role_key
    - Implementar loop de consumo da fila "corrections"
    - Implementar visibility timeout e retry
    - Atualizar status do job para PROCESSING
    - _Requirements: 6.1, 6.2_

  - [x] 5.3 Implementar ImageProcessor
    - Implementar normalize() para ajuste de brilho/contraste
    - Implementar align() para alinhamento via marcadores
    - Implementar detect_marks() para detecção de respostas
    - Implementar read_qr() para leitura de QR code
    - Implementar generate_marked_image() para imagem com correções
    - _Requirements: 6.3, 6.4, 6.6_

  - [ ] 5.4 Escrever testes de propriedade para comparação de respostas
    - **Property 9: Answer Comparison Correctness**
    - **Validates: Requirements 6.5**

  - [x] 5.5 Implementar XLSXGenerator
    - Gerar planilha com colunas: identificador, respostas detectadas, acertos, total
    - Incluir resumo estatístico
    - _Requirements: 6.7_

  - [x] 5.6 Implementar fluxo completo de processamento
    - Orquestrar download → processamento → upload para cada item
    - Atualizar correction_items com resultados
    - Gerar e fazer upload do XLSX ao final
    - Atualizar job status para DONE ou FAILED
    - Broadcast via Realtime
    - _Requirements: 6.6, 6.7, 6.8, 6.9, 6.10, 6.11_

  - [ ]* 5.7 Escrever testes de propriedade para outputs de processamento
    - **Property 10: Processing Output Generation**
    - **Validates: Requirements 6.6, 6.7, 6.8, 6.9, 6.10**

- [ ] 6. Checkpoint - Verificar Worker
  - Executar worker localmente conectado ao Supabase local
  - Testar com imagens de exemplo
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implementar Frontend
  - [ ] 7.1 Configurar projeto React + Vite
    - Criar projeto com `npm create vite@latest`
    - Instalar dependências (supabase-js, react-router-dom, tailwindcss)
    - Configurar variáveis de ambiente VITE_SUPABASE_*
    - _Requirements: 1.1_

  - [ ] 7.2 Implementar AuthContext
    - Criar contexto de autenticação com Supabase Auth
    - Implementar signIn, signUp, signOut, resetPassword
    - Gerenciar sessão e estado de loading
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 7.3 Escrever testes de propriedade para autenticação
    - **Property 1: Authentication Session Validity**
    - **Property 2: Registration Profile Linkage**
    - **Validates: Requirements 1.1, 1.2**

  - [ ] 7.4 Implementar CorrectionService
    - Implementar getUploadUrls() chamando Edge Function
    - Implementar createJob() chamando Edge Function
    - Implementar getResultUrls() chamando Edge Function
    - Implementar subscribeToJob() com Realtime
    - _Requirements: 4.1, 5.1, 7.1, 8.1, 8.2_

  - [ ] 7.5 Implementar páginas de correção
    - Criar página de upload de imagens
    - Criar seletor de template e gabarito
    - Criar visualização de progresso em tempo real
    - Criar página de resultados com download
    - _Requirements: 4.2, 8.3, 8.4_

  - [ ] 7.6 Implementar gestão de gabaritos
    - Criar formulário de criação de gabarito
    - Validar answers_string no frontend
    - Listar gabaritos do usuário
    - _Requirements: 3.1, 3.2, 3.4_

  - [ ]* 7.7 Escrever testes de propriedade para validação de gabarito
    - **Property 5: Answer Key Validation**
    - **Validates: Requirements 3.1, 3.2, 3.3**

  - [ ] 7.8 Implementar gestão de templates
    - Listar templates ativos
    - Exibir detalhes (question_count, alternatives_count)
    - _Requirements: 2.1, 2.2, 2.4_

  - [ ]* 7.9 Escrever testes de propriedade para templates
    - **Property 4: Template Constraints**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

- [ ] 8. Checkpoint - Verificar Frontend
  - Executar `npm run dev` e testar fluxos manualmente
  - Verificar integração com Supabase local
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implementar funcionalidades adicionais
  - [ ] 9.1 Implementar criação de provas client-side
    - Integrar jszip e qrious para geração de DOCX/ZIP
    - Persistir metadados em exams e exam_variants
    - Upload de artefatos para Storage
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

  - [ ]* 9.2 Escrever testes de propriedade para persistência de exames
    - **Property 15: Exam Persistence**
    - **Validates: Requirements 12.2, 12.3, 12.4**

  - [ ] 9.3 Implementar página de assinaturas
    - Listar planos disponíveis
    - Integrar com Stripe Checkout
    - Exibir status da assinatura atual
    - _Requirements: 10.1, 10.2, 10.5_

  - [ ] 9.4 Implementar dashboard de consumo
    - Exibir saldo de tokens
    - Listar histórico de uso (usage_ledger)
    - _Requirements: 9.4_

  - [ ] 9.5 Implementar controle de acesso por role
    - Verificar roles em rotas protegidas
    - Exibir/ocultar funcionalidades baseado em role
    - _Requirements: 1.6, 1.7_

  - [ ]* 9.6 Escrever testes de propriedade para controle de acesso
    - **Property 3: Role-Based Access Control**
    - **Validates: Requirements 1.6, 1.7**

- [ ] 10. Implementar Cron Jobs
  - [ ] 10.1 Configurar pg_cron no Supabase
    - Habilitar extensão pg_cron
    - Criar job para detectar jobs órfãos (PROCESSING > timeout)
    - _Requirements: 13.1, 13.2_

  - [ ] 10.2 Implementar handler de timeout
    - Marcar jobs expirados como FAILED
    - Chamar release_tokens para reembolso
    - _Requirements: 13.2, 13.3_

  - [ ]* 10.3 Escrever testes de propriedade para timeout handling
    - **Property 16: Timeout Handling**
    - **Validates: Requirements 13.2, 13.3**

- [ ] 11. Checkpoint - Verificar funcionalidades completas
  - Testar fluxo completo end-to-end
  - Verificar cron jobs
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Testes E2E
  - [ ] 12.1 Configurar Playwright
    - Instalar Playwright e browsers
    - Configurar base URL e timeouts
    - _Requirements: N/A_

  - [ ]* 12.2 Implementar testes E2E de fluxo de correção
    - Login → Upload → Criar job → Monitorar → Download
    - _Requirements: 1.1, 4.1, 5.1, 8.1, 7.1_

  - [ ]* 12.3 Implementar testes E2E de fluxo de assinatura
    - Selecionar plano → Checkout → Verificar tokens
    - _Requirements: 10.1, 10.2, 9.4_

- [ ] 13. Checkpoint Final
  - Executar todos os testes (unit, property, E2E)
  - Verificar cobertura de código
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada task referencia requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental
- Property tests validam propriedades universais de corretude
- Unit tests validam exemplos específicos e edge cases
- O Worker Python deve ser executado como serviço separado (container/VM)
- Edge Functions são deployadas via `supabase functions deploy`
