import html
import io
import re

import pandas as pd
import pdfplumber
import pytesseract
import streamlit as st
from pdf2image import convert_from_bytes
from PIL import Image, ImageOps

st.set_page_config(page_title="ஆய்வக அறிக்கை விளக்கி", page_icon="🩺")


def E(meaning, reasons="", risk="", diet="", doctor=""):
    return {"meaning": meaning, "reasons": reasons, "risk": risk, "diet": diet, "doctor": doctor}


IRON_DIET = "கீரை வகைகள், பீட்ரூட், பேரீச்சம்பழம், கொண்டைக்கடலை, பருப்பு, முட்டை, வெல்லம் சேர்த்துக் கொள்ளலாம். எலுமிச்சை அல்லது நெல்லிக்காய் சேர்த்தால் இரும்புச்சத்து நன்றாக உறிஞ்சப்படும்."
ANEMIA_DOC = "சோர்வு, மூச்சுத்திணறல், தலைசுற்றல் இருந்தால் அல்லது மதிப்பு மிகக் குறைவாக இருந்தால் விரைவில் மருத்துவரை அணுகவும்."
DEHYDRATION = "உடலில் நீர்ச்சத்து குறைவு, புகைப்பழக்கம், உயரமான இடங்களில் வசிப்பது போன்றவை காரணமாக இருக்கலாம்."

