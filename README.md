# Lab Report Explainer 🩺

A web app that reads a blood test report (digital PDF, scanned PDF or photo), flags each value as LOW / HIGH / NORMAL, and explains it in simple **Tamil**: what it means, possible reasons, risk factors, diet and lifestyle tips, and when to see a doctor.

## 🔗 Live Demo
[Try the app](https://lab-report-explainer-cgxdtecjiu2jxozgwzhedr.streamlit.app/)

## Features
- Accepts digital PDF, scanned PDF, and JPG/PNG photos (OCR with Tesseract)
- Supports 24 tests: CBC (Hemoglobin, RBC, Hematocrit, MCV, MCH, MCHC, WBC, Platelets, Neutrophils, Lymphocytes, Monocytes, Eosinophils, Basophils), Fasting Sugar, HbA1c, Total Cholesterol, Triglycerides, HDL, LDL, Creatinine, Vitamin D, SGPT, SGOT, TSH
- Compares each value with the reference range printed on the report
- Explanations fully in Tamil script

## Safety Design
- Not a diagnosis or treatment tool; no medicine advice
- Shows the values it extracted so users can verify them against the original report
- Sanity checks on OCR output; values it cannot read reliably are skipped, not guessed
- Warns about tests it does not support
- Emergency warning and doctor disclaimer on every result
- Reports are not stored

## Tech Stack
Python, Streamlit, pdfplumber, pytesseract (Tesseract OCR), pdf2image, Pillow, Pandas

## Limitations
- OCR can misread numbers in blurry or tilted photos; always verify against the original report
- Only the 24 tests above are explained; other tests are listed as unsupported
- Tamil explanations are general information, not personalised medical advice

## Roadmap
- More tests (uric acid, urea, electrolytes, urine)
- More Indian languages (Hindi, Telugu, English...)
- Review of the Tamil text by a medical professional

## Disclaimer
For education and awareness only. This is not medical advice. Please consult a doctor.
