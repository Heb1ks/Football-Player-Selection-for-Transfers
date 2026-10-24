"""Build the unified report and actual screenshot evidence PDFs."""
from pathlib import Path
import re, json
from xml.sax.saxutils import escape, quoteattr
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
from io import BytesIO
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
fontdir=Path('C:/Windows/Fonts')
if fontdir.exists():
    pdfmetrics.registerFont(TTFont('Body',str(fontdir/'times.ttf')));pdfmetrics.registerFont(TTFont('Body-Bold',str(fontdir/'timesbd.ttf')))
else:
    fontdir=Path('/usr/share/fonts/truetype/dejavu')
    pdfmetrics.registerFont(TTFont('Body',str(fontdir/'DejaVuSerif.ttf')));pdfmetrics.registerFont(TTFont('Body-Bold',str(fontdir/'DejaVuSerif-Bold.ttf')))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Body-Bold',italic='Body',boldItalic='Body-Bold')
styles={
    'body':ParagraphStyle('body',fontName='Body',fontSize=12,leading=13.8,spaceAfter=5,textColor=colors.black,splitLongWords=True),
    'h1':ParagraphStyle('h1',fontName='Body-Bold',fontSize=18,leading=22,spaceAfter=18,textColor=colors.black),
    'h2':ParagraphStyle('h2',fontName='Body-Bold',fontSize=14,leading=18,spaceBefore=4,spaceAfter=10,keepWithNext=True,textColor=colors.black),
    'h3':ParagraphStyle('h3',fontName='Body-Bold',fontSize=12,leading=15,spaceBefore=8,spaceAfter=5,keepWithNext=True,textColor=colors.black),
    'cell':ParagraphStyle('cell',fontName='Body',fontSize=10,leading=12.5,spaceAfter=0,textColor=colors.black),
    'head':ParagraphStyle('head',fontName='Body-Bold',fontSize=10,leading=12.5,textColor=colors.black,spaceAfter=0),
    'caption':ParagraphStyle('caption',fontName='Body',fontSize=10,leading=12.5,spaceBefore=5,spaceAfter=12,textColor=colors.black),
}
def inline(text):
    text=text.replace('–','-').replace('—','-').replace('\u2011','-')
    text=escape(text)
    text=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
    text=re.sub(r'`([^`]+)`',r'\1',text)
    text=re.sub(r'https?://[^\s<>]+',lambda m:'<link href='+quoteattr(m.group().rstrip('.'))+' color="black">'+m.group().rstrip('.')+'</link>'+('.' if m.group().endswith('.') else ''),text)
    return text
def p(text,style='body'):return Paragraph(inline(text),styles[style])
def image(path,maxwidth,maxheight):
    with PILImage.open(path) as im:w,h=im.size
    scale=min(maxwidth/w,maxheight/h)
    return Image(str(path),width=w*scale,height=h*scale,hAlign='CENTER')
def detail_image(path,maxwidth,maxheight):
    # Crop the visible modal for legibility, retaining the original full screenshot.
    im=PILImage.open(path).convert('RGB');w,h=im.size
    x=min(w-1,int(w/2+300));runs=[];start=None
    for y in range(h):
        bright=min(im.getpixel((x,y)))>=250
        if bright and start is None:start=y
        if not bright and start is not None:runs.append((start,y));start=None
    if start is not None:runs.append((start,h))
    top,bottom=max(runs,key=lambda t:t[1]-t[0])
    if bottom-top<200:raise ValueError('Could not identify visible detail modal: '+str(path))
    extra=105 if path.name=='profile.jpg' else 20
    im=im.crop((max(0,int(w/2-345)),max(0,top-20),min(w,int(w/2+345)),min(h,bottom+extra)))
    stream=BytesIO();im.save(stream,format='PNG');stream.seek(0)
    scale=min(maxwidth/im.width,maxheight/im.height)
    return Image(stream,width=im.width*scale,height=im.height*scale,hAlign='CENTER')
def table(lines,width):
    values=[[x.strip() for x in line.strip().strip('|').split('|')] for line in lines]
    values=[row for row in values if not all(re.fullmatch(r'[: -]+',x) for x in row)]
    n=len(values[0]);weights={2:[1.25,3.7],3:[1.35,2.45,2.45],4:[1.15,2.05,2.05,2.05],5:[1.6,1,1,1,1]}.get(n,[1]*n)
    if values[0][0]=='ID':weights=[.65,1.7,2.2,1.1]
    if values[0][0]=='Audit step':weights=[2.0,.9,3.1]
    data=[[p(x,'head' if i==0 else 'cell') for x in row] for i,row in enumerate(values)]
    t=Table(data,colWidths=[width*x/sum(weights) for x in weights],repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.5,colors.black),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    return t
