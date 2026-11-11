"""Build the method PDF and Markdown from the canonical method_content.json.

Python 3.10+; install reportlab and pypdf. Uses the fonts bundled in assets/.
Run from any directory. The source contracts, policy and saved results are not edited.
"""
from argparse import ArgumentParser
from pathlib import Path
from xml.sax.saxutils import escape
import json
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph, Table, TableStyle
from pypdf import PdfReader, PdfWriter

PUBLIC = Path(__file__).resolve().parents[1]
W, H = 612, 792
M, CW = 42, 528
INK, BLUE, MUTED, LINE, SAGE = map(HexColor, ['#172331','#4355db','#5c6878','#e1e5ed','#f1f5f1'])

def register_fonts():
    for name, file in [('Body','Inter-Regular.ttf'),('Semi','Inter-SemiBold.ttf'),('Bold','Inter-Bold.ttf'),('Display','Inter-Medium.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(PUBLIC/'assets'/file)))
    pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')

class MethodPDF:
    def __init__(self, path, data):
        self.path, self.data = path, data
        self.c = canvas.Canvas(str(path), pagesize=(W,H), pageCompression=1, invariant=1, initialFontName='Body')
        self.y, self.page = 0, 0
        self.c.setTitle(data['title']); self.c.setAuthor(data['author'])
        self.c.setSubject(data['subject']); self.c.setCreator(data['author'])
    def paragraph(self, text, size=11, leading=14.7, font='Body', color=INK, width=CW, x=M, gap=10):
        paragraph=Paragraph(text, ParagraphStyle('p',fontName=font,fontSize=size,leading=leading,textColor=color,splitLongWords=False))
        _,height=paragraph.wrap(width,1000)
        if self.y+height>735:
            raise ValueError(f'Page {self.page} overflows; shorten the canonical source or adjust layout.')
        paragraph.drawOn(self.c,x,H-self.y-height);self.y+=height+gap
    def start(self, page):
        self.page+=1;self.y=25
        self.paragraph('Ingrid Kao / AI contract review',8.8,12,'Semi',INK,gap=0)
        self.c.setFillColor(MUTED);self.c.setFont('Body',8)
        self.c.drawRightString(W-M,H-34,self.data['edition'].upper())
        self.c.setStrokeColor(LINE);self.c.line(M,H-49,W-M,H-49)
        self.y=66;self.paragraph(escape(page['kicker']),9,12,'Semi',BLUE,gap=10)
        self.paragraph(escape(page['title']),25.5,29,'Display',gap=11)
        self.paragraph(escape(page['subtitle']),11.5,15.5,color=MUTED,gap=18)
    def table(self, block):
        widths=block['widths'];head=block['headers'];rows=block['rows']
        ps=lambda text,header=False:Paragraph(escape(str(text)),ParagraphStyle('cell',fontName='Semi'if header else'Body',fontSize=10.3,leading=13.8,textColor=BLUE if header else INK,splitLongWords=False))
        table=Table([[ps(x,True)for x in head]]+[[ps(x)for x in row]for row in rows],colWidths=widths)
        table.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Body'),('BACKGROUND',(0,0),(-1,0),HexColor('#eef0ff')),('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#ffffff'),HexColor('#f8f9fb')]),('LINEBELOW',(0,0),(-1,-1),.5,LINE),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
        _,height=table.wrap(CW,1000)
        if self.y+height>735:raise ValueError(f'Table overflows page {self.page}')
        table.drawOn(self.c,M,H-self.y-height);self.y+=height+15
    def block(self, b):
        kind=b['type']
        if kind=='section':
            self.y+=5;self.paragraph(escape(b['text']),12.8,17,'Semi',gap=7)
        elif kind=='table':self.table(b)
        elif kind=='note':self.paragraph(escape(b['text']),9.7,13,color=MUTED,gap=11)
        elif kind=='quote':
            self.c.setStrokeColor(BLUE); self.c.setLineWidth(2)
            self.c.line(M+1,H-self.y-3,M+1,H-self.y-30)
            self.paragraph('&ldquo;'+escape(b['text'])+'&rdquo;',10.9,15,'Body',color=INK,x=M+12,width=CW-24,gap=5)
            self.paragraph(escape(b['label']),9,12,color=BLUE,x=M+12,width=CW-24,gap=13)
        elif kind=='code':self.paragraph(escape(b['text']),10.3,14,'Semi',color=BLUE,gap=10)
        elif kind=='reference':
            self.paragraph(f'[{b["id"]}] <link href="{escape(b["url"])}" color="#4355db">{escape(b["title"])}</link>',10,13.3,'Semi',gap=4)
            self.paragraph(escape(b['text']),9.5,12.6,color=MUTED,gap=10)
        else:self.paragraph(escape(b['text']))
    def end(self):
        self.c.setStrokeColor(LINE);self.c.line(M,38,W-M,38)
        self.c.setFillColor(MUTED);self.c.setFont('Body',8)
        self.c.drawString(M,24,'Ingrid Kao | Method, evidence and decision controls')
        self.c.drawRightString(W-M,24,f'{self.page} / {len(self.data["pages"])}');self.c.showPage()
    def save(self):
        self.c.save();reader=PdfReader(self.path);writer=PdfWriter();writer.clone_document_from_reader(reader);writer.metadata=None
        writer.add_metadata({'/Title':self.data['title'],'/Author':self.data['author'],'/Creator':self.data['author'],'/Subject':self.data['subject']})
        tmp=self.path.with_suffix('.tmp.pdf');writer.write(tmp);tmp.replace(self.path)

def markdown(data):
    text=['# '+data['title'],'',data['author']+' | '+data['edition'],'']
    for page in data['pages']:
        text.extend(['## '+page['title'],'',page['subtitle'],''])
        for b in page['blocks']:
            kind=b['type']
            if kind=='section':text.extend(['### '+b['text'],''])
            elif kind=='table':
                text.extend(['| '+' | '.join(b['headers'])+' |','| '+' | '.join(['---']*len(b['headers']))+' |'])
                text.extend('| '+' | '.join(str(x)for x in row)+' |'for row in b['rows']);text.append('')
            elif kind=='quote':text.extend(['> '+b['text'],'','Source: '+b['label'],''])
            elif kind=='code':text.extend(['```sh',b['text'],'```',''])
            elif kind=='reference':text.extend([f'[{b["id"]}] [{b["title"]}]({b["url"]}) - '+b['text'],''])
            else:text.extend([b['text'],''])
    return '\n'.join(text)

def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=PUBLIC/'01_ai_review/method_content.json')
    parser.add_argument('--output-dir',type=Path,default=PUBLIC/'01_ai_review')
    args=parser.parse_args();data=json.loads(args.source.read_text());args.output_dir.mkdir(parents=True,exist_ok=True)
    register_fonts();pdf=MethodPDF(args.output_dir/'AI_Contract_Review_Method.pdf',data)
    for page in data['pages']:
        pdf.start(page)
        for block in page['blocks']:pdf.block(block)
        pdf.end()
    pdf.save();(args.output_dir/'AI_Contract_Review_Method.md').write_text(markdown(data))
    print(f'Built {len(data["pages"])}-page method and editable Markdown from {args.source.name}.')

if __name__=='__main__':main()