INFO = {
    "Hemoglobin": {
        "LOW": E("ஹீமோகுளோபின் அளவு இயல்பை விடக் குறைவாக உள்ளது. இது இரத்தசோகைக்கான (அனீமியா) அறிகுறியாக இருக்கலாம்.",
                 "இரும்புச்சத்து, வைட்டமின் B12 அல்லது ஃபோலேட் குறைபாடு, அதிக மாதவிடாய் இரத்தப்போக்கு போன்றவை பொதுவான காரணங்கள்.",
                 "சரிவிகித உணவு இல்லாமை, அதிக இரத்தப்போக்கு, கர்ப்பம், குடலில் புழுக்கள்.",
                 IRON_DIET, ANEMIA_DOC),
        "HIGH": E("ஹீமோகுளோபின் அளவு இயல்பை விட அதிகமாக உள்ளது.", DEHYDRATION, "", "போதுமான தண்ணீர் குடிக்கவும்.",
                  "காரணத்தை அறிய மருத்துவரிடம் காட்டவும்."),
    },
    "RBC Count": {
        "LOW": E("சிவப்பணுக்களின் எண்ணிக்கை குறைவாக உள்ளது. இது இரத்தசோகையுடன் தொடர்புடையதாக இருக்கலாம்.",
                 "இரும்புச்சத்து, வைட்டமின் B12 குறைபாடு அல்லது இரத்த இழப்பு.", "", IRON_DIET, ANEMIA_DOC),
        "HIGH": E("சிவப்பணுக்களின் எண்ணிக்கை அதிகமாக உள்ளது.", DEHYDRATION, "", "போதுமான தண்ணீர் குடிக்கவும்.",
                  "காரணத்தை அறிய மருத்துவரிடம் காட்டவும்."),
    },
    "Hematocrit (PCV)": {
        "LOW": E("இரத்தத்தில் சிவப்பணுக்களின் விகிதம் குறைவாக உள்ளது. இது பொதுவாக இரத்தசோகையுடன் சேர்ந்து காணப்படும்.",
                 "இரும்புச்சத்து குறைபாடு அல்லது இரத்த இழப்பு.", "", IRON_DIET, ANEMIA_DOC),
        "HIGH": E("இரத்தத்தில் சிவப்பணுக்களின் விகிதம் அதிகமாக உள்ளது. நீர்ச்சத்து குறைவால் இப்படி இருக்கலாம்.",
                  DEHYDRATION, "", "போதுமான தண்ணீர் குடிக்கவும்.", "மதிப்பு தொடர்ந்து அதிகமாக இருந்தால் மருத்துவரை அணுகவும்."),
    },
    "MCV": {
        "LOW": E("சிவப்பணுக்களின் அளவு சிறியதாக உள்ளது.",
                 "இரும்புச்சத்து குறைபாடு அல்லது தலசீமியா போன்ற மரபுக் காரணங்கள்.", "", IRON_DIET,
                 "இரும்புச்சத்து பரிசோதனை (Ferritin) தேவையா என்று மருத்துவரிடம் கேளுங்கள்."),
        "HIGH": E("சிவப்பணுக்களின் அளவு பெரியதாக உள்ளது.",
                  "வைட்டமின் B12 அல்லது ஃபோலேட் குறைபாடு, அதிக மது அருந்துதல், தைராய்டு பிரச்சினை.", "",
                  "முட்டை, பால், தயிர், பருப்பு, கீரை வகைகளைச் சேர்த்துக் கொள்ளலாம்.",
                  "B12 பரிசோதனை தேவையா என்று மருத்துவரிடம் கேளுங்கள்."),
    },
    "WBC Count": {
        "LOW": E("வெள்ளையணுக்கள் குறைவாக உள்ளன. இது நோய் எதிர்ப்பு சக்தி குறைவதைக் காட்டலாம்.",
                 "வைரஸ் தொற்று, சில மருந்துகள், ஊட்டச்சத்து குறைபாடு.", "", "சத்தான சரிவிகித உணவு, போதுமான ஓய்வு.",
                 "அடிக்கடி தொற்று அல்லது காய்ச்சல் வந்தால் மருத்துவரை அணுகவும்."),
        "HIGH": E("வெள்ளையணுக்கள் அதிகமாக உள்ளன. உடலில் தொற்று அல்லது வீக்கம் இருக்கலாம்.",
                  "பாக்டீரியா தொற்று, வீக்கம், மன அழுத்தம், புகைப்பழக்கம்.", "", "",
                  "காய்ச்சல், வலி இருந்தால் மருத்துவரை அணுகவும்."),
    },
    "Platelet Count": {
        "LOW": E("இரத்தத் தட்டணுக்கள் குறைவாக உள்ளன. இது இரத்தம் உறைவதைப் பாதிக்கலாம்.",
                 "டெங்கு போன்ற வைரஸ் காய்ச்சல், சில மருந்துகள், வைட்டமின் குறைபாடு.", "", "நிறைய திரவங்கள் குடிக்கவும்.",
                 "காய்ச்சலுடன் இருந்தால், அல்லது மூக்கு, ஈறுகளில் இரத்தப்போக்கு, உடலில் தடிப்புகள் இருந்தால் உடனே மருத்துவரை அணுகவும்."),
        "HIGH": E("இரத்தத் தட்டணுக்கள் அதிகமாக உள்ளன.",
                  "தொற்று, வீக்கம், இரும்புச்சத்து குறைபாடு.", "", "", "மருத்துவரிடம் காட்டி காரணத்தை அறியவும்."),
    },
    "Neutrophils": {
        "LOW": E("நியூட்ரோஃபில் வெள்ளையணுக்கள் குறைவாக உள்ளன.", "வைரஸ் தொற்று, சில மருந்துகள்.", "", "",
                 "காய்ச்சல் இருந்தால் மருத்துவரை அணுகவும்."),
        "HIGH": E("நியூட்ரோஃபில் வெள்ளையணுக்கள் அதிகமாக உள்ளன. இது பெரும்பாலும் பாக்டீரியா தொற்றைக் குறிக்கும்.",
                  "பாக்டீரியா தொற்று, மன அழுத்தம், புகைப்பழக்கம்.", "", "", "காய்ச்சல், வலி இருந்தால் மருத்துவரை அணுகவும்."),
    },
    "Lymphocytes": {
        "LOW": E("லிம்போசைட் வெள்ளையணுக்கள் குறைவாக உள்ளன.", "தொற்று, மன அழுத்தம், சில மருந்துகள்.", "", "",
                 "மருத்துவரிடம் கேளுங்கள்."),
        "HIGH": E("லிம்போசைட் வெள்ளையணுக்கள் அதிகமாக உள்ளன. இது பெரும்பாலும் வைரஸ் தொற்றைக் குறிக்கும்.",
                  "வைரஸ் தொற்று.", "", "", "அறிகுறிகள் தொடர்ந்தால் மருத்துவரை அணுகவும்."),
    },
    "Fasting Blood Sugar": {
        "LOW": E("இரத்தச் சர்க்கரை அளவு குறைவாக உள்ளது.", "நீண்ட நேரம் சாப்பிடாமல் இருப்பது, சில மருந்துகள்.", "",
                 "வியர்வை, நடுக்கம், தலைசுற்றல் இருந்தால் இனிப்பான ஏதாவது சாப்பிடவும்.",
                 "அடிக்கடி இப்படி இருந்தால் மருத்துவரை அணுகவும்."),
        "HIGH": E("வெறும் வயிற்றில் இரத்தச் சர்க்கரை அளவு அதிகமாக உள்ளது. இது நீரிழிவுக்கு முந்தைய நிலை அல்லது நீரிழிவாக இருக்கலாம். இந்தப் பரிசோதனை வெறும் வயிற்றில் எடுக்கப்பட்டதா என்பதையும் உறுதிசெய்யவும்.",
                  "பரிசோதனைக்கு முன் உணவு உண்டிருத்தல், மன அழுத்தம், சில மருந்துகள்.",
                  "குடும்பத்தில் நீரிழிவு, உடல் பருமன், உடற்பயிற்சி இல்லாமை, அதிக இனிப்பு உணவுகள்.",
                  "இனிப்பு, குளிர்பானங்கள், வெள்ளை அரிசி அளவைக் குறைத்து, காய்கறி, கீரை, கேழ்வரகு, கம்பு போன்ற சிறுதானியங்களைச் சேர்க்கவும். தினமும் 30 நிமிடம் நடைப்பயிற்சி செய்யவும்.",
                  "நீரிழிவை உறுதிசெய்ய HbA1c போன்ற பரிசோதனைகள் தேவைப்படலாம். மருத்துவரை அணுகவும்."),
    },
    "Total Cholesterol": {
        "HIGH": E("மொத்த கொலஸ்ட்ரால் அதிகமாக உள்ளது. இது நீண்ட காலத்தில் இதய நோய் அபாயத்தை அதிகரிக்கலாம்.",
                  "கொழுப்பு அதிகமான உணவு, உடற்பயிற்சி இல்லாமை, மரபு.",
                  "குடும்பத்தில் இதய நோய், உடல் பருமன், புகைப்பழக்கம், நீரிழிவு, உயர் இரத்த அழுத்தம்.",
                  "வறுத்த உணவு, நெய், வனஸ்பதி, இறைச்சிக் கொழுப்பைக் குறைக்கவும். ஓட்ஸ், பழங்கள், காய்கறிகள், கொட்டைகள் சேர்க்கவும். தினமும் நடைப்பயிற்சி செய்யவும்.",
                  "LDL, HDL, ட்ரைகிளிசரைடு பரிசோதனைகள் தேவையா என்று மருத்துவரிடம் கேளுங்கள்."),
    },
    "TSH": {
        "LOW": E("தைராய்டு தூண்டும் ஹார்மோன் (TSH) குறைவாக உள்ளது. தைராய்டு அதிகமாகச் செயல்படுவதை (ஹைப்பர்தைராய்டிசம்) குறிக்கலாம்.",
                 "தைராய்டு சுரப்பி அதிகமாகச் செயல்படுதல், சில மருந்துகள்.", "பெண்கள், குடும்பத்தில் தைராய்டு பிரச்சினை.", "",
                 "T3, T4 பரிசோதனைகள் தேவையா என்று மருத்துவரிடம் கேளுங்கள்."),
        "HIGH": E("TSH அதிகமாக உள்ளது. தைராய்டு குறைவாகச் செயல்படுவதை (ஹைப்போதைராய்டிசம்) குறிக்கலாம்.",
                  "தைராய்டு சுரப்பி குறைவாகச் செயல்படுதல், அயோடின் குறைபாடு.",
                  "பெண்கள், குடும்பத்தில் தைராய்டு பிரச்சினை, 40 வயதுக்கு மேல்.",
                  "அயோடின் உப்பைப் பயன்படுத்தவும். சீரான உணவு, தினசரி உடற்பயிற்சி.",
                  "எடை கூடுதல், சோர்வு, குளிர் தாங்க முடியாமை இருந்தால் மருத்துவரை அணுகவும்."),
    },
}
CHOL_DIET = "வறுத்த உணவு, நெய், வனஸ்பதி, இறைச்சிக் கொழுப்பைக் குறைக்கவும். ஓட்ஸ், பழங்கள், காய்கறிகள், கொட்டைகள் சேர்க்கவும். தினமும் நடைப்பயிற்சி செய்யவும்."
LIPID_RISK = "குடும்பத்தில் இதய நோய், உடல் பருமன், புகைப்பழக்கம், நீரிழிவு, உயர் இரத்த அழுத்தம்."
SUGAR_RISK = "குடும்பத்தில் நீரிழிவு, உடல் பருமன், உடற்பயிற்சி இல்லாமை, அதிக இனிப்பு உணவுகள்."
LIVER_DIET = "மது முழுமையாகத் தவிர்க்கவும். வறுத்த, எண்ணெய் அதிகமான உணவுகளைக் குறைக்கவும். காய்கறி, பழங்கள் சேர்த்து, தினமும் நடைப்பயிற்சி செய்யவும். மருத்துவர் சொல்லாமல் மூலிகை, மாத்திரைகளை எடுக்க வேண்டாம்."
LIVER_DOC = "கண், தோல் மஞ்சளாதல், வயிற்று வலி, தொடர் வாந்தி இருந்தால் உடனே மருத்துவரை அணுகவும். மற்றபடி மருத்துவரிடம் காட்டி மேலும் பரிசோதனைகள் செய்யவும்."
OTHER_BLOOD = "மற்ற இரத்த மதிப்புகளுடன் சேர்த்து மருத்துவர் மதிப்பிடுவார். மருத்துவரிடம் கேளுங்கள்."

