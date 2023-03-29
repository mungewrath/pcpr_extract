from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import  getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.units import mm, inch
from uuid import uuid4
from io import BytesIO

TEMPLATE_PATH = "src/template.txt"
GLEASON, RISK, CORES, CANCER_DX = None, None, None, None
subs = {}
HEADER = "Patient summary of results - Prostate Needle Core Biopsy"
INCH = 72.0
X_START, X_END = 0.0, 8.5
Y_START, Y_END = 0.0, 11.0
TIMES = "Times-Roman"
BOLD = "Times-Bold"
stylesheet = getSampleStyleSheet()
normalStyle = stylesheet['Normal']
bodyStyle = stylesheet['BodyText']
headStyle = stylesheet['Heading1']
headStyle.fontSize = 14

num2risk = {0:'None', 1:'low', 2: 'medium', 3: 'high'}
def get_info(info):
    #info = sys.stdin.read().strip().split('|||')
    print(info)
    GLEASON = (info['primary'],info['secondary'], info['total'])
    RISK = num2risk[int(info['risk'])]
    CORES = str(int(round(float(info['positive_cores']) / float(info['total_cores']) * 100, 0)))
    # CANCER_DX = "prostate cancer" if int(GLEASON[2]) > 0 else "None"
    CANCER_DX = info['cancer_dx']
    subs['|||gleason_score|||'] = f"{GLEASON[0]} + {GLEASON[1]} = {GLEASON[2]}"
    subs['|||cores|||'] = CORES
    subs['|||grade|||'] = RISK
    subs['|||risk|||'] = RISK
    subs['|||cancer_dx|||'] = CANCER_DX
    return None


def add_predictions(text):
    print(subs)
    for pattern in subs:
        text = text.replace(pattern, subs[pattern])
    return text

def read_template():
    sections = {}
    header = None
    with open(TEMPLATE_PATH, 'r') as f:
        section_id = 0
        raw_template = f.read()
        updated = add_predictions(raw_template)

        for line in updated.split('\n'):
            if line != '\n' and line:
                tokens = line.split('-')
                if tokens[0].strip() == 'HEADER':
                    header = tokens[1].strip()
                elif tokens[0].strip() == 'SECTION':
                    section_id += 1
                    sections[section_id] = {'title': tokens[1].strip()}
                else:
                    sections[section_id]['text'] = line.strip()

    return header, sections

def draw_header(canvas, header, x_offset):

    canvas.setFont(TIMES, 14)
    canvas.drawString(INCH * 0.3, 10.5 * INCH, header)
    canvas.line((X_START+x_offset)*INCH,
                10.4 * INCH,
                (X_END - x_offset)*INCH,
                10.4 * INCH)
    return canvas

def to_bold(text):
    return '<b>' + text + '<\b>'

def draw_box(canvas,x_offset, y_offset, x1=X_START, x2=X_END,y1=Y_START, y2=Y_END):
    left_x = (x1 + x_offset)*INCH
    right_x = (x2 - x_offset)*INCH

    bottom_y = (y1 + y_offset) * INCH
    top_y = (y2 - y_offset) * INCH

    canvas.line(left_x, bottom_y, right_x, bottom_y)  # bottom of box
    canvas.line(left_x, top_y, right_x, top_y)        # top of box
    canvas.line(left_x, bottom_y, left_x, top_y)      # left side of box
    canvas.line(right_x, bottom_y, right_x, top_y)    # right side of box
    return canvas


def _flowable_section(section_info):
    title, text = section_info['title'], section_info.get('text', None)
    p1 = Paragraph(title, stylesheet['Heading1'])
    if text:
        p2 = Paragraph(text + "<br /><br />", bodyStyle)
        p2.getSpaceAfter()
        return [p1,p2]
    return [p1]


def render_special(canvas, doc):
    canvas.saveState()
    draw_box(canvas, 0.25, 0.25)        # border box
    draw_header(canvas, HEADER, 0.3)    # add header & cross line
    draw_box(canvas, 0.6, 0.6, y1=0, y2=3.2)
    canvas.restoreState()


def main(info_map, email):
    get_info(info_map)
    header, sections = read_template()

    tag = email.split('@')[0]
    filename = f'pcpr_{tag}.pdf'

    buffer = BytesIO()

    pcpr = SimpleDocTemplate(
                             buffer, # 'tmp/' + filename,
                             pagesize=(8.5*inch, 11.0*inch),
                             topMargin=1*inch, bottomMargin=1*inch,
                             leftMargin=0.5*inch, rightMargin=0.5*inch)

    elements = []
    y_offset = 0
    for s in sections:
        elements.extend(_flowable_section(sections[s]))
    pcpr.build(elements, onFirstPage=render_special)

    buffer.seek(0)

    debug = True

    return filename, buffer

if __name__ == '__main__':
    main(None)