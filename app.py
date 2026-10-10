"""Notice Helper: upload a JPG/PNG/PDF notice, get a structured plain-language breakdown."""
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError

load_dotenv()
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # change in .env if needed
MAX_MB = 10
MIME = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "pdf": "application/pdf"}


class DateItem(BaseModel):
    date: str = Field(description="Date as written in the notice")
    what: str = Field(description="What happens or is due on this date")


class Contact(BaseModel):
    name: str = Field(description="Person or office, or 'Not stated'")
    details: str = Field(description="Email, phone, address, or 'Not stated'")


class Notice(BaseModel):
    summary: str
    important_dates: list[DateItem]
    contacts: list[Contact]
    requirements: list[str]
    next_steps: list[str]
    uncertain: list[str] = Field(description="Unclear, unreadable or missing items")
    extracted_text: str = Field(description="Full text as read from the document")


PROMPT = """Analyze this notice for a student.
Return:
- a plain-language summary in 2-3 sentences
- important dates
- contact details
- eligibility or requirements
- a short action checklist
- anything unclear, unreadable or missing
- the full extracted text, so a human can verify your work
Do not invent missing details. If a field is absent or uncertain, say so
(use an empty list, or write 'Not stated')."""


def analyze(data: bytes, mime: str) -> Notice:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to a .env file (see .env.example).")
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model=MODEL,
        contents=[types.Part.from_bytes(data=data, mime_type=mime), PROMPT],
        config=types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=Notice, temperature=0.1
        ),
    )
    return Notice.model_validate_json(resp.text)


st.set_page_config(page_title="Notice Helper", page_icon="📄")
st.title("📄 Notice Helper")
st.caption("Upload a notice (JPG, PNG or PDF) and get a plain-language breakdown.")
st.info(
    "Analysis is sent to an online AI service, so an internet connection is required. "
    "Please don't upload documents with sensitive personal information."
)

up = st.file_uploader("Upload a notice", type=list(MIME))

if up:
    ext = up.name.rsplit(".", 1)[-1].lower()
    if up.size > MAX_MB * 1024 * 1024:
        st.error(f"File is too large. Please keep it under {MAX_MB} MB.")
        up = None
    elif ext != "pdf":
        st.image(up, caption=up.name, use_container_width=True)

if up and st.button("Analyze", type="primary"):
    try:
        with st.spinner("Reading the notice..."):
            st.session_state["result"] = analyze(up.getvalue(), MIME[ext])
    except RuntimeError as e:
        st.error(str(e))
    except ValidationError:
        st.error("The AI returned an unexpected format. Please try again.")
    except Exception:
        st.error("Couldn't analyze this file. Check your internet connection, the API key, "
                 "and that the image is readable, then try again.")

r: Notice | None = st.session_state.get("result")
if r:
    st.subheader("Summary")
    st.write(r.summary)

    st.subheader("Important dates")
    for d in r.important_dates:
        st.markdown(f"- **{d.date}**: {d.what}")
    if not r.important_dates:
        st.write("No dates found.")

    st.subheader("Contacts")
    for c in r.contacts:
        st.markdown(f"- **{c.name}**: {c.details}")
    if not r.contacts:
        st.write("No contact details found.")

    st.subheader("Requirements")
    for x in r.requirements:
        st.markdown(f"- {x}")
    if not r.requirements:
        st.write("None stated.")

    st.subheader("What to do next")
    for x in r.next_steps:
        st.checkbox(x, key=f"step-{x}")

    if r.uncertain:
        st.warning("**Please double-check:**\n\n" + "\n".join(f"- {x}" for x in r.uncertain))

    with st.expander("Extracted text (verify against the original)"):
        st.text(r.extracted_text)

    st.download_button("Save result as JSON", r.model_dump_json(indent=2), "notice_result.json",
                       "application/json")
