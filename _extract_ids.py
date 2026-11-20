from pypdf import PdfReader

path = r"c:\Users\hjamil\.cursor\projects\d-hassan-development-ob-project\attachments\012b1b11-6509-4ce0-a450-bc25626f4aaf\OB.pdf"
reader = PdfReader(path)
page = reader.pages[1]
print("--- RAW ---")
print(repr(page.extract_text()))
print("--- CHARS sample ---")
if "/Resources" in page:
    pass

def visitor(text, cm, tm, fontDict, fontSize):
    if text and text.strip():
        x, y = tm[4], tm[5]
        print(f"{y:7.1f} {x:7.1f} {fontSize:5.1f} {text!r}")

page.extract_text(visitor_text=visitor)
