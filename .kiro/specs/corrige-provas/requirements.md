# Requirements Document

## Introduction

O CorrigeProvas é uma aplicação web para correção automatizada de provas de múltipla escolha, permitindo que professores e instituições criem provas (DOCX) e folhas de resposta com QR Code, definam gabaritos e modelos, enviem imagens digitalizadas de folhas de resposta, recebam correção automática e relatórios (XLSX), e consultem histórico e consumo (tokens) por usuário/instituição.

A arquitetura é Supabase-first: Supabase como backend principal (Auth + DB + Storage + Realtime + Queues + Cron), Edge Functions (TypeScript/Deno) para lógica de negócio, e Worker Python isolado para reconhecimento via OpenCV.

IMPORTANTE: Parte do backend com a lógica em python já existe.

## Glossary

- **Sistema**: A aplicação CorrigeProvas como um todo
- **Frontend**: SPA React + Vite que interage com Supabase
- **Edge_Function**: Função TypeScript/Deno executada no ambiente Supabase para lógica de negócio
- **Worker_Python**: Serviço consumidor de fila que executa pipeline de correção com OpenCV
- **Storage**: Supabase Storage para armazenamento de arquivos (imagens, XLSX, templates)
- **Queue**: Fila durável baseada em pgmq para processamento assíncrono
- **Correction_Job**: Entidade que representa um lote de correções a ser processado
- **Correction_Item**: Entidade que representa uma folha de resposta individual dentro de um job
- **Answer_Key**: Gabarito contendo as respostas corretas para uma prova
- **Template**: Modelo de folha de resposta (10/20/50/100 questões, 4/5 alternativas)
- **Token**: Unidade de consumo para controle de uso do sistema
- **RLS**: Row Level Security - políticas de segurança no Postgres
- **Signed_URL**: URL temporária com assinatura para acesso seguro a arquivos
- **Exam_Variant**: Versão de uma prova com ordem específica de questões e alternativas
- **Model_Identifier**: Identificador único de um modelo de prova (ex: Modelo A, Modelo B)
- **Shuffle_Seed**: Semente para randomização determinística, permitindo reprodutibilidade

## Requirements

### Requirement 1: Autenticação e Gestão de Usuários

**User Story:** As a user, I want to authenticate securely and manage my profile, so that I can access the system and have my data protected.

#### Acceptance Criteria

1. WHEN a user attempts to login, THE Sistema SHALL authenticate via Supabase Auth and establish a secure session
2. WHEN a user registers, THE Sistema SHALL create a profile record linked to auth.users.id
3. WHEN a user requests password reset, THE Sistema SHALL send a reset email via Supabase Auth
4. WHEN a user session expires, THE Sistema SHALL require re-authentication
5. IF an unauthenticated user attempts to access protected resources, THEN THE Sistema SHALL redirect to login
6. WHEN a user has role ADMIN, THE Sistema SHALL grant access to administrative functions
7. WHEN a user belongs to an institution, THE Sistema SHALL associate their data with institution_id

### Requirement 2: Gestão de Templates de Folha de Resposta

**User Story:** As a teacher, I want to manage answer sheet templates, so that I can use standardized formats for my exams.

#### Acceptance Criteria

1. THE Sistema SHALL support templates with 10, 20, 50, or 100 questions
2. THE Sistema SHALL support templates with 4 or 5 alternatives per question
3. WHEN a template is created, THE Sistema SHALL store template_storage_path pointing to Storage bucket
4. WHEN listing templates, THE Sistema SHALL return only active templates (is_active = true)
5. THE Template SHALL contain question_count, alternatives_count, version, and name fields

### Requirement 3: Gestão de Gabaritos (Answer Keys)

**User Story:** As a teacher, I want to create and manage answer keys, so that I can define correct answers for automatic grading.

#### Acceptance Criteria

1. WHEN creating an answer key, THE Sistema SHALL validate that answers_string length equals template.question_count
2. WHEN creating an answer key, THE Sistema SHALL validate that all characters in answers_string are within valid alternatives (A-E based on template)
3. THE Answer_Key SHALL be associated with owner_user_id and optionally with exam_id and institution_id
4. WHEN a user queries answer keys, THE Sistema SHALL return only keys owned by that user or their institution (via RLS)

### Requirement 4: Upload de Imagens para Correção

**User Story:** As a teacher, I want to upload scanned answer sheet images, so that they can be automatically graded.

#### Acceptance Criteria

1. WHEN a user requests upload URLs, THE Edge_Function get_upload_urls SHALL return signed URLs with short TTL
2. WHEN uploading images, THE Frontend SHALL upload directly to Storage bucket uploads/{uid}/...
3. THE Sistema SHALL NOT transmit large files as JSON/base64 to backend
4. WHEN upload completes, THE Sistema SHALL store original_storage_path in correction_items

