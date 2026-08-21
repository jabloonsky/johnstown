"""Składa index.html: template.html + books.json -> index.html"""
import json
from pathlib import Path

HERE = Path(__file__).parent
books = json.loads((HERE / "books.json").read_text(encoding="utf-8"))
data = json.dumps(books, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = (HERE / "template.html").read_text(encoding="utf-8").replace("__DATA__", data)
(HERE / "index.html").write_text(html, encoding="utf-8")
print(f"index.html: {len(html)/1024:.0f} KB, {len(books)} pozycji")
