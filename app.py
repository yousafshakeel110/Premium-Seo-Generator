import streamlit as st
import openai
import zipfile
import os
import tempfile
import pandas as pd
from io import BytesIO
from PIL import Image
import base64

st.set_page_config(page_title="Premium AI SEO Page Generator", layout="wide")
st.title("Premium AI SEO Page Generator (Screenshot Based)")

project_name = st.text_input("Project / Website Name")

screenshots = st.file_uploader(
    "Upload Desktop Screenshots (Multiple allowed)",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

keyword_input = st.text_area(
    "Paste Keywords (one per line)",
    height=150
)

keyword_file = st.file_uploader(
    "Or upload keyword CSV (column name: keyword)",
    type=["csv"]
)

language = st.selectbox(
    "Select Language",
    ["English", "Urdu", "Arabic", "Spanish", "Korean", "Filipino"]
)

seo_type = st.selectbox(
    "SEO Type",
    ["Local", "Global", "Hybrid"]
)

country = st.text_input("Country (optional)")
city = st.text_input("City (optional)")

content_length = st.selectbox(
    "Content Length",
    ["800 words", "1200 words", "1800 words"]
)

openai_key = st.text_input(
    "Paste your OpenAI API Key",
    type="password"
)

generate = st.button("Generate Premium SEO Pages")

def get_keywords():
    if keyword_file:
        df = pd.read_csv(keyword_file)
        return df["keyword"].dropna().tolist()
    return [k.strip() for k in keyword_input.split("\n") if k.strip()]

def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def build_layout_prompt():
    return f"""
Analyze the uploaded website screenshots (desktop view).

TASK:
- Understand the page layout and sections
- Create a clean, semantic HTML5 structure
- Use proper tags: header, section, article, footer
- Add placeholder text where content belongs
- Make SEO-friendly structure
- Do NOT include CSS or JS
- This will be a reusable base template

OUTPUT:
Return only valid HTML.
"""

def build_page_prompt(keyword):
    return f"""
You are an expert SEO content writer.

BASE RULES:
- Use the provided HTML structure exactly
- Replace placeholder text only
- Keep layout unchanged

SEO DETAILS:
Language: {language}
SEO Type: {seo_type}
Primary Keyword: {keyword}
Country: {country}
City: {city}
Content Length: {content_length}

CONTENT RULES:
- NLP and semantic optimization
- Include related entities
- Natural language (no stuffing)
- Unique angle for this keyword
- Add:
  - Meta title
  - Meta description
  - H1, H2, H3
  - FAQ section
  - JSON-LD FAQ schema

OUTPUT:
Return full optimized HTML page only.
"""

if generate:
    if not openai_key or not screenshots:
        st.error("Screenshots and OpenAI key are required.")
    else:
        openai.api_key = openai_key
        keywords = get_keywords()

        images_payload = []
        for img_file in screenshots:
            img = Image.open(img_file)
            images_payload.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_to_base64(img)}"
                }
            })

        layout_response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": build_layout_prompt()},
                        *images_payload
                    ]
                }
            ],
            temperature=0.3
        )

        base_html = layout_response.choices[0].message.content

        with tempfile.TemporaryDirectory() as tmpdir:
            for kw in keywords:
                page_prompt = build_page_prompt(kw)

                page_response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Generate SEO optimized HTML pages."},
                        {"role": "user", "content": base_html + "\n\n" + page_prompt}
                    ],
                    temperature=0.7
                )

                content = page_response.choices[0].message.content
                filename = kw.lower().replace(" ", "-") + ".html"

                with open(os.path.join(tmpdir, filename), "w", encoding="utf-8") as f:
                    f.write(content)

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for file in os.listdir(tmpdir):
                    zipf.write(os.path.join(tmpdir, file), arcname=file)

            st.success("Premium SEO pages generated successfully.")
            st.download_button(
                "Download HTML ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"{project_name}_seo_pages.zip",
                mime="application/zip"
            )
