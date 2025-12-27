declare module 'qrious' {
    interface QRiousOptions {
        background?: string
        backgroundAlpha?: number
        element?: HTMLCanvasElement | HTMLImageElement
        foreground?: string
        foregroundAlpha?: number
        level?: 'L' | 'M' | 'Q' | 'H'
        mime?: string
        padding?: number
        size?: number
        value?: string
    }

    class QRious {
        constructor(options?: QRiousOptions)

        background: string
        backgroundAlpha: number
        foreground: string
        foregroundAlpha: number
        level: 'L' | 'M' | 'Q' | 'H'
        mime: string
        padding: number
        size: number
        value: string

        toDataURL(mime?: string): string
        toCanvas(canvas: HTMLCanvasElement): HTMLCanvasElement
        toImage(image: HTMLImageElement): HTMLImageElement
    }

    export default QRious
}