INFO.update({
    "MCH": {
        "LOW": E("சிவப்பணு ஒன்றில் உள்ள ஹீமோகுளோபின் அளவு குறைவாக உள்ளது.", "இரும்புச்சத்து குறைபாடு.", "", IRON_DIET,
                 "ஹீமோகுளோபின், MCV மதிப்புகளுடன் சேர்த்து மருத்துவரிடம் கேளுங்கள்."),
        "HIGH": E("சிவப்பணு ஒன்றில் உள்ள ஹீமோகுளோபின் அளவு அதிகமாக உள்ளது.", "வைட்டமின் B12 அல்லது ஃபோலேட் குறைபாடு.", "",
                  "முட்டை, பால், தயிர், பருப்பு, கீரை வகைகளைச் சேர்த்துக் கொள்ளலாம்.", "B12 பரிசோதனை தேவையா என்று மருத்துவரிடம் கேளுங்கள்."),
    },
    "MCHC": {
        "LOW": E("சிவப்பணுக்களில் ஹீமோகுளோபின் செறிவு குறைவாக உள்ளது (நிறம் குறைந்த சிவப்பணுக்கள்).", "இரும்புச்சத்து குறைபாடு.", "", IRON_DIET,
                 "ஹீமோகுளோபின், MCV மதிப்புகளுடன் சேர்த்து மருத்துவரிடம் கேளுங்கள்."),
        "HIGH": E("சிவப்பணுக்களில் ஹீமோகுளோபின் செறிவு சற்று அதிகமாக உள்ளது.",
                  "இரத்த மாதிரியை எடுக்கும் அல்லது பரிசோதிக்கும் முறையில் ஏற்படும் மாறுபாடு, அல்லது அரிதாகச் சில சிவப்பணு நிலைகள்.", "", "",
                  "மற்ற இரத்த மதிப்புகள் இயல்பாக இருந்தால் இது பெரும்பாலும் முக்கியமில்லாத மாறுபாடாக இருக்கலாம். உறுதிசெய்ய மருத்துவரிடம் கேளுங்கள்."),
    },
    "Monocytes": {
        "LOW": E("மோனோசைட் வெள்ளையணுக்கள் குறைவாக உள்ளன.", "சில மருந்துகள், ஸ்டீராய்டு பயன்பாடு, சில சமயம் சாதாரண மாறுபாடு.", "", "", OTHER_BLOOD),
        "HIGH": E("மோனோசைட் வெள்ளையணுக்கள் அதிகமாக உள்ளன.", "நீண்டகாலத் தொற்று, வீக்கம், தொற்றிலிருந்து குணமடையும் காலம்.", "", "",
                  "காய்ச்சல், எடை குறைதல் போன்ற அறிகுறிகள் இருந்தால் மருத்துவரை அணுகவும்."),
    },
    "Eosinophils": {
        "LOW": E("ஈசினோஃபில் வெள்ளையணுக்கள் குறைவாக உள்ளன.", "ஸ்டீராய்டு மருந்துகள், மன அழுத்தம். பெரும்பாலும் முக்கியமில்லாத மாறுபாடு.", "", "", OTHER_BLOOD),
        "HIGH": E("ஈசினோஃபில் வெள்ளையணுக்கள் அதிகமாக உள்ளன.", "ஒவ்வாமை, ஆஸ்துமா, தோல் ஒவ்வாமை, குடல் புழுக்கள்.",
                  "ஒவ்வாமை வரலாறு, தூசி, சில உணவுகள் அல்லது மருந்துகளால் ஒவ்வாமை.", "உங்களுக்கு ஒவ்வாத பொருட்களைத் தவிர்க்கவும்.",
                  "இருமல், மூச்சிரைப்பு, தோல் அரிப்பு இருந்தால் மருத்துவரை அணுகவும்."),
    },
    "Basophils": {
        "LOW": E("பேசோஃபில் வெள்ளையணுக்கள் குறைவாக உள்ளன. இது பொதுவாக முக்கியமில்லாத மாறுபாடு.", "", "", "", OTHER_BLOOD),
        "HIGH": E("பேசோஃபில் வெள்ளையணுக்கள் அதிகமாக உள்ளன.", "ஒவ்வாமை, வீக்கம், அரிதாக இரத்த தொடர்பான நோய்கள்.", "", "",
                  "மருத்துவரிடம் காட்டி காரணத்தை அறியவும்."),
    },
    "HbA1c": {
        "LOW": E("கடந்த 2-3 மாத சராசரி சர்க்கரை அளவு குறைவாகக் காணப்படுகிறது.", "இரத்தசோகை, சமீபத்திய இரத்த இழப்பு இருந்தால் இப்படிக் காட்டலாம்.", "", "",
                 "மருத்துவரிடம் கேளுங்கள்."),
        "HIGH": E("கடந்த 2-3 மாதங்களின் சராசரி இரத்தச் சர்க்கரை அளவு அதிகமாக உள்ளது. இது நீரிழிவுக்கு முந்தைய நிலை அல்லது நீரிழிவாக இருக்கலாம்.",
                  "சர்க்கரை கட்டுப்பாடு சரியில்லாமை, இனிப்பு, மாவுச்சத்து அதிகம்.", SUGAR_RISK,
                  "இனிப்பு, குளிர்பானங்கள், வெள்ளை அரிசி அளவைக் குறைத்து, காய்கறி, கீரை, கேழ்வரகு, கம்பு போன்ற சிறுதானியங்களைச் சேர்க்கவும். தினமும் 30 நிமிடம் நடைப்பயிற்சி செய்யவும்.",
                  "மருத்துவரை அணுகி நீரிழிவு உறுதியா என்றும் சிகிச்சை தேவையா என்றும் கேளுங்கள்."),
    },
    "Triglycerides": {
        "HIGH": E("டிரைகிளிசரைடு (இரத்தக் கொழுப்பு) அதிகமாக உள்ளது. இது இதய நோய் அபாயத்தை அதிகரிக்கலாம்.",
                  "இனிப்பு, மாவுச்சத்து, வறுத்த உணவு அதிகம், மது, உடற்பயிற்சி இல்லாமை, நீரிழிவு.", LIPID_RISK,
                  "இனிப்பு, குளிர்பானங்கள், பேக்கரி உணவுகள், வெள்ளை அரிசி, மது குறைக்கவும். மீன், கொட்டைகள், காய்கறிகள் சேர்த்து தினமும் நடைப்பயிற்சி செய்யவும்.",
                  "மதிப்பு மிக அதிகமாக இருந்தாலோ வயிற்று வலி இருந்தாலோ விரைவில் மருத்துவரை அணுகவும்."),
    },
    "HDL Cholesterol": {
        "LOW": E("HDL ('நல்ல' கொலஸ்ட்ரால்) குறைவாக உள்ளது. இது இதய நோய் அபாயத்தை அதிகரிக்கலாம்.",
                 "உடற்பயிற்சி இல்லாமை, புகைப்பழக்கம், உடல் பருமன், நீரிழிவு.", LIPID_RISK,
                 "தினமும் நடைப்பயிற்சி அல்லது உடற்பயிற்சி செய்யவும், புகைப்பழக்கத்தை நிறுத்தவும். கொட்டைகள், மீன், பழங்கள், காய்கறிகள் சேர்க்கவும்.",
                 "மற்ற கொலஸ்ட்ரால் மதிப்புகளுடன் சேர்த்து மருத்துவரிடம் கேளுங்கள்."),
    },
    "LDL Cholesterol": {
        "HIGH": E("LDL ('கெட்ட' கொலஸ்ட்ரால்) அதிகமாக உள்ளது. இது நீண்ட காலத்தில் இதய நோய் அபாயத்தை அதிகரிக்கலாம்.",
                  "கொழுப்பு அதிகமான உணவு, உடற்பயிற்சி இல்லாமை, மரபு.", LIPID_RISK, CHOL_DIET,
                  "உங்கள் இதய அபாயத்தைப் பொறுத்து சிகிச்சை தேவையா என்று மருத்துவரிடம் கேளுங்கள்."),
    },
    "Creatinine": {
        "LOW": E("கிரியாட்டினின் குறைவாக உள்ளது. இது பெரும்பாலும் தசை குறைவு அல்லது அதிக நீர் குடிப்பதால் இருக்கலாம்.", "குறைந்த தசை, கர்ப்பம்.", "", "",
                 "மருத்துவரிடம் கேளுங்கள்."),
        "HIGH": E("கிரியாட்டினின் அதிகமாக உள்ளது. சிறுநீரகம் இரத்தத்தை முழுமையாக வடிகட்டவில்லை என்பதற்கான அறிகுறியாக இருக்கலாம்.",
                  "நீர்ச்சத்து குறைவு, சிறுநீரக பாதிப்பு, அதிக இறைச்சி உணவு அல்லது கடுமையான உடற்பயிற்சி, சில மருந்துகள்.",
                  "நீரிழிவு, உயர் இரத்த அழுத்தம், குடும்பத்தில் சிறுநீரக நோய், வலி மாத்திரைகளை அடிக்கடி எடுத்தல்.",
                  "போதுமான தண்ணீர் குடிக்கவும். மருத்துவர் சொல்லாமல் வலி மாத்திரைகளை எடுக்க வேண்டாம்.",
                  "விரைவில் மருத்துவரை அணுகவும். கால் வீக்கம், சிறுநீர் குறைவு இருந்தால் உடனே காட்டவும்."),
    },
    "Vitamin D": {
        "LOW": E("வைட்டமின் D குறைவாக உள்ளது. எலும்பு வலி, சோர்வு, தசை வலிக்குக் காரணமாகலாம்.",
                 "சூரிய ஒளி குறைவு, உணவில் குறைவு, வயது, அதிக உடல் எடை.",
                 "வீட்டுக்குள் அதிக நேரம், மூடிய ஆடை, கருமையான தோல், வெயிலில் செல்லாமை.",
                 "காலை அல்லது மாலை இளம் வெயிலில் தினமும் 15-20 நிமிடம் இருக்கலாம். முட்டை மஞ்சள் கரு, மீன், பால், காளான் உதவும். சப்ளிமெண்ட் அளவை மருத்துவர்தான் தீர்மானிக்க வேண்டும்.",
                 "எலும்பு வலி தொடர்ந்தால் மருத்துவரை அணுகி சரியான அளவில் சப்ளிமெண்ட் பெறவும்."),
        "HIGH": E("வைட்டமின் D அதிகமாக உள்ளது. பொதுவாக அதிக சப்ளிமெண்ட் எடுப்பதால் இப்படி வரலாம்.", "அதிக அளவு வைட்டமின் D மாத்திரைகள்.", "", "",
                  "சப்ளிமெண்ட் எடுத்துக்கொண்டிருந்தால் அளவை மருத்துவரிடம் உறுதிசெய்யுங்கள்."),
    },
    "SGPT (ALT)": {
        "HIGH": E("கல்லீரல் நொதி (SGPT/ALT) அதிகமாக உள்ளது. கல்லீரலில் வீக்கம் அல்லது பாதிப்பு இருக்கலாம்.",
                  "கொழுப்பு கல்லீரல், மது, ஹெபடைடிஸ் தொற்று, சில மருந்துகள்.",
                  "உடல் பருமன், நீரிழிவு, அதிக மது, கொழுப்பு அதிகமான உணவு.", LIVER_DIET, LIVER_DOC),
    },
    "SGOT (AST)": {
        "HIGH": E("நொதி (SGOT/AST) அதிகமாக உள்ளது. கல்லீரல் அல்லது தசை பாதிப்பைக் குறிக்கலாம்.",
                  "கொழுப்பு கல்லீரல், மது, ஹெபடைடிஸ் தொற்று, கடுமையான உடற்பயிற்சி, சில மருந்துகள்.",
                  "உடல் பருமன், நீரிழிவு, அதிக மது.", LIVER_DIET, LIVER_DOC),
    },
})
DEFAULT = E("இந்த மதிப்பு இயல்பு வரம்புக்கு வெளியே உள்ளது.", "", "", "", "இதுபற்றி மருத்துவரிடம் கேளுங்கள்.")
STATUS_TA = {"LOW": "குறைவு", "HIGH": "அதிகம்", "NORMAL": "இயல்பு"}

