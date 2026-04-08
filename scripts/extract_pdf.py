#!/usr/bin/env python3
"""
extract_pdf.py — Extract text from PDF files page by page.

Usage:
    python extract_pdf.py input.pdf [output.txt]

If output path is not specified, prints to stdout.
"""
import sys
import argparse
import pdfplumber


def extract_pdf_text(pdf_path: str, output_path: str = None) -> str:
    """Extract text from all pages of a PDF file."""
    pdf = pdfplumber.open(pdf_path)
    all_text = []
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            all_text.append(f"=== Page {i+1}/{len(pdf.pages)} ===\n{text}\n")
    pdf.close()

    result = "\n".join(all_text)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✅ Saved: {output_path} ({len(all_text)} pages)")
    else:
        print(result)

    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract text from PDF files')
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('output', nargs='?', default=None, help='Output text file path (optional)')

    args = parser.parse_args()
    extract_pdf_text(args.pdf_path, args.output)
