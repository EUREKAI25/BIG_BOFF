# :file: convert_pdf_to_json.py
# :type: function
# :name: convert_pdf_to_json
# :description: Converts a PDF document into a structured JSON object.
# :inputs: {"pdf_path": "Path to the PDF file"}
# :outputs: {"json_data": "Structured JSON object extracted from the PDF"}
# :category: Operations
# :dependencies: extract_text_from_pdf, Text_to_json

def pdf_to_json(pdf_path):
    """Convert PDF to JSON by extracting text and parsing it into JSON."""
    
    # Step 1: Extract text from PDF
    text = call("extract_text_from_pdf", pdf_path)
    
    # Step 2: Convert extracted text to JSON
    json_data = call("Text_to_json", text)
    
    return json_data
