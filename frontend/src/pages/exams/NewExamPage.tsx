import { zodResolver } from '@hookform/resolvers/zod'
import { useQuery } from '@tanstack/react-query'
import { Check, ChevronLeft, ChevronRight, FileText, Settings } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import QuestionEditor from '@/components/exam-builder/QuestionEditor'
import VariantConfigForm, { type VariantConfigFormValues } from '@/components/exam-builder/VariantConfigForm'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'
import { useAuth } from '@/contexts/AuthContext'
import { ExamBuilderProvider, useExamBuilder } from '@/contexts/ExamBuilderContext'
import { examBuilderService } from '@/services/examBuilderService'
import { examPersistenceService } from '@/services/examPersistenceService'
import { templateService } from '@/services/templateService'
import { toast } from 'sonner'

const steps = [
    { id: 1, name: 'Configuração', icon: Settings },
    { id: 2, name: 'Questões', icon: FileText },
    { id: 3, name: 'Revisão e Geração', icon: Check },
]

import { supabase } from '@/lib/supabase'

function NewExamWizard() {
    const { state, dispatch, addQuestion, updateQuestion, removeQuestion, addAlternative, updateAlternative, removeAlternative, setCorrectAlternative, addQuestionImage, removeQuestionImage, setAlternativeImage, getConfig } = useExamBuilder()
    const { user } = useAuth()
    const navigate = useNavigate()
    const [currentStep, setCurrentStep] = useState(1)
    const [isSaving, setIsSaving] = useState(false)
    const [draftId] = useState(() => crypto.randomUUID()) // Draft ID for image uploads

    // Fetch templates
    const { data: templates } = useQuery({
        queryKey: ['templates'],
        queryFn: async () => {
            const { data } = await templateService.list()
            return data || []
        },
    })

    // Step 1 Form
    const metaSchema = z.object({
        name: z.string().min(3, 'Nome deve ter pelo menos 3 caracteres'),
        templateId: z.string().min(1, 'Selecione um template'),
    })

    const metaForm = useForm<z.infer<typeof metaSchema>>({
        resolver: zodResolver(metaSchema),
        defaultValues: {
            name: state.name,
            templateId: state.templateId,
        },
    })

    const handleNextStep = async () => {
        if (currentStep === 1) {
            const isValid = await metaForm.trigger()
            if (isValid) {
                const values = metaForm.getValues()
                dispatch({ type: 'SET_NAME', payload: values.name })
                dispatch({ type: 'SET_TEMPLATE_ID', payload: values.templateId })
                setCurrentStep(2)
            }
        } else if (currentStep === 2) {
            if (state.questions.length === 0) {
                toast.error('Adicione pelo menos uma questão')
                return
            }
            // Basic validation for questions
            const invalidQuestions = state.questions.filter(q => !q.text.trim() || q.alternatives.some(a => !a.text.trim() && !a.image))
            if (invalidQuestions.length > 0) {
                toast.error('Preencha todos os campos das questões')
                return
            }
            setCurrentStep(3)
        }
    }

    const handlePrevStep = () => {
        setCurrentStep((prev) => Math.max(1, prev - 1))
    }

    const handleCreateExam = async (configValues: VariantConfigFormValues) => {
        if (!user?.id) return

        setIsSaving(true)
        try {
            // 1. Update state with final config
            dispatch({ type: 'SET_VARIANT_COUNT', payload: configValues.variantCount })
            dispatch({ type: 'SET_SHUFFLE_QUESTIONS', payload: configValues.shuffleQuestions })
            dispatch({ type: 'SET_SHUFFLE_ALTERNATIVES', payload: configValues.shuffleAlternatives })
            if (configValues.seed !== undefined) {
                dispatch({ type: 'SET_SEED', payload: configValues.seed })
            }

            // Get the updated config directly from the merged values to avoid stale state
            const finalConfig = {
                ...getConfig(),
                variantCount: configValues.variantCount,
                shuffleQuestions: configValues.shuffleQuestions,
                shuffleAlternatives: configValues.shuffleAlternatives,
                seed: configValues.seed,
            }

            // 2. Generate variants
            const variants = await examBuilderService.generateAllVariants(finalConfig)

            // 3. Generate DOCX files for each variant and upload to Supabase
            const docxStoragePaths = new Map<string, string>()

            for (const variant of variants) {
                // Generate binary
                const blob = await examBuilderService.generateVariantDocx(finalConfig, variant, false) // Question Paper

                // Generate filename/path: userId/draftId/VariantIdentifier.docx
                const storagePath = `${user.id}/${draftId}/${variant.modelIdentifier}.docx`

                // Upload
                const { error: uploadError } = await supabase.storage
                    .from('exam-documents')
                    .upload(storagePath, blob, {
                        contentType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        upsert: true
                    })

                if (uploadError) {
                    console.error('Failed to upload DOCX', uploadError)
                    throw new Error(`Falha ao gerar documento para modelo ${variant.modelIdentifier}`)
                }

                docxStoragePaths.set(variant.modelIdentifier, storagePath)
            }

            // 4. Save exam and variants to database
            const saveResult = await examPersistenceService.saveExam(finalConfig, user.id)
            await examPersistenceService.saveVariants(saveResult.examId, variants, docxStoragePaths)

            toast.success('Prova criada com sucesso!')
            navigate(`/exams/${saveResult.examId}`)

        } catch (error) {
            console.error(error)
            toast.error('Erro ao processar prova: ' + (error instanceof Error ? error.message : 'Erro desconhecido'))
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <div className="min-h-screen bg-background pb-20">
            <header className="sticky top-0 z-50 border-b border-white/10 bg-background/80 backdrop-blur-md">
                <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link to="/exams" className="text-muted-foreground hover:text-foreground">
                            <ChevronLeft className="h-5 w-5" />
                        </Link>
                        <h1 className="text-xl font-bold tracking-tight">Nova Prova</h1>
                    </div>
                </div>
            </header>

            <main className="container mx-auto px-4 py-8 max-w-5xl animate-fade-in-up">
                {/* Stepper */}
                <div className="flex items-center justify-center mb-12">
                    {steps.map((step, index) => (
                        <div key={step.id} className="flex items-center">
                            <div className={`flex flex-col items-center gap-2 ${currentStep >= step.id ? 'text-primary' : 'text-muted-foreground'}`}>
                                <div className={`flex h-10 w-10 items-center justify-center rounded-full border-2 transition-colors ${currentStep >= step.id
                                    ? 'border-primary bg-primary text-primary-foreground'
                                    : 'border-muted-foreground/30 bg-background'
                                    }`}>
                                    <step.icon className="h-5 w-5" />
                                </div>
                                <span className="text-sm font-medium">{step.name}</span>
                            </div>
                            {index < steps.length - 1 && (
                                <div className={`w-24 h-[2px] mx-4 mb-6 transition-colors ${currentStep > step.id ? 'bg-primary' : 'bg-muted-foreground/30'
                                    }`} />
                            )}
                        </div>
                    ))}
                </div>

                {/* Step Content */}
                <div className="mt-8">
                    {currentStep === 1 && (
                        <Card className="glass max-w-2xl mx-auto">
                            <CardHeader>
                                <CardTitle>Informações Básicas</CardTitle>
                                <CardDescription>Defina o nome e o template da sua prova</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <Form {...metaForm}>
                                    <form className="space-y-6">
                                        <FormField
                                            control={metaForm.control}
                                            name="name"
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>Nome da Prova</FormLabel>
                                                    <FormControl>
                                                        <Input placeholder="Ex: Prova de Matemática - 1º Bimestre" {...field} />
                                                    </FormControl>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />

                                        <FormField
                                            control={metaForm.control}
                                            name="templateId"
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>Template (Folha de Resposta)</FormLabel>
                                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                                                        <FormControl>
                                                            <SelectTrigger>
                                                                <SelectValue placeholder="Selecione um template" />
                                                            </SelectTrigger>
                                                        </FormControl>
                                                        <SelectContent>
                                                            {templates?.map((template) => (
                                                                <SelectItem key={template.id} value={template.id}>
                                                                    {template.name} ({template.question_count} questões)
                                                                </SelectItem>
                                                            ))}
                                                        </SelectContent>
                                                    </Select>
                                                    <FormDescription className="text-xs">
                                                        O template define quantas questões a prova deve ter.
                                                    </FormDescription>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                    </form>
                                </Form>
                            </CardContent>
                        </Card>
                    )}

                    {currentStep === 2 && (
                        <div className="space-y-8">
                            <div className="flex items-center justify-between">
                                <h2 className="text-2xl font-bold">Questões</h2>
                                <Button onClick={() => addQuestion()} size="lg" className="shadow-md shadow-primary/20">
                                    <FileText className="mr-2 h-4 w-4" />
                                    Adicionar Questão
                                </Button>
                            </div>

                            <div className="grid gap-6">
                                {state.questions.map((question, index) => (
                                    <QuestionEditor
                                        key={question.id}
                                        question={question}
                                        examId={draftId} // Use draftId for image storage path
                                        onUpdate={(q) => updateQuestion(index, q)}
                                        onRemove={() => removeQuestion(index)}
                                        onAddAlternative={() => addAlternative(index)}
                                        onUpdateAlternative={(altIndex, alt) => updateAlternative(index, altIndex, alt)}
                                        onRemoveAlternative={(altIndex) => removeAlternative(index, altIndex)}
                                        onSetCorrectAlternative={(altIndex) => setCorrectAlternative(index, altIndex)}
                                        onAddImage={(img) => addQuestionImage(index, img)}
                                        onRemoveImage={(imgId) => removeQuestionImage(index, imgId)}
                                        onSetAlternativeImage={(altIndex, img) => setAlternativeImage(index, altIndex, img)}
                                    />
                                ))}

                                {state.questions.length === 0 && (
                                    <div className="text-center py-12 border-2 border-dashed rounded-xl border-muted-foreground/20">
                                        <p className="text-muted-foreground mb-4">Nenhuma questão adicionada</p>
                                        <Button variant="outline" onClick={() => addQuestion()}>
                                            Adicionar Primeira Questão
                                        </Button>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {currentStep === 3 && (
                        <div className="max-w-2xl mx-auto space-y-6">
                            <Card className="glass">
                                <CardHeader>
                                    <CardTitle>Revisão</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <p className="text-sm font-medium text-muted-foreground">Nome da Prova</p>
                                            <p className="text-lg">{state.name}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-muted-foreground">Template</p>
                                            <p className="text-lg">
                                                {templates?.find(t => t.id === state.templateId)?.name || 'Desconhecido'}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-muted-foreground">Questões</p>
                                            <p className="text-lg">{state.questions.length}</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            <VariantConfigForm
                                onSubmit={handleCreateExam}
                                isGenerating={isSaving}
                                questionCount={state.questions.length}
                                defaultValues={{
                                    variantCount: state.variantCount,
                                    shuffleQuestions: state.shuffleQuestions,
                                    shuffleAlternatives: state.shuffleAlternatives,
                                    seed: state.seed
                                }}
                            />
                        </div>
                    )}
                </div>

                {/* Navigation Buttons */}
                <div className="fixed bottom-0 left-0 right-0 p-4 bg-background/80 backdrop-blur-md border-t border-white/10 z-40">
                    <div className="container mx-auto max-w-5xl flex justify-between">
                        <Button
                            variant="outline"
                            onClick={handlePrevStep}
                            disabled={currentStep === 1 || isSaving}
                        >
                            <ChevronLeft className="mr-2 h-4 w-4" />
                            Voltar
                        </Button>

                        {currentStep < 3 ? (
                            <Button onClick={handleNextStep}>
                                Próximo
                                <ChevronRight className="ml-2 h-4 w-4" />
                            </Button>
                        ) : null}
                    </div>
                </div>
            </main>
        </div>
    )
}

export function NewExamPage() {
    return (
        <ExamBuilderProvider>
            <NewExamWizard />
        </ExamBuilderProvider>
    )
}
