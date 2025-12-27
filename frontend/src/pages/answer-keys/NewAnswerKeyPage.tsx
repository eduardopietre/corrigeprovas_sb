import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { Alert, AlertDescription } from '@/components/ui/alert'
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
import { supabase } from '@/lib/supabase'
import { answerKeyService } from '@/services'
import type { Template } from '@/services/types'

const answerKeySchema = z.object({
    name: z.string().min(1, 'Nome é obrigatório'),
    templateId: z.string().uuid('Selecione um template'),
    answersString: z.string().min(1, 'Respostas são obrigatórias'),
})

type AnswerKeyFormValues = z.infer<typeof answerKeySchema>

export function NewAnswerKeyPage() {
    const navigate = useNavigate()
    const [templates, setTemplates] = useState<Template[]>([])
    const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [validationError, setValidationError] = useState<string | null>(null)

    const form = useForm<AnswerKeyFormValues>({
        resolver: zodResolver(answerKeySchema),
        defaultValues: {
            name: '',
            templateId: '',
            answersString: '',
        },
    })

    // Load templates
    useEffect(() => {
        async function loadTemplates() {
            const { data, error } = await supabase
                .from('templates')
                .select('*')
                .eq('is_active', true)
                .order('name')

            if (error) {
                setError('Erro ao carregar templates.')
            } else {
                setTemplates(data as Template[])
            }
            setIsLoading(false)
        }

        loadTemplates()
    }, [])

    // Update selected template when templateId changes
    const templateId = form.watch('templateId')
    useEffect(() => {
        const template = templates.find((t) => t.id === templateId)
        setSelectedTemplate(template || null)
        setValidationError(null)
    }, [templateId, templates])

    // Validate answers string on change
    const answersString = form.watch('answersString')
    useEffect(() => {
        if (!selectedTemplate || !answersString) {
            setValidationError(null)
            return
        }

        const result = answerKeyService.validateAnswersString(answersString, selectedTemplate)
        setValidationError(result.valid ? null : result.error || null)
    }, [answersString, selectedTemplate])

    const onSubmit = async (values: AnswerKeyFormValues) => {
        if (!selectedTemplate) {
            setError('Selecione um template.')
            return
        }

        // Final validation
        const validation = answerKeyService.validateAnswersString(values.answersString, selectedTemplate)
        if (!validation.valid) {
            setValidationError(validation.error || 'Gabarito inválido.')
            return
        }

        setError(null)
        setIsSubmitting(true)

        try {
            const { error } = await answerKeyService.create({
                templateId: values.templateId,
                answersString: values.answersString,
                name: values.name,
            })

            if (error) {
                setError(error.message)
            } else {
                navigate('/answer-keys')
            }
        } catch {
            setError('Erro ao criar gabarito.')
        } finally {
            setIsSubmitting(false)
        }
    }

    const getValidChars = () => {
        if (!selectedTemplate) return 'A, B, C, D, E'
        return 'ABCDE'.slice(0, selectedTemplate.alternatives_count).split('').join(', ')
    }

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b">
                <div className="container mx-auto px-4 py-4 flex items-center gap-4">
                    <Button variant="ghost" size="icon" asChild>
                        <Link to="/answer-keys">
                            <ArrowLeft className="h-5 w-5" />
                        </Link>
                    </Button>
                    <h1 className="text-xl font-bold">Novo Gabarito</h1>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-4 py-8 max-w-2xl">
                {error && (
                    <Alert variant="destructive" className="mb-6">
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                <Card>
                    <CardHeader>
                        <CardTitle>Criar Gabarito</CardTitle>
                        <CardDescription>
                            Defina as respostas corretas para uma prova
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Form {...form}>
                            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                                <FormField
                                    control={form.control}
                                    name="name"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Nome do Gabarito</FormLabel>
                                            <FormControl>
                                                <Input
                                                    placeholder="Ex: Prova de Matemática - 1º Bimestre"
                                                    {...field}
                                                />
                                            </FormControl>
                                            <FormDescription>
                                                Um nome para identificar este gabarito
                                            </FormDescription>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />

                                <FormField
                                    control={form.control}
                                    name="templateId"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Template</FormLabel>
                                            <Select
                                                onValueChange={field.onChange}
                                                defaultValue={field.value}
                                                disabled={isLoading}
                                            >
                                                <FormControl>
                                                    <SelectTrigger>
                                                        <SelectValue placeholder="Selecione um template" />
                                                    </SelectTrigger>
                                                </FormControl>
                                                <SelectContent>
                                                    {templates.map((template) => (
                                                        <SelectItem key={template.id} value={template.id}>
                                                            {template.name} ({template.question_count} questões, {template.alternatives_count} alternativas)
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                            <FormDescription>
                                                O modelo de folha de resposta que será usado
                                            </FormDescription>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />

                                <FormField
                                    control={form.control}
                                    name="answersString"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Respostas</FormLabel>
                                            <FormControl>
                                                <Input
                                                    placeholder={selectedTemplate ? `Ex: ${'ABCDE'.slice(0, selectedTemplate.alternatives_count).repeat(Math.ceil(selectedTemplate.question_count / selectedTemplate.alternatives_count)).slice(0, selectedTemplate.question_count)}` : 'Selecione um template primeiro'}
                                                    {...field}
                                                    onChange={(e) => field.onChange(e.target.value.toUpperCase())}
                                                    disabled={!selectedTemplate}
                                                    className="font-mono tracking-wider"
                                                />
                                            </FormControl>
                                            <FormDescription>
                                                {selectedTemplate ? (
                                                    <>
                                                        Digite {selectedTemplate.question_count} respostas usando apenas: {getValidChars()}
                                                        <br />
                                                        <span className="text-xs">
                                                            Digitado: {answersString.length} / {selectedTemplate.question_count}
                                                        </span>
                                                    </>
                                                ) : (
                                                    'Selecione um template para definir as respostas'
                                                )}
                                            </FormDescription>
                                            {validationError && (
                                                <p className="text-sm text-destructive">{validationError}</p>
                                            )}
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />

                                {/* Preview */}
                                {selectedTemplate && answersString.length > 0 && (
                                    <div className="p-4 bg-muted rounded-lg">
                                        <p className="text-sm font-medium mb-2">Prévia do Gabarito:</p>
                                        <div className="grid grid-cols-10 gap-1 text-xs font-mono">
                                            {answersString.split('').map((char, index) => (
                                                <div
                                                    key={index}
                                                    className={`p-1 text-center rounded ${'ABCDE'.slice(0, selectedTemplate.alternatives_count).includes(char)
                                                        ? 'bg-green-100 text-green-800'
                                                        : 'bg-red-100 text-red-800'
                                                        }`}
                                                >
                                                    <span className="block text-[10px] text-muted-foreground">{index + 1}</span>
                                                    {char}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                <div className="flex gap-4">
                                    <Button
                                        type="button"
                                        variant="outline"
                                        className="flex-1"
                                        asChild
                                    >
                                        <Link to="/answer-keys">Cancelar</Link>
                                    </Button>
                                    <Button
                                        type="submit"
                                        className="flex-1"
                                        disabled={isSubmitting || !!validationError}
                                    >
                                        {isSubmitting ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Criando...
                                            </>
                                        ) : (
                                            'Criar Gabarito'
                                        )}
                                    </Button>
                                </div>
                            </form>
                        </Form>
                    </CardContent>
                </Card>
            </main>
        </div>
    )
}
