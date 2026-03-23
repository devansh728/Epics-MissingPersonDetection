from pypdf import PdfReader

# Read the PDF
reader = PdfReader("index_delayed_ui.pdf")

# Extract text from all pages
full_text = ""
for page_num, page in enumerate(reader.pages, 1):
    text = page.extract_text()
    full_text += f"\n--- Page {page_num} ---\n{text}\n"

# Save to file
with open("pdf_content.txt", "w", encoding="utf-8") as f:
    f.write(full_text)

print(f"Extracted {len(reader.pages)} pages")
print("Content saved to pdf_content.txt")
