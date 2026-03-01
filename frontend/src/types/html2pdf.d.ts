declare module 'html2pdf.js' {
  interface Html2PdfOptions {
    margin?: number | number[]
    filename?: string
    image?: { type: string; quality: number }
    html2canvas?: { scale: number; [key: string]: any }
    jsPDF?: { unit: string; format: string; orientation: string; [key: string]: any }
    [key: string]: any
  }

  interface Html2Pdf {
    set(options: Html2PdfOptions): Html2Pdf
    from(element: Element | string): Html2Pdf
    save(): Promise<void>
    output(type: string, options?: any): Promise<any>
    outputPdf(type?: string): Promise<any>
    outputImg(type?: string): Promise<any>
  }

  function html2pdf(): Html2Pdf

  export default html2pdf
}
