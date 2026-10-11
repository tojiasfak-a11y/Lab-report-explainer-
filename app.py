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
DEFAULT = E("இந்த மதிப்பு இயல்பு வரம்புக்கு வெளியே உள்ளது.", "", "", "", "இதுபற்றி மருத்துவரிடம் கேளுங்கள்.")
STATUS_TA = {"LOW": "குறைவு", "HIGH": "அதிகம்", "NORMAL": "இயல்பு"}

ALIASES = [
    ("Hemoglobin", r"h(?:a)?emoglobin|\bhb\b"),
    ("RBC Count", r"\brbc\b|red blood cell|red cell count|erythrocyte"),
    ("Hematocrit (PCV)", r"h(?:a)?ematocrit|\bpcv\b|packed cell"),
    ("MCV", r"\bmcv\b|mean corpuscular volume"),
    ("WBC Count", r"\bwbc\b|white blood cell|total leu[ck]ocyte|\btlc\b"),
    ("Platelet Count", r"platelet|\bplt\b"),
    ("Neutrophils", r"neutrophil|polymorph"),
    ("Lymphocytes", r"lymphocyte"),
    ("Fasting Blood Sugar", r"fasting\s+(?:blood\s+)?(?:sugar|glucose)|\bfbs\b|glucose\W+fasting"),
    ("Total Cholesterol", r"total\s+cholesterol|cholesterol\W+total|^\W*cholesterol\b"),
    ("TSH", r"\btsh\b|thyroid stimulating"),
]
NUM = r"\d+(?:\.\d+)?"
RANGE = re.compile(rf"({NUM})\s*(?:-|–|—|to)\s*({NUM})", re.I)
BELOW = re.compile(rf"(?:below|less than|up to|upto|<)\s*=?\s*({NUM})", re.I)


TYPICAL = {
    "Hemoglobin": ((10, 15), (14, 19)),
    "RBC Count": ((3.5, 4.8), (5, 6.5)),
    "Hematocrit (PCV)": ((33, 42), (43, 55)),
    "MCV": ((75, 85), (95, 105)),
    "WBC Count": ((3000, 5500), (9000, 12500)),
    "Platelet Count": ((100000, 175000), (350000, 500000)),
    "Neutrophils": ((35, 50), (65, 80)),
    "Lymphocytes": ((15, 25), (35, 50)),
    "Fasting Blood Sugar": ((60, 75), (95, 126)),
    "Total Cholesterol": ((0, 0), (170, 250)),
    "TSH": ((0.1, 0.7), (3.5, 6)),
}


LIMITS = {
    "Hemoglobin": (3, 25), "RBC Count": (1, 9), "Hematocrit (PCV)": (10, 70), "MCV": (50, 130),
    "WBC Count": (500, 100000), "Platelet Count": (5000, 1500000), "Neutrophils": (0, 100),
    "Lymphocytes": (0, 100), "Fasting Blood Sugar": (30, 700), "Total Cholesterol": (50, 600),
    "TSH": (0.01, 100),
}


def plausible(key, value, lo, hi):
    if lo >= hi or key not in TYPICAL:
        return False
    (l1, l2), (h1, h2) = TYPICAL[key]
    v1, v2 = LIMITS[key]
    for f in (1, 1000, 100000):
        if l1 <= lo * f <= l2 and h1 <= hi * f <= h2 and v1 <= value * f <= v2:
            return True
    return False


def parse_line(line):
    line = line.replace("|", " ")
    line = re.sub(r"(?<=\d),(?=\d{3})", "", line)
    low = line.lower()
    for key, pat in ALIASES:
        m = re.search(pat, line, re.I)
        if not m:
            continue
        if key == "Total Cholesterol" and re.search(r"hdl|ldl|vldl|ratio", low):
            continue
        if key == "Neutrophils" and "absolute" in low:
            continue
        if key == "Hemoglobin" and "a1c" in low:
            continue
        rest = re.sub(r"^\s*\([^)]*\)", "", line[m.end():])
        vm = re.search(NUM, rest)
        if not vm:
            return None
        value = float(vm.group())
        after = rest[vm.end():]
        rm, bm = RANGE.search(after), BELOW.search(after)
        if rm and (not bm or rm.start() < bm.start()):
            lo, hi = float(rm.group(1)), float(rm.group(2))
        elif bm:
            lo, hi = 0.0, float(bm.group(1))
        else:
            return None
        tokens = after.split()
        unit = tokens[0] if tokens and not re.match(r"^[\d<>.\-–]+$|^(h|l|high|low|below)$", tokens[0], re.I) else ""
        return key, value, unit, lo, hi
    return None


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


