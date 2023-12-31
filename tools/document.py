import fitz  # PyMuPDF


def convert_pdf_to_markdown(pdf_path):
    # Open the provided PDF file
    document = fitz.open(pdf_path)

    markdown_content = ""

    # Loop through each page in the PDF
    for page_num in range(len(document)):
        # Get the page
        page = document.load_page(page_num)

        # Extract text from the page
        text = page.get_text()

        # Simple formatting: Assuming that larger fonts correspond to headings
        # This part can be enhanced with more sophisticated formatting detection
        if text:  # If there's text on the page, add a markdown heading
            markdown_content += f"## Page {page_num + 1}\n\n"

        # Add the extracted text to the markdown content
        markdown_content += text + "\n\n"

    return markdown_content


# Path to your PDF file
pdf_path = './test/AI in 2024.pdf'

# Convert the PDF to Markdown
markdown_content = convert_pdf_to_markdown(pdf_path)

# Optionally, write the markdown content to a file
with open('output.md', 'w') as md_file:
    md_file.write(markdown_content)

print("Conversion complete. Check the 'output.md' file.")