### Requirement 5: Criação de Jobs de Correção

**User Story:** As a teacher, I want to create correction jobs, so that my uploaded images are processed and graded.

#### Acceptance Criteria

1. WHEN creating a job, THE Edge_Function create_job SHALL validate ownership of answer_key via RLS
2. WHEN creating a job, THE Edge_Function create_job SHALL create correction_job with status QUEUED
3. WHEN creating a job, THE Edge_Function create_job SHALL create correction_items for each uploaded image
4. WHEN creating a job, THE Edge_Function create_job SHALL reserve tokens via transactional SQL function
5. WHEN creating a job, THE Edge_Function create_job SHALL publish message to queue "corrections" with job_id
6. IF token balance is insufficient, THEN THE Edge_Function create_job SHALL reject the request with appropriate error
7. WHEN create_job receives idempotency_key, THE Edge_Function SHALL return existing job if key matches

### Requirement 6: Processamento Assíncrono de Correções

**User Story:** As a system operator, I want corrections to be processed asynchronously, so that the system remains responsive under load.

#### Acceptance Criteria

1. WHEN a message arrives in queue "corrections", THE Worker_Python SHALL consume and process the job
2. WHEN processing a job, THE Worker_Python SHALL download images from Storage using service role credentials
3. WHEN processing an image, THE Worker_Python SHALL perform normalization, alignment, and mark detection via OpenCV
4. WHEN processing an image, THE Worker_Python SHALL read QR/identifier when present
5. WHEN processing an image, THE Worker_Python SHALL compare detected answers with answer_key
6. WHEN processing completes for an item, THE Worker_Python SHALL generate marked image and upload to results bucket
7. WHEN all items are processed, THE Worker_Python SHALL generate XLSX report and upload to results bucket
8. WHEN processing completes, THE Worker_Python SHALL update correction_job status to DONE
9. IF processing fails for an item, THEN THE Worker_Python SHALL record error_code and error_message in correction_item
10. IF processing fails for entire job, THEN THE Worker_Python SHALL update status to FAILED
11. WHEN job status changes, THE Sistema SHALL broadcast update via Supabase Realtime

### Requirement 7: Download de Resultados

**User Story:** As a teacher, I want to download correction results, so that I can review grades and share with students.

#### Acceptance Criteria

1. WHEN requesting results, THE Edge_Function get_result_urls SHALL return signed URL for XLSX file
2. WHEN requesting results, THE Edge_Function get_result_urls SHALL return signed URLs for marked images
3. THE Sistema SHALL generate signed URLs with short expiration time
4. WHEN a user requests results, THE Sistema SHALL validate ownership via RLS before generating URLs

### Requirement 8: Acompanhamento em Tempo Real

**User Story:** As a teacher, I want to monitor correction progress in real-time, so that I know when results are ready.

#### Acceptance Criteria

1. WHEN a correction job is created, THE Frontend SHALL subscribe to Realtime updates for that job
2. WHEN job status changes, THE Sistema SHALL push update via Supabase Realtime
3. WHEN job progress updates (success_items, error_items), THE Sistema SHALL push update via Realtime
4. THE Frontend SHALL display current status and progress to user

### Requirement 9: Controle de Tokens e Consumo

**User Story:** As a user, I want to track my token usage, so that I can manage my consumption and plan purchases.

#### Acceptance Criteria

1. WHEN a correction job is created, THE Sistema SHALL debit tokens from user balance via usage_ledger
2. WHEN tokens are debited, THE Sistema SHALL record delta_tokens (negative), reason, and job_id in usage_ledger
3. WHEN a subscription renews, THE Sistema SHALL credit tokens via usage_ledger with reason PLAN_RENEW
4. WHEN querying balance, THE Sistema SHALL calculate sum of delta_tokens from usage_ledger for user
5. THE Sistema SHALL control tokens via transactional DB operations, not manual decrements

### Requirement 10: Gestão de Planos e Assinaturas

**User Story:** As a user, I want to subscribe to plans, so that I can access the system with appropriate token allowances.

#### Acceptance Criteria

1. THE Sistema SHALL maintain plans table with monthly_price_cents, monthly_tokens, and is_active
2. WHEN a user subscribes, THE Sistema SHALL create subscription record with status ACTIVE
3. WHEN Stripe webhook arrives, THE Edge_Function stripe_webhook SHALL update subscription status
4. WHEN Stripe webhook arrives, THE Edge_Function stripe_webhook SHALL ensure idempotency via event_id
5. WHEN subscription status changes to PAST_DUE or CANCELED, THE Sistema SHALL restrict user access appropriately

### Requirement 11: Segurança e Isolamento de Dados

**User Story:** As a user, I want my data to be secure and isolated, so that only I (or my institution) can access it.

