from typing import List, Optional, Any, Dict
from pydantic import BaseModel

class ExtendedPdfResult(BaseModel):
    out_path: str

class ExtendedPdfResultList(BaseModel):
    out_paths: List[str]

# 1. Page Operations
class PdfScaleInput(BaseModel):
    path: str
    scale_factor: float
    output_path: Optional[str] = None

class PdfCropInput(BaseModel):
    path: str
    x0: float
    y0: float
    x1: float
    y1: float
    output_path: Optional[str] = None

class PdfRearrangeInput(BaseModel):
    path: str
    page_order: List[int] # e.g., [2, 1, 3]
    output_path: Optional[str] = None

class PdfLayoutInput(BaseModel):
    path: str
    n_up: int # 2, 4, 8, etc.
    output_path: Optional[str] = None

class PdfBookletInput(BaseModel):
    path: str
    output_path: Optional[str] = None

class PdfOverlayInput(BaseModel):
    background_path: str
    foreground_path: str
    output_path: Optional[str] = None

# 2. Converters To PDF
class ImgToPdfInput(BaseModel):
    input_paths: List[str]
    output_path: Optional[str] = None

class HtmlToPdfInput(BaseModel):
    html_content: str
    output_path: Optional[str] = None

class EbookToPdfInput(BaseModel):
    path: str
    output_path: Optional[str] = None

class OfficeToPdfInput(BaseModel):
    path: str
    output_path: Optional[str] = None

class SvgToPdfInput(BaseModel):
    path: str
    output_path: Optional[str] = None

# 3. Converters From PDF
class PdfToImagesInput(BaseModel):
    path: str
    dpi: int = 300
    output_dir: Optional[str] = None

class PdfToOfficeInput(BaseModel):
    path: str
    format: str = "docx" # or pptx
    output_path: Optional[str] = None

class PdfToTabularInput(BaseModel):
    path: str
    format: str = "csv" # or xlsx
    output_path: Optional[str] = None

# 4. Security
class PdfAddPasswordInput(BaseModel):
    path: str
    password: str
    output_path: Optional[str] = None

class PdfRemovePasswordInput(BaseModel):
    path: str
    password: str
    output_path: Optional[str] = None

class PdfSanitizeInput(BaseModel):
    path: str
    output_path: Optional[str] = None

class PdfWatermarkInput(BaseModel):
    path: str
    text: str
    opacity: float = 0.5
    output_path: Optional[str] = None

class PdfSignInput(BaseModel):
    path: str
    cert_path: str
    key_path: str
    output_path: Optional[str] = None

# 5. Misc
class PdfCompressInput(BaseModel):
    path: str
    level: str = "screen" # screen, ebook, printer, prepress
    output_path: Optional[str] = None

class PdfRepairInput(BaseModel):
    path: str
    output_path: Optional[str] = None

class PdfMetadataInput(BaseModel):
    path: str
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    output_path: Optional[str] = None

class PdfAttachmentInput(BaseModel):
    path: str
    attachment_paths: List[str]
    output_path: Optional[str] = None

class PdfFlattenInput(BaseModel):
    path: str
    output_path: Optional[str] = None

# 6. Forms
class PdfFillFormInput(BaseModel):
    path: str
    field_data: Dict[str, str]
    output_path: Optional[str] = None

class PdfExtractFormOutput(BaseModel):
    field_data: Dict[str, str]
