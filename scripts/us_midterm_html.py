"""Small auditable HTML reader for historical result tables."""
from html.parser import HTMLParser
import re

class Reader(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.tables=[];self.stack=[];self.skip=0;self.heading='';self.heading_text=None;self.level=0;self.state='';self.caption=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag in ('style','script','sup'):self.skip+=1
  if tag in ('h2','h3','h4') and not self.stack:self.heading_text='';self.level=int(tag[1])
  if tag=='caption':self.caption=True
  if tag=='table':
   t={'rows':[],'row':None,'cell':None,'heading':self.heading,'state':self.state,'caption':''};self.tables.append(t);self.stack.append(t)
  if self.stack:
   t=self.stack[-1]
   if tag=='tr':t['row']=[]
   if tag in ('td','th'):t['cell']={'text':'','links':[],**a}
   if tag=='a' and t['cell'] is not None:t['cell']['links'].append(a.get('href',''))
   if tag in ('br','li','p') and t['cell'] is not None:t['cell']['text']+='\n'
 def handle_data(self,text):
  if self.skip:return
  if self.heading_text is not None:self.heading_text+=text
  if self.caption and self.stack:self.stack[-1]['caption']+=text
  for t in self.stack:
   if t['cell'] is not None:t['cell']['text']+=text
 def handle_endtag(self,tag):
  if tag=='caption':self.caption=False
  if tag in ('style','script','sup'):self.skip=max(0,self.skip-1)
  if tag in ('h2','h3','h4') and self.heading_text is not None:
   self.heading=re.sub(r'\s+',' ',self.heading_text).strip();self.heading_text=None
   if self.level==2:self.state=self.heading
  if self.stack:
   t=self.stack[-1]
   if tag in ('td','th') and t['cell'] is not None:
    t['cell']['text']=re.sub(r'[^\S\n]+',' ',t['cell']['text']).strip()
    if t['row'] is not None:t['row'].append(t['cell'])
    t['cell']=None
   if tag=='tr' and t['row'] is not None:t['rows'].append(t['row']);t['row']=None
   if tag=='caption':self.caption=True
  if tag=='table':self.stack.pop()

def read(path):
 p=Reader();p.feed(path.read_text());return p.tables
