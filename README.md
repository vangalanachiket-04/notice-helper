# Notice Helper

Upload a JPG, PNG or PDF notice and get a summary, important dates, contacts,
requirements, a next-steps checklist, flagged uncertainties, and the extracted text.

## Run
    python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    cp .env.example .env     # then paste your Gemini API key into .env
    streamlit run app.py

## Notes
- Requires internet: files are sent to the Gemini API for analysis.
- Supported: JPG, PNG, PDF up to 10 MB. Not an offline tool and not "all formats".
- Never commit `.env`. Use a sample notice without real personal data for demos.

## Test checklist
1. Clear printed notice  2. Blurry or rotated image  3. Notice with no date
(the app should flag uncertainty, not invent details).
