Invoice Data Extraction App - This project is a web application built with Streamlit that allows users to upload multiple PDF invoices and extract structured data into a CSV file. The app uses the OpenAI API to extract relevant information from invoices and presents it in an organized tabular format.


main.py - Main code 
2024-11-02T05-46_export.csv-extracted and segregated csv file
Screenshot 2024-11-02 112328.png - Streamlit app ui

Cost: Approximately $6 to $18 per 100 invoices for OpenAI API, with additional hosting/storage costs.
Accuracy: 85-95% overall, with some fields more prone to errors.


Features
PDF Upload: Supports uploading multiple invoice PDFs.
Text Extraction: Uses PyPDF2 to extract text from the uploaded PDFs.
Text Cleaning: Cleans the extracted text to ensure it's properly formatted for data extraction.
Data Extraction: Utilizes the OpenAI API (GPT-4) to extract key details from invoices, such as:
Invoice Number
Invoice Date
Due Date
Customer Name
Place of Supply
Item Details (Name, Quantity, Rate, Tax Percentage, Tax Amount, Total Amount)
Total Taxable Amount
Total Tax Amount
Total Amount
Total Discount
Payment Details (UPI ID, Bank Account, IFSC Code, Bank Name, Branch)
Retry Logic: Retries API calls in case of JSON decoding errors.
Data Display: Presents extracted data in a DataFrame for easy viewing.
Download CSV: Allows users to download the extracted data in CSV format.
Installation
Clone the Repository
bash
Copy code
git clone https://github.com/your-username/invoice-data-extraction-app.git
Navigate to the Project Directory
bash
Copy code
cd invoice-data-extraction-app
Install Dependencies Make sure you have Python 3.12 installed. Use pip to install the required packages:
bash
Copy code
pip install streamlit PyPDF2 openai
Set Up OpenAI API Key
Save your OpenAI API key in a file named API_TOKEN.txt or set it as an environment variable:
python
Copy code
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"
Usage
Run the Streamlit App
bash
Copy code
streamlit run app.py
Upload PDF Invoices
Click on the "Upload PDF Invoices" button to upload one or more invoice PDF files.
View Extracted Data
The app will extract text from the PDFs, clean it, and use the OpenAI API to extract structured data.
The extracted data will be displayed in a DataFrame.
Download CSV
Click the "Download CSV File" button to download the extracted data as a CSV file.
Code Overview
extract_text_from_pdf(file): Extracts text from a given PDF file using PyPDF2.
clean_extracted_text(text): Cleans the extracted text by removing non-ASCII characters and extra whitespaces.
extract_data_using_openai(text, retry_count=3): Uses the OpenAI API to extract data from the cleaned text, with retry logic for error handling.
structure_data_to_dataframe_key_value(extracted_data): Converts the extracted JSON data into a structured DataFrame for easy viewing and analysis.
main(): The main function that runs the Streamlit app, handles file uploads, data extraction, and CSV download.
Sample Prompt for OpenAI API
The app uses a well-structured prompt to guide the OpenAI model in extracting the necessary invoice details. It ensures that the output is in valid JSON format, making it easier to parse and structure the data.

Future Improvements
Add support for additional file formats (e.g., images using OCR).
Implement user authentication for secure access.
Provide more options for data visualization and analysis.
Enhance error handling and robustness of the application.
Contributing
If you'd like to contribute to this project, please fork the repository and create a pull request with your changes. Feel free to open issues for any feature requests or bug reports.


other approach 
This application uses advanced machine learning techniques to extract and validate information from invoice documents. It combines traditional text extraction with PyMuPDF and Optical Character Recognition (OCR) and leverages Hugging Face’s LayoutLMv3 model for accurate information parsing.

1.py - python file name
remaining 3 files apart from this 2024-11-02T05-46_export.csv

cost analysis:
Amazon Textract: 10,000 pages x $1.50/1,000 pages = $15/month.
Amazon S3 Storage: If each document is 1 MB, total storage is approximately 10 GB. At $0.023 per GB, this equals $0.23/month.
Hugging Face Pro Plan: $9/month for higher API rate limits.
Total estimated monthly cost: $15 (Textract) + $0.23 (S3) + $9 (Hugging Face) = $24.23/month.
Accuracy:
OCR (pytesseract): Provides moderate accuracy for high-quality scans but struggles with poor or complex layouts. Accuracy can range from 70-80% for structured invoices.
Regex Parsing: Effective for well-structured text but less reliable with inconsistent formats. Performance decreases if the invoice layout varies significantly.
LayoutLMv3 Model: High accuracy (85-95%) for extracting structured data from complex documents. Fine-tuning the model can further enhance performance, but it requires training data and resources.

How It Works
Text Extraction: Extracts raw text from PDF files using PyMuPDF.
Data Parsing: Uses regular expressions to extract fields like GSTIN, company name, phone number, email, etc.
LayoutLMv3 Model: Processes images of invoice pages to extract structured information.
Data Validation: Aggregates and validates extracted data before saving it to a CSV file.
Instructions for Users
Log in to Hugging Face: Open your terminal and run:
bash
Copy code
huggingface-cli login
Or for direct login using a token:
bash
Copy code
huggingface-cli login --token <your_access_token>
Uploading Invoices: Use the “Choose invoices” button to upload your PDF files.
Viewing Results: Extracted data will be displayed below the file uploader.
Downloading CSV: Use the “Download Extracted Data as CSV” button in the sidebar to download the results.
