from html.parser import HTMLParser
import re
class Tables(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.tables=[];self.stack=[];self.sup=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='sup':self.sup+=1
  if tag=='table':
   t={'rows':[],'row':None,'cell':None};self.tables.append(t);self.stack.append(t)
  elif self.stack:
   t=self.stack[-1]
   if tag=='tr':
    if t['row'] is not None:self.endrow(t)
    t['row']=[]
   elif tag in ('td','th'):
    if t['cell'] is not None:self.endcell(t)
    t['cell']={'text':'','tag':tag,**a,'winner':False}
   elif tag=='img' and t['cell'] is not None:
    if 'winner' in a.get('alt','').lower() or 'check_circle' in a.get('src',''):t['cell']['winner']=True
   elif tag=='br' and t['cell'] is not None:t['cell']['text']+=' '
 def endcell(self,t):
  t['cell']['text']=re.sub(r'\s+',' ',t['cell']['text']).strip()
  if t['row'] is not None:t['row'].append(t['cell'])
  t['cell']=None
 def endrow(self,t):
  if t['cell'] is not None:self.endcell(t)
  t['rows'].append(t['row']);t['row']=None
 def handle_endtag(self,tag):
  if tag=='sup':self.sup=max(0,self.sup-1)
  if self.stack:
   t=self.stack[-1]
   if tag in ('td','th') and t['cell'] is not None:self.endcell(t)
   elif tag=='tr' and t['row'] is not None:self.endrow(t)
   elif tag=='table':
    if t['row'] is not None:self.endrow(t)
    self.stack.pop()
 def handle_data(self,data):
  if not self.sup:
   for t in self.stack:
    if t['cell'] is not None:t['cell']['text']+=data

def read(path):
 p=Tables();p.feed(path.read_text());return [t['rows']for t in p.tables]

def expand(rows):
 grid=[];spans={}
 for row in rows:
  line=[];col=0
  def oldcell(col):
   old,n=spans[col];line.append(old)
   if n==1:del spans[col]
   else:spans[col]=(old,n-1)
  for cell in row:
   while col in spans:oldcell(col);col+=1
   cs=int(cell.get('colspan',1));rs=int(cell.get('rowspan',1))
   for _ in range(cs):
    line.append(cell)
    if rs>1:spans[col]=(cell,rs-1)
    col+=1
  while col in spans:oldcell(col);col+=1
  grid.append(line)
 return grid
