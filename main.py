

import openai
import json
from openai import OpenAI
import PyPDF2
import pandas as pd
import streamlit as st
from io import BytesIO
import re
import time

client = OpenAI()
path="API_TOKEN.txt"
os.environ["OPENAI_API_KEY"] = "Your api key"
# Function to extract text from a PDF
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# Function to clean extracted text
def clean_extracted_text(text):
    # Remove non-ASCII characters and excessive whitespac
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Function to use OpenAI API for data extraction
def extract_data_using_openai(text, retry_count=3):
    # Construct the prompt for the OpenAI model
    prompt = f"""
    Extract the following details from the invoice text:
    - Invoice Number
    - Invoice Date
    - Due Date
    - Customer Name
    - Place of Supply
    - Item Details (including Item Name, Quantity, Rate, Tax Percentage, Tax Amount, and Total Amount for each item)
    - Total Taxable Amount
    - Total Tax Amount
    - Total Amount
    - Total Discount
    - Payment Details (such as UPI ID, Bank Account, IFSC Code, Bank Name, Branch, etc.)

    Here's the invoice text:
    {text}

    Return the data in strictly valid JSON format, without any additional explanations or comments. Example:
    {{
        "Invoice Number": "INV-001",
        "Invoice Date": "01 Jan 2024",
        "Due Date": "10 Jan 2024",
        "Customer Name": "John Doe",
        "Place of Supply": "California",
        "Item Details": [
            {{
                "Item Name": "Product A",
                "Quantity": 2,
                "Rate": 100,
                "Tax Percentage": 10,
                "Tax Amount": 20,
                "Total Amount": 220
            }}
        ],
        "Total Taxable Amount": 200,
        "Total Tax Amount": 20,
        "Total Amount": 220,
        "Total Discount": 0,
        "Payment Details": {{
            "UPI ID": "john.doe@upi",
            "Bank Account": "1234567890",
            "IFSC Code": "IFSC0001234",
            "Bank": "Bank of America",
            "Branch": "Downtown Branch"
        }}
    }}
    """

    for attempt in range(retry_count):
        try:
            # Using OpenAI API to get completion
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an invoice data extraction assistant."},
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract the content
            response_content = completion.choices[0].message.content
            # Remove any unwanted characters before and after the JSON
            response_content = response_content.strip()

            # Display raw response for debugging
            st.write("### Raw Response Content:")
            st.text(response_content)

            # Attempt to parse JSON
            return json.loads(response_content)
        except json.JSONDecodeError as e:
            st.error(f"Attempt {attempt + 1} failed: JSON decoding failed: {e}. Retrying...")
            time.sleep(2)  # Wait before retrying
    
    # If all retries fail, return None
    return None

# Function to structure extracted data into key-value pairs for a DataFrame
def structure_data_to_dataframe_key_value(extracted_data):
    rows = []
    for invoice in extracted_data:
        if invoice is None:
            continue
        
        invoice_common_details = {
            "Invoice Number": invoice.get("Invoice Number"),
            "Invoice Date": invoice.get("Invoice Date"),
            "Due Date": invoice.get("Due Date"),
            "Customer Name": invoice.get("Customer Name"),
            "Place of Supply": invoice.get("Place of Supply"),
            "Total Taxable Amount": invoice.get("Total Taxable Amount"),
            "Total Tax Amount": invoice.get("Total Tax Amount"),
            "Total Amount": invoice.get("Total Amount"),
            "Total Discount": invoice.get("Total Discount"),
            "UPI ID": invoice.get("Payment Details", {}).get("UPI ID"),
            "Bank Account": invoice.get("Payment Details", {}).get("Bank Account"),
            "IFSC Code": invoice.get("Payment Details", {}).get("IFSC Code"),
            "Bank": invoice.get("Payment Details", {}).get("Bank"),
            "Branch": invoice.get("Payment Details", {}).get("Branch")
        }
        
        # Iterate over item details and create a row for each item
        if isinstance(invoice.get("Item Details"), list):
            for item in invoice.get("Item Details", []):
                if isinstance(item, dict):
                    row = invoice_common_details.copy()
                    row.update({
                        "Item Name": item.get("Item Name"),
                        "Quantity": item.get("Quantity"),
                        "Rate": item.get("Rate"),
                        "Tax Percentage": item.get("Tax Percentage"),
                        "Tax Amount": item.get("Tax Amount"),
                        "Total Amount per Item": item.get("Total Amount")
                    })
                    rows.append(row)
    return pd.DataFrame(rows)

# Streamlit App
def main():
    st.title("Invoice Data Extraction App")
    st.write("Upload multiple invoices in PDF format and extract the data into a CSV file.")

    # File uploader
    uploaded_files = st.file_uploader("Upload PDF Invoices", type=["pdf"], accept_multiple_files=True)

    # Extracted data storage
    extracted_data = []

    # Process each uploaded file
    if uploaded_files:
        for file in uploaded_files:
            with st.spinner(f"Processing {file.name}..."):
                # Extract text from PDF
                text = extract_text_from_pdf(file)
                
                # Clean extracted text
                cleaned_text = clean_extracted_text(text)
                
                # Display cleaned text for debugging
                st.write(f"### Cleaned Text from {file.name}:")
                st.text(cleaned_text)
                
                # Extract data using OpenAI API
                extracted_json = extract_data_using_openai(cleaned_text)
                
                if extracted_json:
                    extracted_data.append(extracted_json)
                    # Display extracted JSON data for user verification
                    st.write(f"### Extracted Data from {file.name}:")
                    st.json(extracted_json)
                else:
                    st.error(f"Failed to extract data from invoice {file.name} after multiple attempts.")

        # Create DataFrame from extracted data
        if extracted_data:
            df = structure_data_to_dataframe_key_value(extracted_data)
            # Display DataFrame
            st.write("### Extracted Invoice Data:")
            st.dataframe(df)

            # Download CSV button
            if not df.empty:
                csv = df.to_csv(index=False)
                b = BytesIO()
                b.write(csv.encode())
                b.seek(0)
                st.download_button(
                    label="Download CSV File",
                    data=b,
                    file_name="extracted_invoice_data.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()

# Note: This script takes the data from all the uploaded PDFs (like the provided sample) and structures them into respective columns using key-value pairs to create a DataFrame. The extracted information is saved in a CSV file with all the relevant details organized accordingly.