ALIASES = [
    ("Hemoglobin", r"moglobin|\bhb\b"),
    ("RBC Count", r"\brbc\b|red blood cell|red cell count|erythrocyte"),
    ("Hematocrit (PCV)", r"h(?:a)?ematocrit|\bpcv\b|packed cell"),
    ("MCV", r"\bmcv\b|mean corpuscular volume"),
    ("MCH", r"\bmch\b"),
    ("MCHC", r"\bmchc\b"),
    ("WBC Count", r"\bwbc\b|white blood cell|total leu[ck]ocyte|\btlc\b"),
    ("Platelet Count", r"platelet|\bplt\b"),
    ("Neutrophils", r"neutrophil|polymorph"),
    ("Lymphocytes", r"lymphocyte"),
    ("Monocytes", r"monocyte"),
    ("Eosinophils", r"eosinophil"),
    ("Basophils", r"basophil"),
    ("Fasting Blood Sugar", r"fasting\s+(?:blood\s+)?(?:sugar|glucose)|\bfbs\b|glucose\W+fasting"),
    ("HbA1c", r"hba1c|hb\s*a1c|\ba1c\b|glyc\w*ated\s+h(?:a)?emoglobin"),
    ("Total Cholesterol", r"total\s+cholesterol|cholesterol\W+total|^\W*cholesterol\b"),
    ("Triglycerides", r"triglyceride"),
    ("HDL Cholesterol", r"\bhdl\b"),
    ("LDL Cholesterol", r"\bldl\b"),
    ("Creatinine", r"creatinine"),
    ("Vitamin D", r"vitamin\s*d\b|25\W*(?:oh|hydroxy)"),
    ("SGPT (ALT)", r"\bsgpt\b|\balt\b|alanine\s+(?:amino|trans)"),
    ("SGOT (AST)", r"\bsgot\b|\bast\b|aspartate\s+(?:amino|trans)"),
    ("TSH", r"\btsh\b|thyroid stimulating"),
]
NUM = r"\d+(?:\.\d+)?"
RANGE = re.compile(rf"({NUM})\s*(?:-|–|—|to)\s*({NUM})", re.I)
BELOW = re.compile(rf"(?:below|less than|up to|upto|<)\s*=?\s*({NUM})", re.I)
ABOVE = re.compile(rf"(?:above|greater than|more than|>)\s*=?\s*({NUM})", re.I)
DIFF = ("Neutrophils", "Lymphocytes", "Monocytes", "Eosinophils", "Basophils")
LIPID = ("Total Cholesterol", "Triglycerides", "HDL Cholesterol", "LDL Cholesterol")

