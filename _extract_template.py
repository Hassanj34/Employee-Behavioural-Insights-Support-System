import zipfile
from xml.etree import ElementTree as ET

path = r"c:\Users\hjamil\Downloads\Employee_Behavioural_Insights_Project_Report_Template.docx"
out = r"d:\hassan development\ob-project\_template_extract.txt"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

with zipfile.ZipFile(path) as z:
    names = z.namelist()
    xml = z.read("word/document.xml")
    styles = z.read("word/styles.xml") if "word/styles.xml" in names else b""
    numbering = z.read("word/numbering.xml") if "word/numbering.xml" in names else b""

root = ET.fromstring(xml)
body = root.find(f"{W}body")
lines = []
lines.append("=== ZIP FILES ===")
for n in names:
    lines.append(n)
lines.append("=== DOCUMENT ===")

def para_text(p):
    parts = []
    for node in p.iter():
        if node.tag == f"{W}t" and node.text:
            parts.append(node.text)
        elif node.tag == f"{W}tab":
            parts.append("\t")
        elif node.tag == f"{W}br":
            parts.append("\n")
    return "".join(parts)

def style_of(p):
    pPr = p.find(f"{W}pPr")
    if pPr is None:
        return ""
    ps = pPr.find(f"{W}pStyle")
    if ps is not None:
        return ps.get(f"{W}val", "")
    return ""

idx = 0
for child in list(body):
    tag = child.tag.replace(W, "")
    if tag == "p":
        text = para_text(child)
        st = style_of(child)
        lines.append(f"[P {idx} style={st}] {text}")
    elif tag == "tbl":
        lines.append(f"[TABLE {idx}]")
        for ri, row in enumerate(child.findall(f"{W}tr")):
            cells = []
            for cell in row.findall(f"{W}tc"):
                cell_paras = []
                for p in cell.findall(f"{W}p"):
                    cell_paras.append(para_text(p))
                cells.append(" / ".join(cell_paras))
            lines.append(f"  R{ri}: " + " || ".join(cells))
        lines.append("[END TABLE]")
    elif tag == "sectPr":
        lines.append("[SECTPR]")
    else:
        lines.append(f"[{tag}]")
    idx += 1

# styles summary
sroot = ET.fromstring(styles) if styles else None
if sroot is not None:
    lines.append("=== STYLES ===")
    for s in sroot.findall(f"{W}style"):
        sid = s.get(f"{W}styleId", "")
        name_el = s.find(f"{W}name")
        name = name_el.get(f"{W}val", "") if name_el is not None else ""
        lines.append(f"{sid} = {name}")

with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", len(lines), "lines")
