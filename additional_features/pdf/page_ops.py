import os
import fitz
import pikepdf
from additional_features.contracts.pdf_extended import (
    PdfScaleInput, PdfCropInput, PdfRearrangeInput, 
    PdfLayoutInput, PdfBookletInput, PdfOverlayInput, ExtendedPdfResult
)

def pdf_scale(input_data: PdfScaleInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "scaled.pdf"
    doc = fitz.open(input_data.path)
    # Scale pages
    # We create a new doc, and for each page, we draw the old page onto a scaled rect
    new_doc = fitz.open()
    for page in doc:
        rect = page.rect
        new_rect = fitz.Rect(0, 0, rect.width * input_data.scale_factor, rect.height * input_data.scale_factor)
        new_page = new_doc.new_page(width=new_rect.width, height=new_rect.height)
        new_page.show_pdf_page(new_rect, doc, page.number)
    new_doc.save(out_path)
    new_doc.close()
    doc.close()
    return ExtendedPdfResult(out_path=out_path)

def pdf_crop(input_data: PdfCropInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "cropped.pdf"
    doc = fitz.open(input_data.path)
    for page in doc:
        # Set CropBox
        page.set_cropbox(fitz.Rect(input_data.x0, input_data.y0, input_data.x1, input_data.y1))
    doc.save(out_path)
    doc.close()
    return ExtendedPdfResult(out_path=out_path)

def pdf_rearrange(input_data: PdfRearrangeInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "rearranged.pdf"
    # page_order is 1-indexed, we need 0-indexed
    order = [p - 1 for p in input_data.page_order]
    
    with pikepdf.Pdf.open(input_data.path) as src_pdf:
        dst_pdf = pikepdf.Pdf.new()
        for i in order:
            if 0 <= i < len(src_pdf.pages):
                dst_pdf.pages.append(src_pdf.pages[i])
        dst_pdf.save(out_path)
    return ExtendedPdfResult(out_path=out_path)

def pdf_layout(input_data: PdfLayoutInput) -> ExtendedPdfResult:
    # N-up layout. E.g. 2 pages per sheet
    out_path = input_data.output_path or "layout.pdf"
    doc = fitz.open(input_data.path)
    new_doc = fitz.open()
    
    # Simple 2-up implementation (side-by-side)
    # A full robust implementation would handle arbitrary n_up (2, 4, 8)
    if input_data.n_up == 2:
        for i in range(0, len(doc), 2):
            p1 = doc[i]
            p2 = doc[i+1] if i+1 < len(doc) else None
            new_width = p1.rect.width * 2
            new_height = p1.rect.height
            new_page = new_doc.new_page(width=new_width, height=new_height)
            new_page.show_pdf_page(fitz.Rect(0, 0, p1.rect.width, new_height), doc, p1.number)
            if p2:
                new_page.show_pdf_page(fitz.Rect(p1.rect.width, 0, new_width, new_height), doc, p2.number)
    else:
        raise NotImplementedError("Only n_up=2 is implemented in this stub")
        
    new_doc.save(out_path)
    new_doc.close()
    doc.close()
    return ExtendedPdfResult(out_path=out_path)

def pdf_overlay(input_data: PdfOverlayInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "overlay.pdf"
    bg_doc = fitz.open(input_data.background_path)
    fg_doc = fitz.open(input_data.foreground_path)
    
    for i in range(min(len(bg_doc), len(fg_doc))):
        bg_page = bg_doc[i]
        fg_page = fg_doc[i]
        bg_page.show_pdf_page(bg_page.rect, fg_doc, fg_page.number)
        
    bg_doc.save(out_path)
    bg_doc.close()
    fg_doc.close()
    return ExtendedPdfResult(out_path=out_path)
