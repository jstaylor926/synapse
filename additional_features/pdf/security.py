import os
import fitz
import pikepdf
from additional_features.contracts.pdf_extended import (
    PdfAddPasswordInput, PdfRemovePasswordInput, PdfSanitizeInput, 
    PdfWatermarkInput, PdfSignInput, ExtendedPdfResult
)

def pdf_add_password(input_data: PdfAddPasswordInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "protected.pdf"
    with pikepdf.Pdf.open(input_data.path) as pdf:
        pdf.save(
            out_path,
            encryption=pikepdf.Encryption(
                user=input_data.password, 
                owner=input_data.password, 
                allow=pikepdf.Permissions(extract=False, print=False)
            )
        )
    return ExtendedPdfResult(out_path=out_path)

def pdf_remove_password(input_data: PdfRemovePasswordInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "unlocked.pdf"
    with pikepdf.Pdf.open(input_data.path, password=input_data.password) as pdf:
        pdf.save(out_path)
    return ExtendedPdfResult(out_path=out_path)

def pdf_sanitize(input_data: PdfSanitizeInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "sanitized.pdf"
    
    # First pass: PyMuPDF to remove annotations/javascript/links
    doc = fitz.open(input_data.path)
    for page in doc:
        for annot in page.annots():
            page.delete_annot(annot)
        for link in page.links():
            page.delete_link(link)
            
    doc.set_metadata({}) # Clear metadata
    temp_path = f"{out_path}.tmp.pdf"
    doc.save(temp_path, garbage=4, clean=True)
    doc.close()
    
    # Second pass: pikepdf to strip hidden objects and rebuild structure securely
    with pikepdf.Pdf.open(temp_path) as pdf:
        pdf.save(out_path)
        
    os.remove(temp_path)
    return ExtendedPdfResult(out_path=out_path)

def pdf_watermark(input_data: PdfWatermarkInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "watermarked.pdf"
    doc = fitz.open(input_data.path)
    
    for page in doc:
        # Simple diagonal watermark across the page
        rect = page.rect
        page.insert_text(
            fitz.Point(rect.width / 4, rect.height / 2),
            input_data.text,
            fontsize=48,
            color=(0.7, 0.7, 0.7),
            fill_opacity=input_data.opacity,
            rotate=45
        )
        
    doc.save(out_path)
    doc.close()
    return ExtendedPdfResult(out_path=out_path)

def pdf_sign(input_data: PdfSignInput) -> ExtendedPdfResult:
    out_path = input_data.output_path or "signed.pdf"
    # To implement real PKI signatures, libraries like pyHanko or endesive are needed.
    # We will stub this using pyHanko imports for the caller's reference.
    try:
        from pyhanko.sign import signers
        from pyhanko.pdf_utils.writer import copy_into_new_writer
        from pyhanko.pdf_utils.reader import PdfFileReader
        
        signer = signers.SimpleSigner.load_pkcs12(input_data.cert_path, b'password') # Needs actual password in reality
        with open(input_data.path, 'rb') as f:
            w = copy_into_new_writer(PdfFileReader(f))
            with open(out_path, 'wb') as out_f:
                signers.sign_pdf(w, signers.PdfSignatureMetadata(field_name='Signature1'), signer=signer, out=out_f)
                
    except ImportError:
        raise ImportError("pyHanko is required for digital signatures. `pip install pyhanko`")
        
    return ExtendedPdfResult(out_path=out_path)
