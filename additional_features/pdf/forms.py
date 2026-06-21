import os
import fitz
from additional_features.contracts.pdf_extended import (
    PdfFillFormInput, PdfExtractFormOutput, ExtendedPdfResult
)

def pdf_fill_form(input_data: PdfFillFormInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "filled_form.pdf"
    doc = fitz.open(input_data.path)
    
    for page in doc:
        for widget in page.widgets():
            if widget.field_name in input_data.field_data:
                widget.field_value = input_data.field_data[widget.field_name]
                widget.update()
                
    doc.save(out_path)
    doc.close()
    return ExtendedPdfResult(out_path=out_path)

def pdf_extract_form(path: str) -> PdfExtractFormOutput:
    doc = fitz.open(path)
    data = {}
    
    for page in doc:
        for widget in page.widgets():
            if widget.field_name:
                data[widget.field_name] = widget.field_value
                
    doc.close()
    return PdfExtractFormOutput(field_data=data)
