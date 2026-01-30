import os
from bs4 import BeautifulSoup
from htmldocx import HtmlToDocx

def convert_resume():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_dir, "resume_general.html")
    css_path = os.path.join(base_dir, "resume_style.css")
    docx_path = os.path.join(base_dir, "resume_general.docx")

    # Read HTML
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Use simplified CSS to avoid crashes in htmldocx
    simplified_css = """
    body { font-family: sans-serif; }
    h1 { color: #2563eb; font-size: 24pt; font-weight: bold; }
    h2 { color: #1e293b; font-size: 14pt; border-bottom: 1px solid #cccccc; }
    .job-title { font-weight: bold; }
    .job-date { color: #2563eb; }
    """

    soup = BeautifulSoup(html_content, "html.parser")
    
    # Remove existing link to css
    for link in soup.find_all("link", rel="stylesheet"):
        link.decompose()
    
    # Add style tag
    style_tag = soup.new_tag("style")
    style_tag.string = simplified_css
    if soup.head:
        soup.head.append(style_tag)
    else:
        head = soup.new_tag("head")
        head.append(style_tag)
        soup.insert(0, head)

    # Process inline styles: STRIP ALL to be safe
    for tag in soup.find_all(True):
        if tag.has_attr('style'):
            del tag['style']

    # Convert
    parser = HtmlToDocx()
    
    # Let's use robust method:
    import docx
    doc = docx.Document()
    try:
        parser.add_html_to_document(str(soup), doc)
        doc.save(docx_path)
        print(f"Successfully converted {html_path} to {docx_path}")
    except Exception as e:
        print(f"Error during conversion: {e}")
        # Print a snippet of what might be failing if it helps, but usually just printing e is enough for now.
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    convert_resume()
