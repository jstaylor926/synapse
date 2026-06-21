import os
import fitz
import subprocess
from additional_features.contracts.pdf_extended import (
    ImgToPdfInput, HtmlToPdfInput, EbookToPdfInput, 
    OfficeToPdfInput, SvgToPdfInput, ExtendedPdfResult
)

def img_to_pdf(input_data: ImgToPdfInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "images.pdf"
    doc = fitz.open()
    for img_path in input_data.input_paths:
        img_doc = fitz.open(img_path)
        pdf_bytes = img_doc.convert_to_pdf()
        img_pdf = fitz.open("pdf", pdf_bytes)
        doc.insert_pdf(img_pdf)
        img_doc.close()
        img_pdf.close()
    doc.save(out_path)
    doc.close()
    return ExtendedPdfResult(out_path=out_path)

def html_to_pdf(input_data: HtmlToPdfInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "html.pdf"
    import weasyprint
    weasyprint.HTML(string=input_data.html_content).write_pdf(out_path)
    return ExtendedPdfResult(out_path=out_path)

def ebook_to_pdf(input_data: EbookToPdfInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or f"{input_data.path}.pdf"
    # Uses calibre's ebook-convert tool
    subprocess.run(["ebook-convert", input_data.path, out_path], check=True)
    return ExtendedPdfResult(out_path=out_path)

def office_to_pdf(input_data: OfficeToPdfInput) -> ExtendedPdfResult:
    out_dir = os.path.dirname(input_data.output_path) if input_data.output_path else "."
    # Uses libreoffice headless
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", out_dir, input_data.path], check=True)
    # soffice generates a file with the same basename but .pdf extension
    base_name = os.path.splitext(os.path.basename(input_data.path))[0]
    expected_out = os.path.join(out_dir, f"{base_name}.pdf")
    
    if input_data.output_path and expected_out != input_data.output_path:
        os.rename(expected_out, input_data.output_path)
        
    return ExtendedPdfResult(out_path=input_data.output_path or expected_out)

def svg_to_pdf(input_data: SvgToPdfInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "svg.pdf"
    import cairosvg
    cairosvg.svg2pdf(url=input_data.path, write_to=out_path)
    return ExtendedPdfResult(out_path=out_path)