#### Acceptance Criteria

1. THE Sistema SHALL enable RLS on all tables containing user data
2. WHEN a user queries data, THE Sistema SHALL filter by owner_user_id = auth.uid() via RLS
3. WHEN a user belongs to institution, THE Sistema SHALL allow access to institution data based on role
4. THE Sistema SHALL store SERVICE_ROLE_KEY only in server-side environments (Worker, Edge Functions)
5. THE Sistema SHALL validate hCaptcha server-side in Edge Functions
6. WHEN uploading to Storage, THE Sistema SHALL enforce path prefix uploads/{uid}/... via policies
7. WHEN downloading from Storage, THE Sistema SHALL enforce path prefix results/{uid}/... via policies

### Requirement 12: Criação de Provas e Folhas de Resposta

**User Story:** As a teacher, I want to create exams and answer sheets with QR codes, so that I can distribute standardized materials.

#### Acceptance Criteria

1. WHEN creating an exam, THE Frontend SHALL generate DOCX and answer sheets client-side using jszip and qrious
2. WHEN creating an exam, THE Sistema SHALL persist exam metadata in Postgres (exams table)
3. WHEN creating exam variants, THE Sistema SHALL store variant_index, model_id, and qrcode_payload
4. WHEN saving exam artifacts, THE Sistema SHALL upload ZIPs/DOCX to Storage bucket (exports or templates)

### Requirement 15: Randomização de Provas e Geração de Modelos

**User Story:** As a teacher, I want to randomize question and alternative order to generate multiple exam variants, so that I can reduce cheating and have unique answer keys for each variant.

#### Acceptance Criteria

1. WHEN creating an exam with randomization enabled, THE Sistema SHALL allow the user to specify the number of variants to generate
2. WHEN generating variants, THE Sistema SHALL shuffle the order of questions according to user preference (enabled/disabled)
3. WHEN generating variants, THE Sistema SHALL shuffle the order of alternatives within each question according to user preference (enabled/disabled)
4. WHEN generating variants with shuffled alternatives, THE Sistema SHALL update the correct answer letter to match the new position
5. FOR EACH generated variant, THE Sistema SHALL produce a unique answer_key reflecting the shuffled order
6. WHEN generating multiple variants, THE Sistema SHALL assign a unique model identifier (e.g., Model A, Model B) to each variant
7. WHEN exporting variants, THE Sistema SHALL generate a ZIP containing all DOCX files and a summary of answer keys per model
8. THE Sistema SHALL ensure that shuffling is deterministic when given the same seed, allowing reproducibility

### Requirement 16: Imagens em Questões e Alternativas

**User Story:** As a teacher, I want to add images to questions and alternatives, so that I can create richer exam content with diagrams, charts, and visual elements.

#### Acceptance Criteria

1. WHEN editing a question, THE Sistema SHALL allow the user to insert one or more images in the question text
2. WHEN editing an alternative, THE Sistema SHALL allow the user to insert one image per alternative
3. WHEN uploading images for questions, THE Sistema SHALL validate that the file is a valid image format (JPEG, PNG, WebP)
4. WHEN uploading images for questions, THE Sistema SHALL store the image in Storage bucket and reference it in the question data
5. WHEN generating DOCX, THE Sistema SHALL embed all referenced images inline at their designated positions
6. WHEN displaying question preview, THE Sistema SHALL render images at appropriate size maintaining aspect ratio
7. IF an image upload fails, THEN THE Sistema SHALL display an error message and allow retry without losing other question data
8. WHEN shuffling questions or alternatives containing images, THE Sistema SHALL preserve the image associations correctly

### Requirement 13: Rotinas de Manutenção (Cron)

**User Story:** As a system operator, I want automated maintenance routines, so that the system remains healthy and efficient.

#### Acceptance Criteria

1. THE Sistema SHALL run cron jobs via pg_cron for recurring maintenance
2. WHEN a job remains in PROCESSING status beyond timeout threshold, THE Cron_Job SHALL mark it as FAILED
3. WHEN a job is marked FAILED by timeout, THE Sistema SHALL release reserved tokens if applicable
4. THE Sistema SHALL run cleanup routines for old artifacts in Storage based on retention policy
5. THE Sistema SHALL run reconciliation routines to detect orphaned jobs

### Requirement 14: Validação de Entrada

**User Story:** As a developer, I want all inputs validated, so that the system is protected from malformed data.

#### Acceptance Criteria

1. WHEN Edge Functions receive requests, THE Sistema SHALL validate inputs using Zod schemas
2. IF input validation fails, THEN THE Edge_Function SHALL return descriptive error response
3. WHEN creating answer_key, THE Sistema SHALL validate answers_string format (length and character set)
4. WHEN creating correction_job, THE Sistema SHALL validate that referenced answer_key and template exist

