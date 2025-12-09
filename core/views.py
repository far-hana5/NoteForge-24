
import os
from django.shortcuts import render
from PIL import Image
import google.generativeai as genai


'''

def extract_text_from_image(image_path):
    """Send image to Gemini 2.5 for handwriting text extraction."""
    model = genai.GenerativeModel("gemini-2.5-flash")
    img = Image.open(image_path)

    # You can adjust the prompt for better accuracy if handwriting is unclear
    prompt = "Extract all handwritten text clearly and accurately from this image."

    try:
        response = model.generate_content([prompt, img])
        return response.text.strip() if response.text else "(No text found)"
    except Exception as e:
        return f"(Error processing image: {str(e)})"

def home(request):
    extracted_results = []

    if request.method == "POST":
        images = request.FILES.getlist("images")
        os.makedirs("media", exist_ok=True)

        for img_file in images:
            save_path = f"media/{img_file.name}"
            with open(save_path, "wb+") as f:
                for chunk in img_file.chunks():
                    f.write(chunk)

            text = extract_text_from_image(save_path)
            extracted_results.append({"name": img_file.name, "text": text})

    return render(request, "course_detail.html", {"results": extracted_results})


from django.shortcuts import render
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch

# Load model & processor once at startup
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

def ocr_view(request):
    text = None
    if request.method == "POST" and request.FILES.get("image"):
        # Read uploaded image
        image_file = request.FILES["image"]
        image = Image.open(image_file).convert("RGB")

        # Preprocess and run model
        pixel_values = processor(images=image, return_tensors="pt").pixel_values
        generated_ids = model.generate(pixel_values)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return render(request, "home.html", {"text": text})

'''