class ReportDocument(SimpleDocTemplate):
    def afterFlowable(self,flowable):
        if not isinstance(flowable,Paragraph) or flowable.style.name!='h2':return
        text=flowable.getPlainText()
        if not re.match(r'^(?:\d+ |References$|Appendix )',text):return
        key='section-'+re.sub(r'[^a-z0-9]+','-',text.lower()).strip('-')
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text,key,level=0)
        self.notify('TOCEntry',(0,text,self.page,key))

def report():
    doc=ReportDocument(str(OUT/'TransferLens_PreDefense_Report.pdf'),pagesize=A4,leftMargin=56.7,rightMargin=56.7,topMargin=56.7,bottomMargin=56.7,title='TransferLens Probationary Period 1 Report',author='Rymbaev Eskender and Diar Gizatov')
    lines=(ROOT/'docs/report.md').read_text(encoding='utf-8').splitlines();story=[];i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line=='<!-- pagebreak -->':story.append(PageBreak());i+=1;continue
        if line=='<!-- toc -->':
            toc=TableOfContents()
            toc.levelStyles=[ParagraphStyle('toc-entry',fontName='Body',fontSize=12,leading=17,spaceBefore=5,leftIndent=0,rightIndent=22,textColor=colors.black)]
            story.extend([p('Table of contents','h2'),toc]);i+=1;continue
        if line.startswith('|'):
            chunk=[]
            while i<len(lines) and lines[i].strip().startswith('|'):chunk.append(lines[i]);i+=1
            story.extend([table(chunk,doc.width),Spacer(1,12)]);continue
        match=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',line)
        if match:
            path=(ROOT/'docs'/match[2]).resolve()
            maxheight=330 if 'diagrams' in str(path) else (485 if path.name=='profile.jpg' else 355 if path.name=='shortlist.jpg' else 390)
            picture=detail_image(path,doc.width,maxheight) if path.name=='profile.jpg' else image(path,doc.width,maxheight)
            caption=match[1]+(' - detail crop; full original screenshot retained' if path.name=='profile.jpg' else '')
            story.append(KeepTogether([picture,p(caption,'caption')]))
            i+=1;continue
        if line.startswith('#'):
            level=len(line)-len(line.lstrip('#'));story.append(p(line.lstrip('# '),'h1' if level==1 else 'h2' if level==2 else 'h3'));i+=1;continue
        if re.match(r'^\d+\. ',line):
            story.append(p(line));i+=1;continue
        chunk=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(('#','|','![','<!--')) and not re.match(r'^\d+\. ',lines[i].strip()):
            chunk.append(lines[i].strip());i+=1
        story.append(p(' '.join(chunk)))
    doc.multiBuild(story)
    import shutil
    team=json.loads((ROOT/'docs/team.json').read_text(encoding='utf-8'))
    group=team.get('group')
    if group:shutil.copyfile(OUT/'TransferLens_PreDefense_Report.pdf',OUT/f'{group}_Rymbaev_ProbPeriod1.pdf')

def board():
    doc=SimpleDocTemplate(str(OUT/'TransferLens_Task_Board_Evidence.pdf'),pagesize=A4,leftMargin=30,rightMargin=30,topMargin=48,bottomMargin=40,title='TransferLens Task Board Evidence',author='Rymbaev Eskender and Diar Gizatov')
    story=[p('Project board and task evidence','h2'),p('Actual screenshots captured on 15 October 2026. The shared tracker is GitHub Issues; the local board presents versioned task definitions and artifact status. Personal owners and review still need confirmation. Open issues are not misrepresented as completed personal contributions.'),p('Shared tracker: https://github.com/Heb1ks/Football-Player-Selection-for-Transfers/issues')]
    shots=ROOT/'docs/screenshots'
    paths=[shots/'github-issues.jpg',shots/'board.jpg',*sorted(shots.glob('task-DIP-*.jpg'))]
    for path in paths:
        if not path.exists():continue
        story.append(PageBreak());story.append(p({'github-issues.jpg':'Shared GitHub issue tracker','board.jpg':'Local board with linked GitHub issues'}.get(path.name,path.stem.replace('task-','')),'h2'))
        story.append(detail_image(path,doc.width,doc.height-115) if path.name.startswith('task-') else image(path,doc.width,doc.height-115))
        story.append(p('Screenshot source: '+('github.com/Heb1ks/Football-Player-Selection-for-Transfers/issues' if path.name=='github-issues.jpg' else 'http://127.0.0.1:8765/board')+' | Actual state on 15 October 2026','caption'))
        if path.name.startswith('task-'):story.append(p('Detail crop for readability. The original full screenshot is retained in docs/screenshots.','caption'))
    story.append(PageBreak());story.append(p('Task index and links','h2'))
    tasks=json.loads((ROOT/'docs/tasks.json').read_text(encoding='utf-8'))['tasks']
    for t in tasks:story.append(p(t['id']+' '+t['title']+' | '+t['status']+' | '+t.get('issue_url','Link pending')))
    doc.build(story)

if __name__=='__main__':
    report();board();print('Built unified report and screenshot evidence PDFs.')
