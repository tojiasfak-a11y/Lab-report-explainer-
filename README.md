# Lab Report Explainer 🩺

A Tamil-first web app that reads a blood test report (digital PDF, scanned PDF or photo), compares every value with the report's own reference range, and explains abnormal results in simple Tamil: what it means, possible reasons, risk factors, diet and lifestyle tips, and when to see a doctor.

## 🔗 Live Demo
[Try the app](https://lab-report-explainer-cgxdtecjiu2jxozgwzhedr.streamlit.app/)

## Features
- Accepts digital PDFs, scanned PDFs, and JPG/PNG photos (OCR with Tesseract)
- Compiled results table: test name (Tamil + English), your value, reference range, and a LOW / HIGH / NORMAL badge
- Visual range bar for each test, showing where your value sits against the normal range
- Summary cards (total, normal, low, high)
- Tamil explanations for abnormal values only, in collapsible sections
- Supports 24 tests: Hemoglobin, RBC, Hematocrit, MCV, MCH, MCHC, WBC, Platelets, Neutrophils, Lymphocytes, Monocytes, Eosinophils, Basophils, Fasting Sugar, HbA1c, Total Cholesterol, Triglycerides, HDL, LDL, Creatinine, Vitamin D, SGPT, SGOT, TSH
- Handles real-world report quirks: age-wise reference ranges (uses the 18+ range), values and ranges printed in different units (thousands / lakhs)

## Safety Design
- Not a diagnosis or treatment tool; no medicine advice
- Shows the extracted values so users can check them against the original report
- Sanity checks on OCR output; values it cannot read reliably are skipped, never guessed
- Warns about tests it does not support or could not read
- Emergency warning and doctor disclaimer on every result
- Reports are processed in memory and not stored

## Tech Stack
Python, Streamlit, pdfplumber, pytesseract (Tesseract OCR), pdf2image, Pillow, Pandas

## Limitations
- OCR can misread numbers in blurry or tilted photos; always verify against the original report
- Only the 24 tests above are explained; other tests are listed as unsupported
- Age-wise ranges: the 18+ range is used, so results for children may differ
- Tamil explanations are general information, not personalised medical advice

## Roadmap
- Age and gender input for exact reference ranges
- More tests (uric acid, urea, electrolytes, urine)
- More Indian languages (Hindi, Telugu, English...)
- Review of the Tamil text by a medical professional

## Disclaimer
For education and awareness only. This is not medical advice. Please consult a doctor.
