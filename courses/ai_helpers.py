from django.shortcuts import render, get_object_or_404,redirect
from .models import Course, SectionNote,LectureFinalNote
from category.models import CourseCategory
from PIL import Image
import google.generativeai as genai
import os
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from django.contrib.auth.decorators import login_required

from django.http import FileResponse
from collections import defaultdict

from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))




def extract_text_from_image(image_path):
    ocr_model = genai.GenerativeModel("gemini-2.5-flash")
    img = Image.open(image_path)
    prompt = "Extract handwritten text accurately from this image."

    try:
        response = ocr_model.generate_content([prompt, img])
        return response.text.strip() if response.text else "(No text found)"
    except:
        return "(Error extracting text)"
    

def structure_text_with_gemini(all_text):
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = ( "The following text was extracted using OCR and may contain mistakes, formatting errors, " "and broken structure. Your job is to CLEAN and RECONSTRUCT it, not rewrite it.\n\n" 
    "📌 STRICT RULES:\n"
    "- Convert everything into clean, structured Markdown.\n"
    "- Use # for main headings.\n" 
    "- Use ## for subheadings.\n" 
    "- Use bullet points for lists.\n" 
    "- Use fenced code blocksfor code.\n"
    "- Fix indentation, spacing, and incorrect formatting.\n"
    "- DO NOT summarize information you can explain topic .\n"
    "- Preserve technical meaning.\n"
    "- Do not use * or ** or *** in text \n"
    "- If OCR text is wrong, correct it and explain simply in 1–2 lines.\n"
    "- When you detect a topic change, create a section heading.\n"
    "- Make sure output is clean, readable, and well-structured.\n\n"
    "📌 INPUT OCR TEXT (very messy):\n"
    f"{all_text}\n\n"
    "📌 OUTPUT (clean Markdown only):"
)

    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else all_text
    except:
        return all_text
