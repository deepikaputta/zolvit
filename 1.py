import streamlit as st
from PIL import Image
import pytesseract
from transformers import LayoutLMv3Processor, LayoutLMv3ForQuestionAnswering
import torch
import boto3
import os
import json
import fitz  # PyMuPDF
import csv
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import re

# Set up AWS credentials
AWS_ACCESS_KEY = ""
AWS_SECRET_KEY = ""

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load LayoutLM processor and model
processor = LayoutLMv3Processor.from_pretrained("microsoft/layoutlmv3-base")
model = LayoutLMv3ForQuestionAnswering.from_pretrained("microsoft/layoutlmv3-base")

# Function to extract text from PDF using PyMuPDF
def extract_text_from_pdf(pdf_file):
    try:
        text = ""
        with fitz.open(pdf_file) as pdf:
            for page_number in range(len(pdf)):
                page = pdf.load_page(page_number)
                text += page.get_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return None

# Function to parse invoice data using regular expressions
def parse_invoice_data(text):
    try:
        parsed_data = {
            "Company Name": re.search(r"Company Name:\s*(.*)", text, re.IGNORECASE),
            "GSTIN": re.search(r"GSTIN:\s*(\w+)", text),
            "Customer Phone": re.search(r"Phone:\s*(\+?\d{10,})", text),
            "Customer Email": re.search(r"Email:\s*([\w\.-]+@[\w\.-]+)", text),
            "Invoice Number": re.search(r"Invoice Number:\s*(\w+)", text),
            "Invoice Date": re.search(r"Invoice Date:\s*([\d\-\/]+)", text),
            "Due Date": re.search(r"Due Date:\s*([\d\-\/]+)", text),
            "Total Amount": re.search(r"Total Amount:\s*(\d+\.\d{2})", text),
        }

        # Extract matches and handle None values
        parsed_data = {key: match.group(1) if match else "N/A" for key, match in parsed_data.items()}
        return parsed_data

    except Exception as e:
        logger.error(f"Error parsing invoice data: {e}")
        return {}

# Function to extract data using Hugging Face LayoutLM model
def extract_with_huggingface(pdf_file):
    try:
        with fitz.open(pdf_file) as pdf:
            extracted_text = ""
            for page_number in range(len(pdf)):
                page = pdf.load_page(page_number)
                # Convert the page to an image
                pix = page.get_pixmap(dpi=300)
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Process the image using LayoutLMv3Processor
                encoding = processor(image, return_tensors="pt")
                
                # Generate output using the model
                outputs = model(**encoding)
                
                # Extract and append the text (adapt this part based on the model output)
                extracted_text += f"Extracted text for page {page_number}\n"

        return extracted_text
    except Exception as e:
        logger.error(f"Error extracting data with Hugging Face model: {e}")
        return None

# Function to process each file and extract structured data
def process_file(uploaded_file):
    logger.info(f"Processing PDF file: {uploaded_file.name}...")
    extracted_text = extract_text_from_pdf(uploaded_file)
    parsed_data = parse_invoice_data(extracted_text) if extracted_text else {}
    huggingface_data = extract_with_huggingface(uploaded_file)
    
    if extracted_text:
        parsed_data['Hugging Face Data'] = huggingface_data
        return parsed_data, uploaded_file.name
    else:
        return None, uploaded_file.name

# Function to generate a CSV file with the extracted data
def generate_csv_report(extracted_data_list):
    csv_file_path = f"extracted_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        headers = ["File", "Company Name", "Company Address", "GSTIN", "Customer Phone", "Customer Email", "Invoice Number", "Invoice Date", "Due Date", "Customer Name", "Place of Supply", "Bank Name", "Account Number", "IFSC Code", "Branch", "Item Number", "Item Name", "Item Rate", "Item Quantity", "Item Taxable Value", "Item Tax Amount", "Item Total Amount", "Taxable Amount", "CGST", "SGST", "Total Discount", "Round Off", "Total Amount"]
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            for data in extracted_data_list:
                writer.writerow({
                    "File": data['File'],
                    "Company Name": data.get("Company Name", "N/A"),
                    "Company Address": data.get("Company Address", "N/A"),
                    "GSTIN": data.get("GSTIN", "N/A"),
                    "Customer Phone": data.get("Customer Phone", "N/A"),
                    "Customer Email": data.get("Customer Email", "N/A"),
                    "Invoice Number": data.get("Invoice Number", "N/A"),
                    "Invoice Date": data.get("Invoice Date", "N/A"),
                    "Due Date": data.get("Due Date", "N/A"),
                    "Customer Name": data.get("Customer Name", "N/A"),
                    "Place of Supply": data.get("Place of Supply", "N/A"),
                    "Bank Name": data.get("Bank Name", "N/A"),
                    "Account Number": data.get("Account Number", "N/A"),
                    "IFSC Code": data.get("IFSC Code", "N/A"),
                    "Branch": data.get("Branch", "N/A"),
                    "Item Number": data.get("Item Number", "N/A"),
                    "Item Name": data.get("Item Name", "N/A"),
                    "Item Rate": data.get("Rate", "N/A"),
                    "Item Quantity": data.get("Quantity", "N/A"),
                    "Item Taxable Value": data.get("Taxable Value", "N/A"),
                    "Item Tax Amount": data.get("Tax Amount", "N/A"),
                    "Item Total Amount": data.get("Total Amount", "N/A"),
                    "Taxable Amount": data.get("Taxable Amount", "N/A"),
                    "CGST": data.get("CGST", "N/A"),
                    "SGST": data.get("SGST", "N/A"),
                    "Total Discount": data.get("Total Discount", "N/A"),
                    "Round Off": data.get("Round Off", "N/A"),
                    "Total Amount": data.get("Total Amount", "N/A")
                })
        return csv_file_path
    except Exception as e:
        logger.error(f"Error saving CSV file: {e}")
        return None

# Streamlit app structure
st.title("Invoice Data Extraction and Segregation Bot with Advanced Validation")

# Upload multiple invoices (PDF or image)
uploaded_files = st.file_uploader("Choose invoices (PDF files)", type=['pdf'], accept_multiple_files=True)

all_extracted_data = []

if uploaded_files:
    max_workers = min(4, len(uploaded_files))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_file, uploaded_file) for uploaded_file in uploaded_files]
        for i, future in enumerate(as_completed(futures)):
            parsed_data, filename = future.result()
            if parsed_data:
                extracted_data = {
                    "File": filename,
                    **parsed_data
                }
                all_extracted_data.append(extracted_data)

    # Display extracted data
    for data in all_extracted_data:
        st.subheader(f"Extracted Data for {data['File']}")
        st.write(data)

    # Generate and provide a download link for the CSV report
    csv_path = generate_csv_report(all_extracted_data)
    if csv_path:
        with open(csv_path, "rb") as csv_file:
            st.sidebar.download_button(label="Download Extracted Data as CSV", data=csv_file, file_name=csv_path, mime="text/csv", key="csv_download")

    # Calculate and display accuracy (placeholder logic)
    st.sidebar.write("Average Extraction Accuracy: Placeholder%")

# Instructions for users
st.sidebar.title("Instructions")
st.sidebar.write("""
1. Open your terminal and run `huggingface-cli login` (or `huggingface-cli login --token <your_access_token>` for direct token login) to authenticate with Hugging Face.
2. Upload your invoices (PDF files).
3. Extracted data will be displayed for each file.
4. You can download the extracted data as a CSV file.
""")
