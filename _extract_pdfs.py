from pypdf import PdfReader

paths = [
    r"c:\Users\hjamil\.cursor\projects\d-hassan-development-ob-project\attachments\012b1b11-6509-4ce0-a450-bc25626f4aaf\Organizational.pdf",
    r"c:\Users\hjamil\.cursor\projects\d-hassan-development-ob-project\attachments\012b1b11-6509-4ce0-a450-bc25626f4aaf\OB.pdf",
]
out = r"d:\hassan development\ob-project\_pdf_extract.txt"
chunks = []
for path in paths:
    reader = PdfReader(path)
    chunks.append(f"===== {path.split(chr(92))[-1]} pages={len(reader.pages)} =====\n")
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        # PDF extracts each word on its own line. Join wrapped lines into paragraphs.
        lines = [ln.strip() for ln in text.splitlines()]
        paragraphs = []
        buf = []
        for ln in lines:
            if not ln:
                if buf:
                    paragraphs.append(" ".join(buf))
                    buf = []
            else:
                buf.append(ln)
        if buf:
            paragraphs.append(" ".join(buf))
        chunks.append(f"\n----- PAGE {i} -----\n")
        chunks.append("\n".join(paragraphs))
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(chunks))
print("ok", len(chunks))
