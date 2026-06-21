import os
import fitz
import pikepdf
import subprocess
from additional_features.contracts.pdf_extended import (
    PdfCompressInput, PdfRepairInput, PdfMetadataInput, 
    PdfAttachmentInput, PdfFlattenInput, ExtendedPdfResult
)

def pdf_compress(input_data: PdfCompressInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "compressed.pdf"
    # Uses ghostscript for heavy compression
    gs_settings = f"/default" # screen, ebook, printer, prepress
    if input_data.level in ["screen", "ebook", "printer", "prepress"]:
        gs_settings = f"/{input_data.level}"
        
    cmd = [
        "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={gs_settings}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={out_path}", input_data.path
    ]
    subprocess.run(cmd, check=True)
    return ExtendedPdfResult(out_path=out_path)

def pdf_repair(input_data: PdfRepairInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "repaired.pdf"
    # qpdf is excellent at repairing corrupt PDF streams
    subprocess.run(["qpdf", "--replace-input", input_data.path, out_path], check=True)
    return ExtendedPdfResult(out_path=out_path)

def pdf_metadata(input_data: PdfMetadataInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "metadata.pdf"
    doc = fitz.open(input_data.path)
    meta = doc.metadata
    
    if input_data.title is not None:
        meta['title'] = input_data.title
    if input_data.author is not None:
        meta['author'] = input_data.author
    if input_data.subject is not None:
        meta['subject'] = input_data.subject
        
    doc.set_metadata(meta)
    doc.save(out_path)
    doc.close()
    return ExtendedPdfResult(out_path=out_path)

def pdf_attachment(input_data: PdfAttachmentInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "attached.pdf"
    doc = fitz.open(input_data.path)
    
    for att_path in input_data.attachment_paths:
        with open(att_path, "rb") as f:
            att_data = f.read()
        basename = os.path.basename(att_path)
        doc.embfile_add(basename, att_data)
        
    doc.save(out_path)
    doc.close()
    return ExtendedPdfResult(out_path=out_path)

def pdf_flatten(input_data: PdfFlattenInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "flattened.pdf"
    doc = fitz.open(input_data.path)
    
    for page in doc:
        for annot in page.annots():
            page.delete_annot(annot)
        for widget in page.widgets():
            page.delete_widget(widget)
            
    doc.save(out_path)
    doc.close()
    return ExtendedPdfResult(out_path=out_path)
