/**
 * ZipExportService - Generates ZIP files containing all exam variants
 * Requirements: 12.4, 15.7
 */

import { supabase } from '@/lib/supabase'
import { saveAs } from 'file-saver'
import JSZip from 'jszip'
import QRious from 'qrious'
import { generateAllVariants, generateAnswerKeySummary, generateVariantDocx } from './examBuilderService'
import type { ExamConfig } from './examBuilderTypes'

export interface ZipExportOptions {
    includeAnswerKey: boolean
    includeAnswerSheet: boolean
    includeSummary: boolean
}

export interface ZipExportProgress {
    current: number
    total: number
    stage: 'generating' | 'packaging' | 'uploading' | 'complete'
    message: string
}

export type ProgressCallback = (progress: ZipExportProgress) => void

/**
 * Generates a QR code as a data URL
 */
function generateQRCode(data: string, size: number = 150): string {
    const qr = new QRious({
        value: data,
        size,
        level: 'M',
        background: 'white',
        foreground: 'black',
    })
    return qr.toDataURL('image/png')
}

/**
 * Generates an answer sheet HTML for a variant
 */
function generateAnswerSheetHTML(
    examName: string,
    modelIdentifier: string,
    questionCount: number,
    alternativesCount: number,
    qrPayload: string
): string {
    const qrDataUrl = generateQRCode(qrPayload, 150)
    const alternatives = 'ABCDE'.slice(0, alternativesCount).split('')

    let questionsHTML = ''
    for (let i = 1; i <= questionCount; i++) {
        const bubbles = alternatives
            .map(alt => `<span class="bubble">${alt}</span>`)
            .join('')
        questionsHTML += `
            <div class="question-row">
                <span class="question-number">${i.toString().padStart(2, '0')}</span>
                <div class="bubbles">${bubbles}</div>
            </div>
        `
    }

    return `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Folha de Respostas - ${examName} - Modelo ${modelIdentifier}</title>
    <style>
        @page {
            size: A4;
            margin: 1cm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            margin: 0;
            padding: 20px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
            border-bottom: 2px solid #000;
            padding-bottom: 10px;
        }
        .title-section {
            flex: 1;
        }
        .title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .model {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .qr-section {
            text-align: center;
        }
        .qr-code {
            width: 100px;
            height: 100px;
        }
        .student-info {
            margin-bottom: 20px;
            padding: 10px;
            border: 1px solid #000;
        }
        .student-info label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .student-info input {
            width: 100%;
            height: 25px;
            border: none;
            border-bottom: 1px solid #000;
        }
        .instructions {
            margin-bottom: 20px;
            padding: 10px;
            background: #f5f5f5;
            border: 1px solid #ddd;
        }
        .instructions h3 {
            margin: 0 0 10px 0;
            font-size: 14px;
        }
        .instructions ul {
            margin: 0;
            padding-left: 20px;
        }
        .answers-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
        }
        .question-row {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 5px;
            border: 1px solid #ddd;
        }
        .question-number {
            font-weight: bold;
            width: 25px;
        }
        .bubbles {
            display: flex;
            gap: 8px;
        }
        .bubble {
            width: 20px;
            height: 20px;
            border: 2px solid #000;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            font-weight: bold;
        }
        .footer {
            margin-top: 20px;
            text-align: center;
            font-size: 10px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="title-section">
            <div class="title">${examName}</div>
            <div class="model">Modelo ${modelIdentifier}</div>
        </div>
        <div class="qr-section">
            <img class="qr-code" src="${qrDataUrl}" alt="QR Code">
            <div style="font-size: 10px; margin-top: 5px;">Modelo ${modelIdentifier}</div>
        </div>
    </div>
    
    <div class="student-info">
        <label>Nome do Aluno:</label>
        <input type="text" />
        <label style="margin-top: 10px;">Turma:</label>
        <input type="text" style="width: 200px;" />
    </div>
    
    <div class="instructions">
        <h3>Instruções:</h3>
        <ul>
            <li>Use caneta preta ou azul</li>
            <li>Preencha completamente o círculo da alternativa escolhida</li>
            <li>Não rasure ou faça marcações fora dos círculos</li>
            <li>Marque apenas uma alternativa por questão</li>
        </ul>
    </div>
    
    <div class="answers-grid">
        ${questionsHTML}
    </div>
    
    <div class="footer">
        Gerado por CorrigeProvas | ${new Date().toLocaleDateString('pt-BR')}
    </div>
</body>
</html>
    `
}

/**
 * Exports all exam variants as a ZIP file
 */