TYPICAL = {
    "Hemoglobin": ((10, 15), (14, 19)),
    "RBC Count": ((3.5, 4.8), (5, 6.5)),
    "Hematocrit (PCV)": ((33, 42), (43, 55)),
    "MCV": ((75, 85), (95, 105)),
    "MCH": ((24, 28), (30, 35)),
    "MCHC": ((30, 33), (34, 38)),
    "WBC Count": ((3000, 5500), (9000, 12500)),
    "Platelet Count": ((100000, 175000), (350000, 500000)),
    "Neutrophils": ((35, 50), (65, 80)),
    "Lymphocytes": ((15, 25), (35, 50)),
    "Monocytes": ((0, 4), (5, 12)),
    "Eosinophils": ((0, 2), (3, 8)),
    "Basophils": ((0, 1), (1, 3)),
    "Fasting Blood Sugar": ((60, 75), (95, 126)),
    "HbA1c": ((0, 4.6), (5.5, 7)),
    "Total Cholesterol": ((0, 0), (170, 250)),
    "Triglycerides": ((0, 60), (120, 200)),
    "HDL Cholesterol": ((30, 60), (55, 10000000)),
    "LDL Cholesterol": ((0, 0), (70, 160)),
    "Creatinine": ((0.3, 0.9), (1, 1.5)),
    "Vitamin D": ((10, 32), (40, 110)),
    "SGPT (ALT)": ((0, 15), (30, 60)),
    "SGOT (AST)": ((0, 15), (30, 60)),
    "TSH": ((0.1, 0.7), (3.5, 6)),
}

LIMITS = {
    "Hemoglobin": (3, 25), "RBC Count": (1, 9), "Hematocrit (PCV)": (10, 70), "MCV": (50, 130),
    "MCH": (10, 50), "MCHC": (20, 45),
    "WBC Count": (500, 100000), "Platelet Count": (5000, 1500000), "Neutrophils": (0, 100),
    "Lymphocytes": (0, 100), "Monocytes": (0, 50), "Eosinophils": (0, 60), "Basophils": (0, 20),
    "Fasting Blood Sugar": (30, 700), "HbA1c": (3, 20), "Total Cholesterol": (50, 600),
    "Triglycerides": (20, 5000), "HDL Cholesterol": (5, 150), "LDL Cholesterol": (10, 600),
    "Creatinine": (0.1, 25), "Vitamin D": (1, 400), "SGPT (ALT)": (1, 6000), "SGOT (AST)": (1, 6000),
    "TSH": (0.01, 100),
}


SCALE_BOUNDS = {"WBC Count": (1000, 40000), "Platelet Count": (10000, 1000000)}


def fit(key, value, lo, hi):
    """Return the value expressed in the range's own units, or None if anything looks implausible."""
    if lo >= hi or key not in TYPICAL:
        return None
    (l1, l2), (h1, h2) = TYPICAL[key]
    v1, v2 = LIMITS[key]
    for fr in (1, 1000, 100000):
        if not (l1 <= lo * fr <= l2 and h1 <= hi * fr <= h2):
            continue
        for fv in (1, 1000, 100000):
            if fv == 1:
                ok = v1 <= value <= v2
            else:
                b1, b2 = SCALE_BOUNDS.get(key, (None, None))
                ok = b1 is not None and b1 <= value * fv <= b2
            if ok:
                return round(value * fv / fr, 4)
    return None


