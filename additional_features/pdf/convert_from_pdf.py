import os
import fitz
import subprocess
from additional_features.contracts.pdf_extended import (
    PdfToImagesInput, PdfToOfficeInput, PdfToTabularInput, 
    ExtendedPdfResult, ExtendedPdfResultList
)

def pdf_to_images(input_data: PdfToImagesInput) -> ExtendedPdfResultList:
    out_dir = input_data.output_dir or "."
    doc = fitz.open(input_data.path)
    out_paths = []
    
    # Calculate matrix for DPI
    zoom = input_data.dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    
    base_name = os.path.splitext(os.path.basename(input_data.path))[0]
    
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        out_path = os.path.join(out_dir, f"{base_name}_page_{page.number + 1}.png")
        pix.save(out_path)
        out_paths.append(out_path)
        
    doc.close()
    return ExtendedPdfResultList(out_paths=out_paths)

def pdf_to_office(input_data: PdfToOfficeInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or f"output.{input_data.format}"
    if input_data.format == "docx":
        from pdf2docx import Converter
        cv = Converter(input_data.path)
        cv.convert(out_path)
        cv.close()
    else:
        # PPTX requires more complex libraries like python-pptx or routing through libreoffice/other tools
        raise NotImplementedError("Only docx conversion is directly supported via pdf2docx stub.")
        
    return ExtendedPdfResult(out_path=out_path)

def pdf_to_tabular(input_data: PdfToTabularInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or f"output.{input_data.format}"
    import tabula
    
    if input_data.format == "csv":
        tabula.convert_into(input_data.path, out_path, output_format="csv", pages='all')
    elif input_data.format == "xlsx":
        # Usually tabula handles CSV, we might need to convert CSV to XLSX via pandas
        import pandas as pd
        dfs = tabula.read_pdf(input_data.path, pages='all')
        with pd.ExcelWriter(out_path) as writer:
            for i, df in enumerate(dfs):
                df.to_excel(writer, sheet_name=f'Table_{i+1}', index=False)
    else:
        raise ValueError(f"Unsupported tabular format: {input_data.format}")
        
    return ExtendedPdfResult(out_path=out_path)
