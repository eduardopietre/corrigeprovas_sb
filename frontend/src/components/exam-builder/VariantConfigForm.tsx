/**
 * VariantConfigForm - Configuration form for exam variant generation
 * Requirements: 15.1, 15.5, 15.6
 */

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
import { Switch } from '@/components/ui/switch'
import { zodResolver } from '@hookform/resolvers/zod'
import { Download, FileText, Shuffle } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

const variantConfigSchema = z.object({
    variantCount: z.number().min(1).max(26),
    shuffleQuestions: z.boolean(),
    shuffleAlternatives: z.boolean(),
    seed: z.number().optional(),
    includeAnswerKey: z.boolean(),
})

export type VariantConfigFormValues = z.infer<typeof variantConfigSchema>

export interface VariantConfigFormProps {
    defaultValues?: Partial<VariantConfigFormValues>
    onSubmit: (values: VariantConfigFormValues) => void
    isGenerating?: boolean
    questionCount: number
}

export function VariantConfigForm({
    defaultValues,
    onSubmit,
    isGenerating = false,
    questionCount,
}: VariantConfigFormProps) {
    const form = useForm<VariantConfigFormValues>({
        resolver: zodResolver(variantConfigSchema),
        defaultValues: {
            variantCount: 1,
            shuffleQuestions: false,
            shuffleAlternatives: false,
            seed: undefined,
            includeAnswerKey: true,
            ...defaultValues,
        },
    })

    const variantOptions = Array.from({ length: 26 }, (_, i) => ({
        value: i + 1,
        label: `${i + 1} ${i === 0 ? 'variante' : 'variantes'} (${String.fromCharCode(65 + i)})`,
    }))

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Shuffle className="h-5 w-5" />
                    Configuração de Variantes
                </CardTitle>
                <CardDescription>
                    Configure como as variantes da prova serão geradas
                </CardDescription>
            </CardHeader>
            <CardContent>
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                        {/* Variant count */}
                        <FormField
                            control={form.control}
                            name="variantCount"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Número de Variantes</FormLabel>
                                    <Select
                                        onValueChange={(value) => field.onChange(parseInt(value))}
                                        defaultValue={field.value.toString()}
                                    >
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Selecione o número de variantes" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            {variantOptions.map((option) => (
                                                <SelectItem
                                                    key={option.value}
                                                    value={option.value.toString()}
                                                >
                                                    {option.label}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <FormDescription>
                                        Cada variante terá um identificador único (A, B, C, ...)
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {/* Shuffle questions */}
                        <FormField
                            control={form.control}
                            name="shuffleQuestions"
                            render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                    <div className="space-y-0.5">
                                        <FormLabel className="text-base">
                                            Embaralhar Questões
                                        </FormLabel>
                                        <FormDescription>
                                            A ordem das questões será diferente em cada variante
                                        </FormDescription>
                                    </div>
                                    <FormControl>
                                        <Switch
                                            checked={field.value}
                                            onCheckedChange={field.onChange}
                                            disabled={questionCount < 2}
                                        />
                                    </FormControl>
                                </FormItem>
                            )}
                        />

                        {/* Shuffle alternatives */}
                        <FormField
                            control={form.control}
                            name="shuffleAlternatives"
                            render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                    <div className="space-y-0.5">
                                        <FormLabel className="text-base">
                                            Embaralhar Alternativas
                                        </FormLabel>
                                        <FormDescription>
                                            A ordem das alternativas será diferente em cada variante
                                        </FormDescription>
                                    </div>
                                    <FormControl>
                                        <Switch
                                            checked={field.value}
                                            onCheckedChange={field.onChange}
                                        />
                                    </FormControl>
                                </FormItem>
                            )}
                        />

                        {/* Include answer key */}
                        <FormField
                            control={form.control}
                            name="includeAnswerKey"
                            render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                    <div className="space-y-0.5">
                                        <FormLabel className="text-base">
                                            Incluir Gabarito
                                        </FormLabel>
                                        <FormDescription>
                                            Adiciona uma página com o gabarito em cada documento
                                        </FormDescription>
                                    </div>
                                    <FormControl>
                                        <Switch
                                            checked={field.value}
                                            onCheckedChange={field.onChange}
                                        />
                                    </FormControl>
                                </FormItem>
                            )}
                        />

                        {/* Seed (optional, for advanced users) */}
                        <FormField
                            control={form.control}
                            name="seed"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Semente (opcional)</FormLabel>
                                    <FormControl>
                                        <Input
                                            type="number"
                                            placeholder="Deixe em branco para gerar automaticamente"
                                            {...field}
                                            value={field.value ?? ''}
                                            onChange={(e) => {
                                                const value = e.target.value
                                                field.onChange(value ? parseInt(value) : undefined)
                                            }}
                                        />
                                    </FormControl>
                                    <FormDescription>
                                        Use a mesma semente para reproduzir exatamente as mesmas variantes
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {/* Summary */}
                        <div className="rounded-lg bg-muted p-4 space-y-2">
                            <h4 className="font-medium flex items-center gap-2">
                                <FileText className="h-4 w-4" />
                                Resumo
                            </h4>
                            <ul className="text-sm text-muted-foreground space-y-1">
                                <li>• {questionCount} questões</li>
                                <li>• {form.watch('variantCount')} variante(s) será(ão) gerada(s)</li>
                                <li>
                                    • Questões {form.watch('shuffleQuestions') ? 'serão' : 'não serão'} embaralhadas
                                </li>
                                <li>
                                    • Alternativas {form.watch('shuffleAlternatives') ? 'serão' : 'não serão'} embaralhadas
                                </li>
                            </ul>
                        </div>

                        {/* Submit button */}
                        <Button
                            type="submit"
                            className="w-full"
                            disabled={isGenerating || questionCount === 0}
                        >
                            <Download className="h-4 w-4 mr-2" />
                            {isGenerating ? 'Gerando...' : 'Gerar Variantes'}
                        </Button>
                    </form>
                </Form>
            </CardContent>
        </Card>
    )
}

export default VariantConfigForm