def clean_line(line):
    line = line.replace("|", " ")
    return re.sub(r"(?<=\d),(?=\d{3})", "", line)


def find_range(after):
    found = []
    m = RANGE.search(after)
    if m:
        found.append((m.start(), float(m.group(1)), float(m.group(2))))
    m = BELOW.search(after)
    if m:
        found.append((m.start(), 0.0, float(m.group(1))))
    m = ABOVE.search(after)
    if m:
        found.append((m.start(), float(m.group(1)), 1000000.0))
    return min(found)[1:] if found else None


AGE = re.compile(r"\d+\s*-\s*\d+\s*(?:yrs?|years?)\b\s*:?|(?:>|above|over)\s*\d+\s*(?:yrs?|years?)\b\s*:?", re.I)
ADULT = re.compile(r"(?:>|above|over)\s*18\s*(?:yrs?|years?)|adults?\b", re.I)
AGE_WORD = re.compile(r"yrs?|vrs|years?", re.I)


def adult_range(line):
    line = clean_line(line)
    m = ADULT.search(line)
    return find_range(line[m.end():]) if m else None


def parse_line(line):
    line = clean_line(line)
    low = line.lower()
    for key, pat in ALIASES:
        m = re.search(pat, line, re.I)
        if not m:
            continue
        if key in LIPID and re.search(r"ratio|\bnon\b|non-|vldl", low):
            continue
        if key == "Total Cholesterol" and re.search(r"hdl|ldl", low):
            continue
        if key in DIFF and "absolute" in low:
            continue
        if key == "Hemoglobin" and re.search(r"a1c|glyc|mean cell|corpuscular|\bmch|methem|carboxy", low):
            continue
        if key == "Creatinine" and re.search(r"clearance|ratio|urine", low):
            continue
        rest = re.sub(r"^\s*\([^)]*\)", "", line[m.end():])
        vm = re.search(NUM, rest)
        if not vm:
            return None
        value = float(vm.group())
        after = rest[vm.end():]
        rng = find_range(AGE.sub(" ", after))
        if not rng:
            return None
        lo, hi = rng
        tokens = after.split()
        unit = tokens[0] if tokens and not re.match(r"^[\d<>.\-–]+$|^(h|l|high|low|below|above)$", tokens[0], re.I) else ""
        if unit.lower().startswith("millio"):
            unit = "million/cumm"
        elif unit.startswith("%"):
            unit = "%"
        return key, value, unit, lo, hi
    return None


def unknown_test_name(line):
    line = clean_line(line)
    m = re.search(r"\d", line)
    if not m or re.search(r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", line) or AGE_WORD.search(line):
        return None
    if any(re.search(pat, line, re.I) for _, pat in ALIASES):
        return None
    after = line[m.start():]
    if not (RANGE.search(after) or BELOW.search(after) or ABOVE.search(after)):
        return None
    name = re.sub(r"[^A-Za-z() ,./\-]", " ", line[:m.start()])
    name = re.sub(r"\s+[HL]\s*$", "", name.strip())
    name = re.sub(r"\s+", " ", name).strip(" ,.:-/")
    if len(re.findall(r"[A-Za-z]", name)) < 4:
        return None
    return name[:40]


def ocr_image(img):
    img = ImageOps.exif_transpose(img).convert("L")
    if img.width < 2400:
        f = 2400 / img.width
        img = img.resize((int(img.width * f), int(img.height * f)), Image.LANCZOS)
    img = ImageOps.autocontrast(img)
    return pytesseract.image_to_string(img, config="--psm 6") + "\n" + pytesseract.image_to_string(img, config="--psm 4")


def read_text(uploaded):
    data = uploaded.getvalue()
    if uploaded.name.lower().endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages)
        if len(text.strip()) >= 30:
            return text, "pdf"
        pages = convert_from_bytes(data, dpi=200, first_page=1, last_page=3)
        return "\n".join(ocr_image(p) for p in pages), "ocr"
    return ocr_image(Image.open(io.BytesIO(data))), "ocr"


def repair(key, value, lo, hi):
    v = fit(key, value, lo, hi)
    if v is not None:
        return v, lo, hi
    for fl, fh in ((0.1, 0.1), (1, 0.1), (0.1, 1)):
        if (fl != 1 and not (lo.is_integer() and lo >= 10)) or (fh != 1 and not (hi.is_integer() and hi >= 10)):
            continue
        for fv in (1, 0.1):
            if fv != 1 and not (value.is_integer() and value >= 10):
                continue
            v = fit(key, value * fv, lo * fl, hi * fh)
            if v is not None:
                return v, round(lo * fl, 2), round(hi * fh, 2)
    return None


def analyze_text(text):
    lines = text.split("\n")
    best, doubtful, unknown = {}, [], []
    for i, line in enumerate(lines):
        res = parse_line(line)
        if not res:
            name = unknown_test_name(line)
            if name and name.lower() not in [u.lower() for u in unknown]:
                unknown.append(name)
            continue
        key, value, unit, lo, hi = res
        adult = False
        if AGE_WORD.search(line):
            for nxt in lines[i + 1:i + 4]:
                if parse_line(nxt):
                    break
                ar = adult_range(nxt)
                if ar:
                    lo, hi = ar
                    adult = True
                    break
        if key in best and (best[key][1] or not adult):
            continue
        fixed = repair(key, value, lo, hi)
        if not fixed:
            doubtful.append(key)
            continue
        best[key] = ((key, fixed[0], unit, fixed[1], fixed[2]), adult)
    doubtful = sorted(set(doubtful) - set(best))
    rows = [v[0] for v in best.values()]
    df = pd.DataFrame(rows, columns=["Test", "Value", "Unit", "Low", "High"])
    if not df.empty:
        df["Status"] = df.apply(
            lambda r: "LOW" if r.Value < r.Low else ("HIGH" if r.Value > r.High else "NORMAL"), axis=1)
    return df, doubtful, unknown[:10]


