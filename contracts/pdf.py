from typing import List, Optional, Union
from pydantic import BaseModel

#
# Ingest
#
class PdfIngestInput(BaseModel):
    path_or_url: str

class PdfIngestResult(BaseModel):
    doc_id: str
    markdown: str
    pages: int

#
# Extract Text
#
class PdfExtractTextInput(BaseModel):
    path: str
    pages: Optional[List[int]] = None  # None means all pages

class PdfExtractTextOutput(BaseModel):
    text: str

#
# Merge
#
class PdfMergeInput(BaseModel):
    input_paths: List[str]
    output_path: Optional[str] = None
    generate_toc: bool = False

class PdfMergeOutput(BaseModel):
    out_path: str

#
# Split
#
class PdfSplitInput(BaseModel):
    path: str
    page_ranges: List[str]  # e.g. ["1-5", "6-10"]
    output_dir: Optional[str] = None

class PdfSplitOutput(BaseModel):
    out_paths: List[str]

#
# Rotate
#
class PdfRotateInput(BaseModel):
    path: str
    angle: int  # e.g., 90, 180, 270
    pages: Optional[List[int]] = None # None means all pages
    output_path: Optional[str] = None

class PdfRotateOutput(BaseModel):
    out_path: str

#
# OCR
#
class PdfOcrInput(BaseModel):
    path: str
    output_path: Optional[str] = None
    languages: Optional[List[str]] = ["eng"]

class PdfOcrResult(BaseModel):
    out_path: str

#
# Redact
#
class RedactionArea(BaseModel):
    page: int
    x0: float
    y0: float
    x1: float
    y1: float

class PdfRedactInput(BaseModel):
    path: str
    areas: Optional[List[RedactionArea]] = None
    patterns: Optional[List[str]] = None
    output_path: Optional[str] = None

class PdfRedactOutput(BaseModel):
    out_path: str
