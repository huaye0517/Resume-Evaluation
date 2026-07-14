# -*- coding: utf-8 -*-
"""简历/JD 文本解析模块。

根据文件扩展名，把 PDF、Word(.docx) 或纯文本文件解析为字符串。
解析失败时不抛出异常中断整批，而是返回带提示的结果。
"""

import io
import os
import re


# 支持的文件扩展名
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# OCR 引擎单例（首次使用时才初始化，避免拖慢启动）
_OCR_ENGINE = None


def is_supported(filename):
    """判断文件名是否为支持的格式。"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in SUPPORTED_EXTENSIONS


def _count_cjk(text):
    """统计文本中的中文字符数量。"""
    return len(re.findall(r"[\u4e00-\u9fff]", text or ""))


def _looks_low_quality(text):
    """判断 PDF 直接提取的文本是否为空或乱码（需转 OCR）。

    设计类排版 PDF 常把中文渲染成图片或无 Unicode 映射的字体，
    直接提取会得到空文本、`(cid:xxx)` 或一堆无意义的零散字符。
    """
    if not text or not text.strip():
        return True
    # pdfminer 对无映射字体会输出 (cid:数字)
    if "(cid:" in text:
        return True
    # 中文简历正常应含大量中文；若中文极少，再看是否像正常英文文本
    if _count_cjk(text) < 10:
        # 统计成形的英文单词（长度>=2），数量足够则认为是正常英文简历
        words = re.findall(r"[A-Za-z]{2,}", text)
        if len(words) < 20:
            return True
    return False


def _get_ocr_engine():
    """获取（并缓存）OCR 引擎实例。"""
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        from rapidocr_onnxruntime import RapidOCR

        _OCR_ENGINE = RapidOCR()
    return _OCR_ENGINE


def _ocr_pdf(file_bytes, max_pages=10, zoom=2.0):
    """把 PDF 逐页渲染成图片后做中文 OCR，返回识别出的文字。

    适用于纯图片 / 无文字层的设计类简历 PDF。
    - max_pages：最多识别的页数，防止超长文档耗时过久
    - zoom：渲染倍率，越大越清晰但越慢（2.0 一般足够）
    """
    import fitz  # PyMuPDF
    import numpy as np
    from PIL import Image

    engine = _get_ocr_engine()

    texts = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        page_count = min(len(doc), max_pages)
        for i in range(page_count):
            page = doc[i]
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            arr = np.array(img)

            result, _ = engine(arr)
            if result:
                # result 每项形如 [box, text, score]，按识别顺序拼接
                page_lines = [item[1] for item in result if item and len(item) > 1]
                if page_lines:
                    texts.append("\n".join(page_lines))

    return "\n".join(texts).strip()


def _extract_pdf(file_bytes):
    """从 PDF 字节流中逐页提取文字。"""
    import pdfplumber

    texts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text:
                texts.append(page_text)
    return "\n".join(texts).strip()


def _extract_docx(file_bytes):
    """从 Word(.docx) 字节流中提取段落与表格文字。"""
    from docx import Document

    document = Document(io.BytesIO(file_bytes))

    parts = []
    # 普通段落
    for para in document.paragraphs:
        if para.text and para.text.strip():
            parts.append(para.text.strip())

    # 表格内容（简历常用表格排版，需一并提取）
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text and cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))

    return "\n".join(parts).strip()


def _extract_txt(file_bytes):
    """从纯文本字节流中解码文字，自动尝试常见中文编码。"""
    for encoding in ("utf-8", "gbk", "gb18030", "utf-16"):
        try:
            return file_bytes.decode(encoding).strip()
        except (UnicodeDecodeError, LookupError):
            continue
    # 兜底：忽略无法解码的字节，避免崩溃
    return file_bytes.decode("utf-8", errors="ignore").strip()


def parse_file(filename, file_bytes):
    """解析单个文件，返回 (text, error)。

    成功时 error 为 None；失败或无法提取文字时 text 为空、error 为提示信息。
    """
    ext = os.path.splitext(filename)[1].lower()

    try:
        if ext == ".pdf":
            # 先尝试直接提取文字（速度快、效果好）
            text = _extract_pdf(file_bytes)
            # 若提取为空或乱码（设计类排版/图片型 PDF），自动转 OCR 兜底
            if _looks_low_quality(text):
                try:
                    ocr_text = _ocr_pdf(file_bytes)
                    if ocr_text and _count_cjk(ocr_text) > _count_cjk(text):
                        text = ocr_text
                except Exception as ocr_exc:
                    # OCR 失败不影响其它候选人；若原文本也为空则在下方统一提示
                    if not text:
                        return "", f"PDF 文字提取为空，且 OCR 识别失败：{ocr_exc}"
        elif ext == ".docx":
            text = _extract_docx(file_bytes)
        elif ext == ".txt":
            text = _extract_txt(file_bytes)
        else:
            return "", f"不支持的文件格式：{ext}（仅支持 PDF / Word(.docx) / txt）"
    except Exception as exc:  # 解析异常时单独标注，不影响整批
        return "", f"文件解析失败：{exc}"

    if not text:
        # 常见于扫描件 / 纯图片 PDF
        return "", "无法提取文本（可能是扫描件或纯图片，建议改用可复制文本的简历）"

    return text, None