TA_NAME = {
    "Hemoglobin": "ஹீமோகுளோபின்",
    "RBC Count": "சிவப்பணுக்கள் எண்ணிக்கை",
    "Hematocrit (PCV)": "ஹீமாடோகிரிட் (PCV)",
    "MCV": "MCV (சிவப்பணு அளவு)",
    "MCH": "MCH (சிவப்பணுவில் ஹீமோகுளோபின்)",
    "MCHC": "MCHC (ஹீமோகுளோபின் செறிவு)",
    "WBC Count": "வெள்ளையணுக்கள் எண்ணிக்கை",
    "Platelet Count": "இரத்தத் தட்டணுக்கள்",
    "Neutrophils": "நியூட்ரோஃபில்",
    "Lymphocytes": "லிம்போசைட்",
    "Monocytes": "மோனோசைட்",
    "Eosinophils": "ஈசினோஃபில்",
    "Basophils": "பேசோஃபில்",
    "Fasting Blood Sugar": "வெறும் வயிற்றுச் சர்க்கரை",
    "HbA1c": "HbA1c (3 மாதச் சர்க்கரை)",
    "Total Cholesterol": "மொத்த கொலஸ்ட்ரால்",
    "Triglycerides": "டிரைகிளிசரைடு",
    "HDL Cholesterol": "HDL கொலஸ்ட்ரால்",
    "LDL Cholesterol": "LDL கொலஸ்ட்ரால்",
    "Creatinine": "கிரியாட்டினின்",
    "Vitamin D": "வைட்டமின் D",
    "SGPT (ALT)": "SGPT (ALT) கல்லீரல் நொதி",
    "SGOT (AST)": "SGOT (AST) நொதி",
    "TSH": "தைராய்டு (TSH)",
}
BADGE = {"LOW": ("↓ குறைவு", "low"), "HIGH": ("↑ அதிகம்", "high"), "NORMAL": ("✓ இயல்பு", "ok")}

CSS = """<style>
.lr-hero{background:linear-gradient(135deg,#0f766e,#0e7490 55%,#1d4ed8);color:#fff;border-radius:16px;padding:20px 18px;margin:0 0 14px 0}
.lr-title{font-size:1.55rem;font-weight:800;line-height:1.35;margin:0 0 6px 0}
.lr-sub{font-size:.95rem;opacity:.93;line-height:1.5}
.lr-cards{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px 0}
.lr-card{border-radius:12px;padding:10px 4px;text-align:center;border:1px solid rgba(128,128,128,.28);background:rgba(128,128,128,.07)}
.lr-card b{display:block;font-size:1.6rem;line-height:1.2}
.lr-card span{font-size:.76rem;opacity:.85}
.lr-card.ok b{color:#16a34a}.lr-card.low b{color:#d97706}.lr-card.high b{color:#dc2626}
.lr-wrap{overflow-x:auto;border:1px solid rgba(128,128,128,.28);border-radius:12px;margin:6px 0 10px 0}
table.lr{width:100%;border-collapse:collapse;font-size:.88rem}
table.lr th{background:rgba(128,128,128,.16);text-align:left;padding:8px;font-size:.76rem}
table.lr td{padding:8px;vertical-align:top;border:0}
table.lr tr.main td{padding-bottom:3px}
table.lr tr.barrow td{padding:0 8px 10px 8px}
table.lr tr.low td{background:rgba(245,158,11,.11)}
table.lr tr.high td{background:rgba(239,68,68,.11)}
.en,.un{font-size:.72rem;opacity:.72}
.bd{display:inline-block;padding:2px 8px;border-radius:999px;font-size:.78rem;font-weight:700;white-space:nowrap}
.bd.ok{background:rgba(22,163,74,.16);color:#16a34a}.bd.low{background:rgba(217,119,6,.2);color:#d97706}.bd.high{background:rgba(220,38,38,.16);color:#dc2626}
.bar{position:relative;height:8px;border-radius:99px;background:rgba(128,128,128,.28)}
.zone{position:absolute;top:0;bottom:0;border-radius:99px;background:rgba(22,163,74,.6)}
.mk{position:absolute;top:50%;width:14px;height:14px;margin:-7px 0 0 -7px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 0 1px rgba(0,0,0,.4)}
.mk.ok{background:#16a34a}.mk.low{background:#d97706}.mk.high{background:#dc2626}
.lr-legend{font-size:.76rem;opacity:.75;margin:2px 0 8px 0}
</style>"""

HERO = (
    '<div class="lr-hero"><div class="lr-title">🩺 ஆய்வக அறிக்கை விளக்கி</div>'
    '<div class="lr-sub">உங்கள் இரத்தப் பரிசோதனை அறிக்கையைப் (PDF அல்லது புகைப்படம்) பதிவேற்றுங்கள். '
    'ஒவ்வொரு மதிப்பும் இயல்பு வரம்புடன் ஒப்பிடப்பட்டு, எளிய தமிழில் விளக்கப்படும்.</div></div>'
)


def fmt(x):
    return f"{x:g}"


def bar_html(r, cls):
    lo, hi, v = float(r.Low), float(r.High), float(r.Value)
    if hi >= 1000000:
        mn, mx = lo * 0.6, max(v * 1.15, lo * 1.6)
        end = None
    else:
        span = hi - lo
        mn = 0.0 if lo == 0 else lo - span * 0.5
        mx = hi + span * 0.5
        mn, mx = min(mn, v - span * 0.1), max(mx, v + span * 0.1)
        end = hi
    rng = (mx - mn) or 1.0
    pos = lambda x: max(0.0, min(100.0, (x - mn) / rng * 100))
    left = pos(lo)
    width = (100.0 - left) if end is None else pos(end) - left
    return (f'<div class="bar"><div class="zone" style="left:{left:.1f}%;width:{width:.1f}%"></div>'
            f'<div class="mk {cls}" style="left:{pos(v):.1f}%"></div></div>')


def summary_html(df):
    n = len(df)
    low = int((df.Status == "LOW").sum())
    high = int((df.Status == "HIGH").sum())
    ok = n - low - high
    cards = [("", n, "மொத்தம்"), ("ok", ok, "இயல்பு"), ("low", low, "குறைவு"), ("high", high, "அதிகம்")]
    return '<div class="lr-cards">' + "".join(
        f'<div class="lr-card {c}"><b>{v}</b><span>{t}</span></div>' for c, v, t in cards) + "</div>"