export async function exportExamAsZip(
    config: ExamConfig,
    options: ZipExportOptions,
    onProgress?: ProgressCallback
): Promise<Blob> {
    const zip = new JSZip()
    const variants = generateAllVariants(config)
    const totalSteps = variants.length + (options.includeSummary ? 1 : 0) + (options.includeAnswerSheet ? variants.length : 0)
    let currentStep = 0

    // Generate DOCX for each variant
    for (const variant of variants) {
        onProgress?.({
            current: ++currentStep,
            total: totalSteps,
            stage: 'generating',
            message: `Gerando Modelo ${variant.modelIdentifier}...`,
        })

        const docxBlob = await generateVariantDocx(config, variant, options.includeAnswerKey)
        const filename = `${config.name.replace(/[^a-zA-Z0-9]/g, '_')}_Modelo_${variant.modelIdentifier}.docx`
        zip.file(filename, docxBlob)
    }

    // Generate answer sheets if requested
    if (options.includeAnswerSheet) {
        const answerSheetsFolder = zip.folder('folhas_de_resposta')

        for (const variant of variants) {
            onProgress?.({
                current: ++currentStep,
                total: totalSteps,
                stage: 'generating',
                message: `Gerando folha de respostas Modelo ${variant.modelIdentifier}...`,
            })

            const qrPayload = JSON.stringify({
                examId: config.name,
                model: variant.modelIdentifier,
                questionCount: config.questions.length,
            })

            const html = generateAnswerSheetHTML(
                config.name,
                variant.modelIdentifier,
                config.questions.length,
                config.questions[0]?.alternatives.length || 4,
                qrPayload
            )

            const filename = `folha_respostas_Modelo_${variant.modelIdentifier}.html`
            answerSheetsFolder?.file(filename, html)
        }
    }

    // Generate summary if requested
    if (options.includeSummary) {
        onProgress?.({
            current: ++currentStep,
            total: totalSteps,
            stage: 'generating',
            message: 'Gerando resumo dos gabaritos...',
        })

        const summary = generateAnswerKeySummary(config, variants)
        zip.file('gabaritos.txt', summary)

        // Also generate a CSV version
        let csv = 'Modelo,Gabarito\n'
        for (const variant of variants) {
            csv += `${variant.modelIdentifier},${variant.answerKey}\n`
        }
        zip.file('gabaritos.csv', csv)
    }

    // Package the ZIP
    onProgress?.({
        current: totalSteps,
        total: totalSteps,
        stage: 'packaging',
        message: 'Empacotando arquivos...',
    })

    const zipBlob = await zip.generateAsync({ type: 'blob' })

    onProgress?.({
        current: totalSteps,
        total: totalSteps,
        stage: 'complete',
        message: 'Exportação concluída!',
    })

    return zipBlob
}

/**
 * Exports and downloads the ZIP file
 */
export async function downloadExamZip(
    config: ExamConfig,
    options: ZipExportOptions,
    onProgress?: ProgressCallback
): Promise<void> {
    const zipBlob = await exportExamAsZip(config, options, onProgress)
    const filename = `${config.name.replace(/[^a-zA-Z0-9]/g, '_')}_provas.zip`
    saveAs(zipBlob, filename)
}

/**
 * Exports and uploads the ZIP file to Supabase Storage
 */
export async function uploadExamZip(
    config: ExamConfig,
    options: ZipExportOptions,
    userId: string,
    examId: string,
    onProgress?: ProgressCallback
): Promise<string> {
    const zipBlob = await exportExamAsZip(config, options, (progress) => {
        if (progress.stage !== 'complete') {
            onProgress?.(progress)
        }
    })

    onProgress?.({
        current: 1,
        total: 1,
        stage: 'uploading',
        message: 'Enviando para o servidor...',
    })

    const filename = `${config.name.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}.zip`
    const storagePath = `${userId}/${examId}/${filename}`

    const { error } = await supabase.storage
        .from('exports')
        .upload(storagePath, zipBlob, {
            contentType: 'application/zip',
            upsert: false,
        })

    if (error) {
        throw new Error(`Failed to upload ZIP: ${error.message}`)
    }

    onProgress?.({
        current: 1,
        total: 1,
        stage: 'complete',
        message: 'Upload concluído!',
    })

    return storagePath
}

export interface ZipExportService {
    exportExamAsZip: typeof exportExamAsZip
    downloadExamZip: typeof downloadExamZip
    uploadExamZip: typeof uploadExamZip
}

export const zipExportService: ZipExportService = {
    exportExamAsZip,
    downloadExamZip,
    uploadExamZip,
}

export default zipExportService
