from pathlib import Path
from PIL import Image,ImageDraw
import pypdfium2 as pdfium
from pypdf import PdfReader
import pdfplumber,json
ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'qa';QA.mkdir(exist_ok=True)
summary=[]
for src in (ROOT/'output/pdf').glob('*.pdf'):
    stem='report' if 'Report' in src.name else 'board'
    doc=pdfium.PdfDocument(src);pages=[]
    with pdfplumber.open(src) as pdf:
        for i,pg in enumerate(pdf.pages):
            chars=pg.chars
            outside=[c for c in chars if c['x0']<25 or c['x1']>pg.width-24 or c['top']<10 or c['bottom']>pg.height-10]
            text=pg.extract_text() or ''
            summary.append({'file':src.name,'page':i+1,'characters':len(text),'outside_page_margin':len(outside),'start':text[:85]})
            im=doc[i].render(scale=1.45).to_pil();im.save(QA/f'{stem}-{i+1:02}.png');pages.append(im)
    for start in range(0,len(pages),4):
        canvas=Image.new('RGB',(1600,2240),'#d8d8d8');draw=ImageDraw.Draw(canvas)
        for k,im in enumerate(pages[start:start+4]):
            im=im.copy();im.thumbnail((780,1080));x=(k%2)*800;y=(k//2)*1120
            canvas.paste(im,(x,y+25));draw.text((x+8,y+5),f'{stem} {start+k+1}',fill='black')
        canvas.save(QA/f'{stem}-contact-{start+1:02}.png')
(QA/'inspection.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({'pages':len(summary),'outside_margin':sum(p['outside_page_margin'] for p in summary),'short_pages':[(p['file'],p['page'],p['characters']) for p in summary if p['characters']<180]},indent=2))