def table_html(df):
    rows = []
    for r in df.itertuples():
        label, cls = BADGE[r.Status]
        ta = html.escape(TA_NAME.get(r.Test, r.Test))
        en = html.escape(r.Test)
        unit = html.escape(str(r.Unit))
        row_cls = "" if cls == "ok" else cls
        if r.High >= 1000000:
            rng = f"≥ {fmt(r.Low)}"
        elif r.Low == 0:
            rng = f"&lt; {fmt(r.High)}"
        else:
            rng = f"{fmt(r.Low)} – {fmt(r.High)}"
        rows.append(
            f'<tr class="main {row_cls}"><td><b>{ta}</b><br><span class="en">{en}</span></td>'
            f'<td><b>{fmt(r.Value)}</b><br><span class="un">{unit}</span></td>'
            f'<td>{rng}</td><td><span class="bd {cls}">{label}</span></td></tr>'
            f'<tr class="barrow {row_cls}"><td colspan="4">{bar_html(r, cls)}</td></tr>')
    head = "<tr><th>பரிசோதனை</th><th>உங்கள் மதிப்பு</th><th>இயல்பு வரம்பு</th><th>நிலை</th></tr>"
    return f'<div class="lr-wrap"><table class="lr"><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>'


def explain_box(r):
    info = INFO.get(r.Test, {}).get(r.Status, DEFAULT)
    st.markdown(f"**பொருள்:** {info['meaning']}")
    if info["reasons"]:
        st.markdown(f"**சாத்தியமான காரணங்கள்:** {info['reasons']}")
    if info["risk"]:
        st.markdown(f"**ஆபத்துக் காரணிகள்:** {info['risk']}")
    if info["diet"]:
        st.markdown(f"**உணவு / வாழ்க்கை முறை:** {info['diet']}")
    if info["doctor"]:
        st.markdown(f"**மருத்துவரை எப்போது அணுகவும்:** {info['doctor']}")


st.markdown(CSS + HERO, unsafe_allow_html=True)
st.warning("இது மருத்துவ ஆலோசனை அல்ல. நோயைக் கண்டறிவதோ சிகிச்சை அளிப்பதோ இந்த செயலியின் வேலை அல்ல. சந்தேகம் இருந்தால் மருத்துவரை அணுகவும். நெஞ்சு வலி, மூச்சுத்திணறல், மயக்கம் போன்ற அவசர நிலையில் உடனே மருத்துவ உதவி பெறவும்.")
st.info("உங்கள் அறிக்கையில் பெயர், தொலைபேசி எண் இருந்தால் அவற்றை நீக்கிவிட்டுப் பதிவேற்றுவது நல்லது. புகைப்படம் எடுத்தால் நல்ல வெளிச்சத்தில், நேராக, தெளிவாக எடுக்கவும்.")

uploaded = st.file_uploader("அறிக்கையைப் பதிவேற்றுங்கள் (PDF அல்லது புகைப்படம்)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded:
    try:
        with st.spinner("அறிக்கையைப் படிக்கிறோம்..."):
            text, source = read_text(uploaded)
            df, doubtful, unknown = analyze_text(text)
    except Exception as e:
        st.error("கோப்பைப் படிக்க முடியவில்லை. தெளிவான PDF அல்லது புகைப்படத்தை முயற்சிக்கவும்.")
        st.caption(f"தொழில்நுட்பப் பிழை: {e}")
        st.stop()

    if source == "ocr":
        st.warning("புகைப்படத்திலிருந்து எழுத்துகள் படிக்கப்பட்டுள்ளன, அதனால் சில எண்கள் தவறாக இருக்கலாம். சில பரிசோதனைகள் படிக்கப்படாமலும் போகலாம். கீழே உள்ள மதிப்புகளை உங்கள் அசல் அறிக்கையுடன் சரிபார்க்கவும்.")

    if df.empty:
        st.error("இந்த அறிக்கையில் பரிசோதனை மதிப்புகளைப் படிக்க முடியவில்லை. தெளிவான புகைப்படம் அல்லது டிஜிட்டல் PDF-ஐ முயற்சிக்கவும்.")
    else:
        if unknown:
            st.warning("இந்த அறிக்கையில் உள்ள இந்தப் பரிசோதனைகளை இந்த செயலியால் விளக்க முடியவில்லை: " + ", ".join(unknown) + ". இவற்றுக்கு அசல் அறிக்கையைப் பார்த்து மருத்துவரிடம் கேளுங்கள்.")
        if doubtful:
            st.warning("இந்த மதிப்புகளைச் சரியாகப் படிக்க முடியவில்லை, அதனால் அவற்றை விட்டுவிட்டோம்: " + ", ".join(doubtful) + ". அசல் அறிக்கையைப் பார்க்கவும்.")

        st.markdown(summary_html(df) + table_html(df), unsafe_allow_html=True)
        st.markdown('<div class="lr-legend">பச்சைப் பகுதி = இயல்பு வரம்பு. புள்ளி = உங்கள் மதிப்பு.</div>', unsafe_allow_html=True)
        st.caption("அறிக்கையில் வயது வாரியான வரம்புகள் இருந்தால் 18 வயதுக்கு மேற்பட்டவர்களுக்கான வரம்பு எடுக்கப்படும். மதிப்பும் வரம்பும் வெவ்வேறு அலகுகளில் (ஆயிரம் / லட்சம்) இருந்தால் ஒரே அலகாக மாற்றிக் காட்டப்படும்.")

        abn = df[df.Status != "NORMAL"]
        if len(abn):
            st.subheader("விளக்கங்கள்")
            st.caption("இயல்பாக இல்லாத மதிப்புகளுக்கு மட்டும். தட்டினால் விரியும்.")
            for r in abn.itertuples():
                arrow = "↓" if r.Status == "LOW" else "↑"
                with st.expander(f"{arrow} {TA_NAME.get(r.Test, r.Test)} · {fmt(r.Value)} {r.Unit}"):
                    explain_box(r)
            st.info("பொதுவான குறிப்புகள்: தினமும் 30 நிமிடம் நடைப்பயிற்சி, போதுமான தண்ணீர், 7-8 மணி நேர உறக்கம், சரிவிகித உணவு. இயல்பாக இல்லாத மதிப்புகளுடன் உங்கள் மருத்துவரைச் சந்திக்கவும்.")
        else:
            st.success("படிக்கப்பட்ட எல்லா மதிப்புகளும் இயல்பு வரம்புக்குள் உள்ளன. இருந்தாலும் அறிகுறிகள் இருந்தால் மருத்துவரைச் சந்திக்கவும்.")

    with st.expander("படிக்கப்பட்ட உரை (சரிபார்க்க)"):
        st.text(text)
    st.caption("உங்கள் அறிக்கை எங்கும் சேமிக்கப்படாது.")
