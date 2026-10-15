"""Editable architecture descriptions and readable vector/raster exports."""
from pathlib import Path
import math, json
from reportlab.graphics.shapes import Drawing,Rect,Ellipse,Circle,Line,Polygon,String
from reportlab.graphics import renderSVG,renderPDF
import pypdfium2 as pdfium
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'diagrams';OUT.mkdir(exist_ok=True)
INK='#253947';EDGE='#9aabb4';FILL='#f1f6f4'
from reportlab.lib.colors import HexColor as C

def label(d,x,y,text,size=13,anchor='middle'):
    for i,line in enumerate(text.split('\n')):d.add(String(x,y-i*18,line,fontName='Helvetica',fontSize=size,fillColor=C(INK),textAnchor=anchor))
def box(d,x,y,w,h,title,sub=''):
    d.add(Rect(x,y,w,h,rx=7,strokeColor=C(EDGE),fillColor=C(FILL)))
    label(d,x+w/2,y+h/2+9,title,14)
    if sub:label(d,x+w/2,y+h/2-13,sub,11)
def arrow(d,x1,y1,x2,y2,text='',tx=None,ty=None):
    d.add(Line(x1,y1,x2,y2,strokeColor=C(EDGE),strokeWidth=1.5));a=math.atan2(y2-y1,x2-x1)
    pts=[x2,y2,x2-8*math.cos(a-.45),y2-8*math.sin(a-.45),x2-8*math.cos(a+.45),y2-8*math.sin(a+.45)]
    d.add(Polygon(pts,fillColor=C(EDGE),strokeColor=None))
    if text:label(d,tx if tx is not None else (x1+x2)/2,ty if ty is not None else (y1+y2)/2+12,text,10)
def save(name,d,source):
    renderSVG.drawToFile(d,str(OUT/f'{name}.svg'))
    pdf=renderPDF.drawToString(d);doc=pdfium.PdfDocument(pdf);doc[0].render(scale=2).to_pil().save(OUT/f'{name}.png')
    (OUT/f'{name}.mmd').write_text(source.strip()+'\n',encoding='utf-8')

d=Drawing(700,390)
box(d,15,270,170,75,'Scout or analyst','filters and inspects')
box(d,250,270,220,75,'TransferLens local app','historical decision support')
box(d,525,270,160,75,'Supervisor','reviews evidence')
box(d,15,65,190,85,'Dataset publisher','four retained CSV snapshots')
box(d,250,65,220,85,'Offline RMT pipeline','cohort and model artifacts')
box(d,525,65,160,85,'GitHub and PDFs','code, issues and report')
arrow(d,185,308,250,308,'brief',ty=321);arrow(d,525,308,470,308,'inspect',ty=321)
arrow(d,205,107,250,107,'inputs',ty=120);arrow(d,360,150,360,270,'fixed assets',tx=403,ty=210)
arrow(d,470,107,525,107,'evidence',ty=120)
label(d,350,21,'No live provider call or automatic transfer action during inference',11)
save('context',d,'''flowchart LR
  Analyst[Scout or analyst] -->|Filter and inspect| App[TransferLens local app]
  Supervisor -->|Review| App
  Publisher[Dataset publisher] -->|Retained CSV snapshot| Pipeline[Offline RMT pipeline]
  Pipeline -->|Fixed cohort and model artifacts| App
  Pipeline -->|Research evidence| Repository[GitHub and report PDFs]
''')

d=Drawing(700,410)
box(d,15,285,180,80,'Browser frontend','HTML CSS JavaScript')
box(d,260,285,180,80,'HTTP handler','app/server.py')
box(d,505,285,180,80,'Inference engine','app/core.py')
box(d,15,75,180,90,'Browser localStorage','saved scenario shortlist')
box(d,260,75,180,90,'CSV and JSON','cohort, metrics and tasks')
box(d,505,75,180,90,'Trusted RF pipelines','individual and context')
arrow(d,195,325,260,325,'GET JSON / CSV',ty=343);arrow(d,440,325,505,325,'validated query',ty=343)
arrow(d,105,285,105,165,'save / load',tx=150,ty=225)
arrow(d,595,285,595,165,'predict',tx=625,ty=225)
arrow(d,530,285,410,165,'read inputs',tx=437,ty=224)
label(d,350,25,'Offline build prepares artifacts; request handling never trains a model',11)
save('components',d,'''flowchart LR
  UI[Browser HTML CSS JS] -->|GET JSON and CSV| HTTP[app/server.py]
  HTTP -->|Validated query| Engine[app/core.py]
  Engine -->|Read historical features| Data[CSV cohort and JSON results]
  Engine -->|Predict with feature allowlists| RF[Trusted individual and formation RF pipelines]
  UI -->|Save and load scenarios| Local[Browser localStorage]
  HTTP -->|Read task definitions| Tasks[docs/tasks.json]
''')

d=Drawing(700,530)
d.add(Rect(175,35,360,470,rx=4,strokeColor=C(EDGE),fillColor=None))
label(d,355,480,'TransferLens system',15)
def actor(x,y,title):
    d.add(Circle(x,y+25,10,strokeColor=C(INK),fillColor=None));d.add(Line(x,y+15,x,y-20,strokeColor=C(INK)))
    d.add(Line(x-18,y+3,x+18,y+3,strokeColor=C(INK)))
    d.add(Line(x,y-20,x-17,y-43,strokeColor=C(INK)));d.add(Line(x,y-20,x+17,y-43,strokeColor=C(INK)))
    label(d,x,y-65,title,12)
actor(75,305,'Scout / analyst');actor(625,305,'Reviewer');actor(75,100,'Student')
ucs=[(355,420,'Find and rank candidates'),(355,350,'Inspect player profile'),(355,280,'Compare saved shortlist'),(355,210,'Explore club context'),(355,140,'Export candidate CSV'),(355,70,'Review model evidence')]
for x,y,text in ucs:
    d.add(Ellipse(x,y,148,24,strokeColor=C(EDGE),fillColor=C(FILL)));label(d,x,y-4,text,12)
for idx in range(5):
    x,y,_=ucs[idx];d.add(Line(98,300,207,y,strokeColor=C(EDGE)))
d.add(Line(602,300,503,70,strokeColor=C(EDGE)))
d.add(Line(98,100,207,70,strokeColor=C(EDGE)))
save('use-cases',d,'''flowchart LR
  Scout[Scout or analyst] --- U1([Find and rank candidates])
  Scout --- U2([Inspect player profile])
  Scout --- U3([Compare saved shortlist])
  Scout --- U4([Explore club context])
  Scout --- U5([Export candidate CSV])
  Reviewer --- U6([Review model evidence])
  Student --- U6
  subgraph TransferLens system
    U1
    U2
    U3
    U4
    U5
    U6
  end
''')
(OUT/'use-cases.puml').write_text('''@startuml
left to right direction
actor "Scout or analyst" as Scout
actor Reviewer
actor Student
rectangle "TransferLens" {
  usecase "Find and rank candidates" as U1
  usecase "Inspect player profile" as U2
  usecase "Compare saved shortlist" as U3
  usecase "Explore club context" as U4
  usecase "Export candidate CSV" as U5
  usecase "Review model evidence" as U6
}
Scout -- U1
Scout -- U2
Scout -- U3
Scout -- U4
Scout -- U5
Reviewer -- U6
Student -- U6
@enduml
''',encoding='utf-8')
print('Exported context, use-case and component diagrams as editable sources, SVG and PNG.')
