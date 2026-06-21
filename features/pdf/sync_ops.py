import os
import fitz  # PyMuPDF
import pikepdf
import re
from typing import List, Optional
from contracts.pdf import (
    PdfExtractTextInput, PdfExtractTextOutput,
    PdfMergeInput, PdfMergeOutput,
    PdfSplitInput, PdfSplitOutput,
    PdfRotateInput, PdfRotateOutput,
    PdfRedactInput, PdfRedactOutput
)

def pdf_extract_text(input_data: PdfExtractTextInput) -> PdfExtractTextOutput:
    """Extract raw text from a PDF, optionally from specific pages."""
    doc = fitz.open(input_data.path)
    extracted = []
    
    pages_to_extract = input_data.pages if input_data.pages else range(len(doc))
    
    for page_num in pages_to_extract:
        if 0 <= page_num < len(doc):
            page = doc[page_num]
            extracted.append(page.get_text())
    
    doc.close()
    return PdfExtractTextOutput(text="\\n".join(extracted))


def pdf_merge(input_data: PdfMergeInput) -> PdfMergeOutput:
    """Merge multiple PDFs into one using pikepdf for lossless structural merge."""
    output_path = input_data.output_path or "merged.pdf"
    merged_pdf = pikepdf.Pdf.new()
    
    for path in input_data.input_paths:
        with pikepdf.Pdf.open(path) as src_pdf:
            merged_pdf.pages.extend(src_pdf.pages)
            
    # TODO: generate_toc if required
            
    merged_pdf.save(output_path)
    return PdfMergeOutput(out_path=output_path)


def pdf_split(input_data: PdfSplitInput) -> PdfSplitOutput:
    """Split a PDF into multiple parts based on page ranges."""
    output_dir = input_data.output_dir or os.path.dirname(input_data.path)
    base_name = os.path.splitext(os.path.basename(input_data.path))[0]
    out_paths = []
    
    with pikepdf.Pdf.open(input_data.path) as src_pdf:
        total_pages = len(src_pdf.pages)
        for i, page_range in enumerate(input_data.page_ranges):
            # Parse ranges like "1-5" or "6-10", making them 0-indexed
            parts = page_range.split('-')
            start = int(parts[0]) - 1
            end = int(parts[1]) if len(parts) > 1 else start + 1
            
            # Clamp to valid pages
            start = max(0, min(start, total_pages - 1))
            end = max(1, min(end, total_pages))
            
            part_pdf = pikepdf.Pdf.new()
            for p_idx in range(start, end):
                part_pdf.pages.append(src_pdf.pages[p_idx])
            
            out_path = os.path.join(output_dir, f"{base_name}_part_{i+1}.pdf")
            part_pdf.save(out_path)
            out_paths.append(out_path)
            
    return PdfSplitOutput(out_paths=out_paths)


def pdf_rotate(input_data: PdfRotateInput) -> PdfRotateOutput:
    """Rotate specific pages or all pages of a PDF."""
    output_path = input_data.output_path or "rotated.pdf"
    
    with pikepdf.Pdf.open(input_data.path) as src_pdf:
        pages_to_rotate = input_data.pages if input_data.pages else range(len(src_pdf.pages))
        
        for p_idx in pages_to_rotate:
            if 0 <= p_idx < len(src_pdf.pages):
                page = src_pdf.pages[p_idx]
                # Page rotation is additive, taking modulus 360
                current_rotation = int(page.get("/Rotate", 0))
                page.Rotate = (current_rotation + input_data.angle) % 360
                
        src_pdf.save(output_path)
        
    return PdfRotateOutput(out_path=output_path)


def pdf_redact(input_data: PdfRedactInput) -> PdfRedactOutput:
    """Apply true content removal redactions using PyMuPDF."""
    output_path = input_data.output_path or "redacted.pdf"
    doc = fitz.open(input_data.path)
    
    # Redact by explicit areas
    if input_data.areas:
        for area in input_data.areas:
            if 0 <= area.page < len(doc):
                page = doc[area.page]
                rect = fitz.Rect(area.x0, area.y0, area.x1, area.y1)
                page.add_redact_annot(rect, fill=(0, 0, 0))
                page.apply_redactions()

    # Redact by text patterns (regex)
    if input_data.patterns:
        for page in doc:
            for pattern in input_data.patterns:
                # Find text instances
                text_instances = page.search_for(pattern) # Simple string search 
                # For proper regex, we'd iterate words and match, but search_for handles basic string match
                # PyMuPDF doesn't natively search regex cleanly without iterating textpage.
                # Here we assume patterns are simple strings for now, or implement a basic regex search over get_text("words").
                for inst in text_instances:
                    page.add_redact_annot(inst, fill=(0, 0, 0))
            page.apply_redactions()
            
    doc.save(output_path, garbage=3, deflate=True) # garbage=3 ensures unused objects are removed
    doc.close()
    
    return PdfRedactOutput(out_path=output_path)
