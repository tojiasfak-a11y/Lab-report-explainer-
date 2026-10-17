# Lab Report Explainer (Thelivu) 🩺

A Tamil-first web app that reads a blood test report (digital PDF, scanned PDF or photo), compares every value with the report's own reference range, and explains abnormal results in simple Tamil or English: what it means, possible reasons, risk factors, diet and lifestyle tips, and when to see a doctor.

## 🔗 Live app
**[Open Thelivu](https://tojiasfak-a11y.github.io/Lab-report-explainer-/)**: works in any phone browser and can be installed like an app (Chrome menu > Install app).

Older Streamlit version (kept as a backup): [Streamlit app](https://lab-report-explainer-cgxdtecjiu2jxozgwzhedr.streamlit.app/)

## Features
- Reads digital PDFs, scanned PDFs and JPG/PNG photos (OCR in the browser with Tesseract.js, PDF text with pdf.js)
- 26 supported tests: Hemoglobin, RBC, Hematocrit, MCV, MCH, MCHC, WBC, Platelets, Neutrophils, Lymphocytes, Monocytes, Eosinophils, Basophils, Fasting, Random and Post-meal Sugar, HbA1c, Total Cholesterol, Triglycerides, HDL, LDL, Creatinine, Vitamin D, SGPT, SGOT, TSH
- Summary donut chart, a card per test with a range bar and a LOW / HIGH / NORMAL badge, and explanations for abnormal values only
- Tamil and English
- Voice help: reads the results aloud in Tamil or English using the phone's own voices (offers itself when the app is opened, with a stop button and speed control)
- Floating health-icon background, count-up numbers and range-bar animation, with an on/off switch (also respects the phone's reduce-motion setting)
- Installable as an app; the page opens offline after the first visit
- Handles real-world report quirks: age-wise ranges (uses the 18+ range), values and ranges in different units (thousands / lakhs), decimal commas, Indian number format

## Privacy
Everything runs in your browser. Your report is not uploaded or stored. (The reading tools are downloaded from a CDN the first time you scan a photo.)

## Safety design
- Not a diagnosis or treatment tool; no medicine advice
- Shows the extracted values so users can check them against the original report
- Sanity checks on OCR output; values it cannot read reliably are skipped, never guessed
- Warns about tests it does not support or could not read, and detects hospital discharge summaries and prescriptions
- Emergency warning and doctor disclaimer on every result

## Tech stack
HTML, CSS and JavaScript (no framework), pdf.js, Tesseract.js, service worker. The first prototype (Python + Streamlit) is still in `app.py`.

## Limitations
- OCR can misread numbers in blurry or tilted photos; always verify against the original report
- Only the 26 tests above are explained; other tests are listed as unsupported
- If age-wise ranges are printed, the 18+ range is used, so results for children can differ
- The first photo scan downloads about 15 MB and needs internet
- The Tamil explanations have not yet been reviewed by a doctor

## Roadmap
- Doctor review of the Tamil text
- Age and gender input, more tests
- Hindi and other languages with native-speaker review
- Own web address

## Disclaimer
For education and awareness only. This is not medical advice. Please consult a doctor.