def analyze_text(text):
    rows, seen, doubtful = [], set(), []
    for line in text.split("\n"):
        res = parse_line(line)
        if not res or res[0] in seen:
            continue
        if not plausible(res[0], res[1], res[3], res[4]):
            doubtful.append(res[0])
            continue
        seen.add(res[0])
        rows.append(res)
    doubtful = sorted(set(doubtful) - seen)
    df = pd.DataFrame(rows, columns=["Test", "Value", "Unit", "Low", "High"])
    if not df.empty:
        df["Status"] = df.apply(
            lambda r: "LOW" if r.Value < r.Low else ("HIGH" if r.Value > r.High else "NORMAL"), axis=1)
    return df, doubtful


def show(r):
    head = f"**{r.Test}**: {r.Value:g} {r.Unit} (இயல்பு: {r.Low:g} - {r.High:g}) → **{STATUS_TA[r.Status]}**"
    if r.Status == "NORMAL":
        st.success(head)
        return
    st.error(head)
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
    st.divider()


st.title("🩺 ஆய்வக அறிக்கை விளக்கி")
st.write("உங்கள் இரத்தப் பரிசோதனை அறிக்கையின் (PDF அல்லது புகைப்படம்) ஒவ்வொரு மதிப்பும் என்ன அர்த்தம் என்பதை எளிய தமிழில் விளக்குகிறோம்.")
st.warning("இது மருத்துவ ஆலோசனை அல்ல. நோயைக் கண்டறிவதோ சிகிச்சை அளிப்பதோ இந்த செயலியின் வேலை அல்ல. சந்தேகம் இருந்தால் மருத்துவரை அணுகவும். நெஞ்சு வலி, மூச்சுத்திணறல், மயக்கம் போன்ற அவசர நிலையில் உடனே மருத்துவ உதவி பெறவும்.")
st.info("உங்கள் அறிக்கையில் பெயர், தொலைபேசி எண் இருந்தால் அவற்றை நீக்கிவிட்டுப் பதிவேற்றுவது நல்லது. புகைப்படம் எடுத்தால் நல்ல வெளிச்சத்தில், நேராக, தெளிவாக எடுக்கவும்.")

uploaded = st.file_uploader("அறிக்கையைப் பதிவேற்றுங்கள் (PDF அல்லது புகைப்படம்)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded:
    try:
        with st.spinner("அறிக்கையைப் படிக்கிறோம்..."):
            text, source = read_text(uploaded)
            df, doubtful = analyze_text(text)
    except Exception as e:
        st.error("கோப்பைப் படிக்க முடியவில்லை. தெளிவான PDF அல்லது புகைப்படத்தை முயற்சிக்கவும்.")
        st.caption(f"தொழில்நுட்பப் பிழை: {e}")
        st.stop()

    if source == "ocr":
        st.warning("புகைப்படத்திலிருந்து எழுத்துகள் படிக்கப்பட்டுள்ளன, அதனால் சில எண்கள் தவறாக இருக்கலாம். சில பரிசோதனைகள் படிக்கப்படாமலும் போகலாம். கீழே உள்ள மதிப்புகளை உங்கள் அசல் அறிக்கையுடன் சரிபார்க்கவும்.")

    if df.empty:
        st.error("இந்த அறிக்கையில் பரிசோதனை மதிப்புகளைப் படிக்க முடியவில்லை. தெளிவான புகைப்படம் அல்லது டிஜிட்டல் PDF-ஐ முயற்சிக்கவும்.")
    else:
        n = int((df.Status != "NORMAL").sum())
        if source == "ocr":
            st.markdown("**படிக்கப்பட்ட மதிப்புகள் (அசல் அறிக்கையுடன் சரிபார்க்கவும்):**")
            st.dataframe(df[["Test", "Value", "Unit", "Low", "High"]])
        st.subheader(f"சுருக்கம்: {len(df)} மதிப்புகளில் {n} இயல்பாக இல்லை")
        for _, r in df.iterrows():
            show(r)
        if n:
            st.info("பொதுவான குறிப்புகள்: தினமும் 30 நிமிடம் நடைப்பயிற்சி, போதுமான தண்ணீர், 7-8 மணி நேர உறக்கம், சரிவிகித உணவு. இயல்பாக இல்லாத மதிப்புகளுடன் உங்கள் மருத்துவரைச் சந்திக்கவும்.")
        if doubtful:
            st.warning("இந்த மதிப்புகளைச் சரியாகப் படிக்க முடியவில்லை, அதனால் அவற்றை விட்டுவிட்டோம்: " + ", ".join(doubtful) + ". அசல் அறிக்கையைப் பார்க்கவும்.")
        with st.expander("முழு அட்டவணை"):
            st.dataframe(df)
    with st.expander("படிக்கப்பட்ட உரை (சரிபார்க்க)"):
        st.text(text)
    st.caption("உங்கள் அறிக்கை எங்கும் சேமிக்கப்படாது.")
