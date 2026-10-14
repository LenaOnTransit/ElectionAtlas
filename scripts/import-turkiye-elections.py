"""Build Türkiye's 1950–2023 national archive. Publishing is a separate transaction."""
import json,re,uuid,hashlib,colorsys,unicodedata
from builtins import round as round_builtin
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'scripts/turkiye-election-import';CACHE=ROOT/'.cache/turkiye'
TABLES=json.loads((OUT/'source-tables.json').read_text());PRIMARY=json.loads((OUT/'historical-primary-extract.json').read_text());LINKS=json.loads((OUT/'links.json').read_text())
CHECKED='2026-10-14';BOOK='https://cdn.tbmm.gov.tr/TbmmWeb/Yayinlar/Dosya/338840aa-508c-482f-a7dd-fd19f0254f3c.pdf'
HIST='https://www.ysk.gov.tr/doc/dosyalar/docs/Milletvekili/1950-1977/Turkiye.pdf';POST='https://www.ysk.gov.tr/doc/dosyalar/docs/Milletvekili/1983-2007/Turkiye.pdf';STATS='https://www.ysk.gov.tr/doc/dosyalar/docs/14Mayis2023CBSecimIstatistik.pdf'
OFFICIAL={'2011':'https://www.ysk.gov.tr/doc/dosyalar/docs/2011MilletvekiliSecimi/gumrukdahil/gumrukdahil.pdf','2015-June':'https://www.ysk.gov.tr/doc/dosyalar/docs/Milletvekili/7Haziran2015/KesinSecimSonuclari/ResmiGazete/D.pdf','2015-November':'https://www.ysk.gov.tr/doc/dosyalar/docs/Milletvekili/1Kasim2015/KesinSecimSonuclari/96-D.pdf','2018':'https://www.ysk.gov.tr/doc/dosyalar/docs/24Haziran2018/KesinSecimSonuclari/2018MV-96C.pdf','2023':STATS}
PRESOFF={2014:'https://www.ysk.gov.tr/doc/dosyalar/docs/2014CB/2014CB-Kesin-416_d_Genel.pdf',2018:'https://www.ysk.gov.tr/doc/dosyalar/docs/24Haziran2018/KesinSecimSonuclari/2018CB-416D.pdf',2023:'https://www.ysk.gov.tr/doc/dosyalar/docs/14Mayis2023/KesinSecimSonuclari/2023CB-TumSecimSonucu.pdf'}
def source(label,url):return dict(label=label,url=url)
def slug(s):return re.sub('[^a-z0-9]+','-',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip('-')
def num(s):
 s=s.replace(',','').strip()
 return float(s) if re.fullmatch(r'\d+(?:\.\d+)?',s) else None
def integer(s):
 n=num(s);return int(n) if n is not None and n.is_integer() else None
def trint(s):return int(s.replace('.',''))
NAMES={'Adalet Partisi':'Justice Party','Adalet ve Kalkınma Partisi':'Justice and Development Party','Anavatan Partisi':'Motherland Party','Aydınlık Türkiye Partisi':'Bright Turkey Party','Barış Partisi':'Peace Party','Bağımsız Türkiye Partisi':'Independent Turkey Party','Bağımsızlar':'Independents','Birlik Partisi':'Unity Party','Büyük Birlik Partisi':'Great Unity Party', 'Cumhuriyet Halk Partisi':"Republican People's Party",'Cumhuriyetçi Güven Partisi':'Republican Reliance Party','Cumhuriyetçi Köylü Millet Partisi':'Republican Villagers Nation Party','Cumhuriyetçi Millet Partisi':'Republican Nation Party','Demokrasi ve Barış Partisi':'Democracy and Peace Party','Demokrat Parti':'Democrat Party','Demokrat Türkiye Partisi':'Democratic Turkey Party','Demokratik Halk Partisi':"Democratic People's Party",'Demokratik Parti':'Democratic Party','Demokratik Sol Parti':'Democratic Left Party','Değişen Türkiye Partisi':'Changing Turkey Party','Doğru Yol Partisi':'True Path Party','Emek Partisi':'Labour Party','Fazilet Partisi':'Virtue Party','Genç Parti':'Young Party','Güven Partisi':'Reliance Party','Halkçı Parti':'Populist Party','Halkın Demokrasi Partisi':"People's Democracy Party",'Halkın Yükselişi Partisi':"People's Ascent Party",'Hürriyet Partisi':'Liberty Party','Islahatçı Demokrasi Partisi':'Reformist Democracy Party','Köylü Partisi':"Turkish Villagers' Party",'Liberal Demokrat Parti':'Liberal Democratic Party','Millet Partisi':'Nation Party','Milli Selamet Partisi':'National Salvation Party','Milliyetçi Demokrasi Partisi':'Nationalist Democracy Party','Milliyetçi Hareket Partisi':'Nationalist Movement Party','Milliyetçi Çalışma Partisi':'Nationalist Task Party','Refah Partisi':'Welfare Party','Saadet Partisi':'Felicity Party','Sosyaldemokrat Halkçı Parti':'Social Democratic Populist Party','Sosyalist Parti':'Socialist Party','Sosyalist İktidar Partisi':'Socialist Power Party','Türkiye Birlik Partisi':'Unity Party','Türkiye Komünist Partisi':'Communist Party of Turkey','Türkiye İşçi Partisi':"Workers' Party of Turkey",'Vatan Partisi':'Homeland Party','Yeni Demokrasi Hareketi':'New Democracy Movement','Yeni Parti':'New Party','Yeni Türkiye Partisi':'New Turkey Party','Yeniden Doğuş Partisi':'Rebirth Party','Yurt Partisi':'Homeland Party (Yurt Partisi)','Özgürlük ve Dayanışma Partisi':'Freedom and Solidarity Party','İşçi Partisi':"Workers' Party",'Halkların Demokratik Partisi':"Peoples' Democratic Party",'İyi Parti':'Good Party','Hür Dava Partisi':'Free Cause Party','Memleket Partisi':'Homeland Party (Memleket Partisi)','Adalet Birlik Partisi':'Justice Unity Party','Güç Birliği Partisi':'Power Union Party','Hak ve Özgürlükler Partisi':'Rights and Freedoms Party','Halkın Kurtuluş Partisi':"People's Liberation Party",'Milli Yol Partisi':'National Path Party','Sol Parti':'Left Party','Türkiye Komünist Hareketi':'Communist Movement of Turkey','Yeniden Refah Partisi':'New Welfare Party','Yenilik Partisi':'Innovation Party','Yeşiller ve Sol Gelecek Partisi':'Party of Greens and the Left Future','Zafer Partisi':'Victory Party','Hak ve Eşitlik Partisi':'Rights and Equality Party','Halkın Sesi Partisi':"People's Voice Party",'Milliyetçi ve Muhafazakar Parti':'Nationalist and Conservative Party','Millet ve Adalet Partisi':'Nation and Justice Party','Hak ve Adalet Partisi':'Rights and Justice Party','Merkez Parti':'Centre Party','Toplumsal Uzlaşma Reform ve Kalkınma Partisi':'Social Reconciliation Reform and Development Party','Anadolu Partisi':'Anatolia Party','Komünist Parti':'Communist Party','Halkın Yükselişi Partisi':"People's Ascent Party",'Vatan':'Patriotic Party'}
ALIASES={"People's Democratic Party":"Peoples' Democratic Party","Workers' Party":"Workers' Party of Turkey",'Turkey Unity Party':'Unity Party','Republican Trust Party':'Republican Reliance Party','Prosperity Party':'Welfare Party','Nationalist Labour Party':'Nationalist Task Party','Labour Party (Turkey)':'Labour Party','Labor Party':'Labour Party'}
INFO={
 'Justice and Development Party':('AKP','#f4a024',['conservatism'],'Justice_and_Development_Party_(Turkey)'),
 "Republican People's Party":('CHP','#d9252b',['social-democracy'],"Republican_People%27s_Party"),
 'Nationalist Movement Party':('MHP','#a91d22',['nationalism'],'Nationalist_Movement_Party'),
 "Peoples' Democratic Party":('HDP','#8b398f',['democratic-socialism','minority-politics'],"Peoples%27_Democratic_Party"),
 'Party of Greens and the Left Future':('YSP','#41944e',['green-politics','minority-politics'],'Party_of_Greens_and_the_Left_Future'),
 'Good Party':('İYİ','#43b6dc',['nationalism'],'Good_Party'),
 'Motherland Party':('ANAP','#df9f22',['liberal-conservatism'],'Motherland_Party_(Turkey)'),
 'True Path Party':('DYP','#e53037',['liberal-conservatism'],'True_Path_Party'),
 'Democrat Party':('DP','#bd222c',['liberal-conservatism'],'Democrat_Party_(Turkey,_1946–1960)'),
 'Justice Party':('AP','#d03336',['liberal-conservatism'],'Justice_Party_(Turkey)'),
 'Democratic Party':('DP','#cf5545',['conservatism'],'Democratic_Party_(Turkey,_1970)'),
 'Democratic Left Party':('DSP','#438bc2',['social-democracy'],'Democratic_Left_Party_(Turkey)'),
 'Social Democratic Populist Party':('SHP','#de493f',['social-democracy'],'Social_Democratic_Populist_Party_(Turkey)'),
 'Populist Party':('HP','#d36348',['social-democracy'],'Populist_Party_(Turkey)'),
 'Republican Nation Party':('CMP','#6f6395',['nationalism'],'Republican_Nation_Party'),
 'Republican Villagers Nation Party':('CKMP','#75613e',['national-conservatism'],'Republican_Villagers_Nation_Party'),
 'New Turkey Party':('YTP','#e5914a',[],'New_Turkey_Party_(1961)'),
 'Reliance Party':('GP','#855143',['republicanism'],'Reliance_Party'),
 'Republican Reliance Party':('CGP','#855143',['republicanism'],'Republican_Reliance_Party'),
 'Welfare Party':('RP','#e12e35',['islamism'],'Welfare_Party'),
 'Virtue Party':('FP','#cc2533',['islamism'],'Virtue_Party'),
 'National Salvation Party':('MSP','#26774b',['islamism'],'National_Salvation_Party'),
 'Felicity Party':('SP','#c62236',['islamism'],'Felicity_Party'),
 'New Welfare Party':('YRP','#b7252d',['islamism'],'New_Welfare_Party'),
 'Great Unity Party':('BBP','#d2232c',['nationalism'],'Great_Unity_Party'),
 'Free Cause Party':('HÜDA PAR','#4b8c37',['islamism'],'Free_Cause_Party'),
 "Workers' Party of Turkey":('TİP','#ba1729',['democratic-socialism'],"Workers%27_Party_of_Turkey_(2017)"),
 'Communist Party of Turkey':('TKP','#a92228',['communism'],'Communist_Party_of_Turkey_(2001)'),
 'Communist Movement of Turkey':('TKH','#a92228',['communism'],'Communist_Movement_of_Turkey'),
 'Communist Party':('KP','#a92228',['communism'],'Communist_Party_(Turkey,_2014)'),
 'Labour Party':('EMEP','#cf252d',['marxism-leninism'],'Labour_Party_(Turkey)'),
 'Freedom and Solidarity Party':('ÖDP','#df3034',['democratic-socialism'],'Freedom_and_Solidarity_Party'),
 'Left Party':('SOL','#df3034',['democratic-socialism'],'Left_Party_(Turkey)'),
 'Liberal Democratic Party':('LDP','#265da3',['classical-liberalism'],'Liberal_Democratic_Party_(Turkey)'),
 'Victory Party':('ZP','#bc1f29',['nationalism'],'Victory_Party_(Turkey)'),
 'Homeland Party (Memleket Partisi)':('MP','#267cc0',['republicanism'],'Homeland_Party_(Turkey,_2021)'),
 "Democratic People's Party":('DEHAP','#75943d',['minority-politics'],"Democratic_People%27s_Party_(Turkey)"),
 "People's Democracy Party":('HADEP','#b1942e',['minority-politics'],"People%27s_Democracy_Party"),
 'Patriotic Party':('VATAN','#cb2934',['nationalism'],'Patriotic_Party_(Turkey)'),
 'Nationalist Task Party':('MÇP','#a91d22',['nationalism'],'Nationalist_Task_Party'),
 'Nation Party':('MP','#6c528d',[],'Nation_Party_(Turkey,_1992)'),
 'Nationalist Democracy Party':('MDP','#495a8a',[],'Nationalist_Democracy_Party'),
 'Unity Party':('TBP','#876386',[],'Unity_Party_(Turkey)'),
}
records=[];profiles={};audit=[]
def canon(name):return ALIASES.get(name,name)
def profile(name,year):
 name=canon(name)
 if name in ['', 'Independent','Independents']:return None
 key=name
 if name=='Democrat Party':key+= ' (1946–1960)' if year<=1960 else ' (2007)'
 if name=='Justice Party':key+= ' (1961–1980)' if year<1980 else ' (2015)'
 if name=='Motherland Party' and year>2009:key+=' (2011)'
 if name=='New Turkey Party':key+= ' (1961)' if year<1980 else ' (2002)'
 if name=='Nation Party':key+= ' (1948)' if year<1960 else ' (1962)' if year<1980 else ' (1992)'
 if name=="Workers' Party of Turkey":key+= ' (1961)' if year<1980 else ' (2017)'
 if name=="Workers' Party" and year==1954:key='Democratic Labour Party (1950)'
 if name=='Homeland Party':key+=' (1954)' if year<1960 else ' (1991)'
 if name=='Communist Party of Turkey':key+=' (2001)'
 if key=='Nation Party (1948)':page_override='Nation_Party_(Turkey,_1948)'
 elif key=='Nation Party (1962)':page_override='Nation_Party_(Turkey,_1962)'
 else:page_override=None
 if name not in INFO:key+= ' — '+str(year)  # no unsupported continuity for minor ballot labels
 short,color,tags,page=INFO.get(name,('',None,[],None))
 if page_override:page=page_override
 if key=='Democrat Party (2007)':page='Democrat_Party_(Turkey,_2007)'
 if key=='Justice Party (2015)':page='Justice_Party_(Turkey,_2015)';tags=[]
 if key=='Motherland Party (2011)':tags=[];page=None
 if key=='New Turkey Party (2002)':page='New_Turkey_Party_(2002)'
 if key=="Workers' Party of Turkey (1961)":page='Workers%27_Party_of_Turkey_(1961)'
 profile_tags=list(tags)
 if name=="Republican People's Party" and year<1965:tags=['republicanism','nationalism']
 if color is None:
  h=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)/0xffffffff;color='#'+''.join(f'{round(x*255):02x}' for x in colorsys.hls_to_rgb(h,.43,.55))
 sources=[source('Party history and political tradition','https://en.wikipedia.org/wiki/'+page)] if page else []
 if name=='Justice and Development Party':sources.append(source('AKP: conservative-democratic political identity','https://www.akparti.org.tr/haberler/ak-partinin-kimligi-muhafazakar-ve-demokrat-kimligidir-13012021-170005/'))
 if name=="Workers' Party of Turkey" and year>=2017:sources.append(source('TİP: socialist party programme','https://www.tip.org.tr/parti-programi'))
 if name=='Nationalist Movement Party':sources.append(source('MHP: nationalist principles and programme','https://www.mhp.org.tr/htmldocs/mhp/355/mhp/index.html'))
 if key not in profiles:profiles[key]=dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/party/tr/'+key)),country_id='tr',name=key,short_name=short,color=color,ideology_ids=['ideology-'+t for t in profile_tags],notes='Historical ballot identity. Colours are an editorial display palette. Ideology labels describe the broad party tradition, not each individual candidate. '+('Sources: '+', '.join(s['url'] for s in sources) if sources else 'Ideology is unassessed; no classification or continuity is inferred.'),archived=False)
 return profiles[key],['ideology-'+t for t in tags],sources
def result(e,name,votes=None,share=None,seats=None,party=None,winner=False):
 name=canon(name);party=canon(party) if party is not None else name;p=profile(party,int(e['startDate'][:4]))
 r=dict(id=e['id']+'-r'+str(len(e['results'])+1),name=name,party=party,color=p[0]['color'] if p else '#808080',votes=votes,share=share,seats=seats,previousSeats=None,electoralVotes=None,winner=winner,advanced=False,ideologyIds=p[1] if p else [])
 if p:r.update(partyId=p[0]['id'],ideologyBasis=dict(kind='party-era' if p[2] else 'unassessed',year=int(e['startDate'][:4]),note='Broad election-era party tradition; not a personal ideology classification.',sources=p[2]))
 e['results'].append(r);return r
def base(date,office,total=None,method='direct'):
 title={'assembly':'Grand National Assembly','senate':'Senate of the Republic','president':'presidential'}[office]
 e=dict(id=f'world-turkiye-{office}-{date}',countryId='tr',title=f'Türkiye {title} election {date[:4]}',type='presidential' if office=='president' else 'parliamentary',body='President of Türkiye' if office=='president' else 'Senate of the Republic (Cumhuriyet Senatosu)' if office=='senate' else 'Grand National Assembly (Türkiye Büyük Millet Meclisi)',startDate=date,endDate='',precision='day',dateStatus='confirmed',status='held',publication='published',round='General',seriesId='turkiye-'+office,snap=False,summary='',government='',turnout=None,totalSeats=total,resultStatus='final',resultCoverage='complete',voteBasis='',results=[],sources=[],checked=CHECKED,notes='',articleId='',version=1,electionMethod=method,linkedElectionIds=[])
 records.append(e);return e
def gettable(key,field='Seats'):
 return next(t for t in TABLES[key] if any(c['text']==field for r in t['rows'] for c in r))
def tablerows(t,field='Seats',vote_index=None):
 hi,h=next((i,[c['text'] for c in row]) for i,row in enumerate(t['rows']) if 'Votes' in [c['text'] for c in row] and field in [c['text'] for c in row])
 vi=h.index('Votes') if vote_index is None else vote_index;si=h.index('Seats') if 'Seats' in h else None
 rows=[];meta={}
 for row in t['rows'][hi+1:]:
  if len(row)<=vi:continue
  texts=[c['text'] for c in row];names=list(dict.fromkeys(x for x in texts[:vi] if x))
  if not names:continue
  if names[0] in ['Total','Valid votes','Invalid/blank votes','Total votes','Registered voters/turnout','Total MP/turnout']:
   meta[names[0]]=dict(votes=integer(texts[vi]),share=num(texts[vi+1]) if len(texts)>vi+1 else None,seats=integer(texts[si]) if si is not None and len(texts)>si else None);continue
  if 'Total' in names or names[0].startswith('Source:'):continue
  v=integer(texts[vi]);s=integer(texts[si]) if si is not None and len(texts)>si else None
  if v is None:continue
  name=names[-1];party=names[-1] if field=='Candidate' else None
  if field=='Candidate':name=names[0]
  rows.append(dict(name=canon(name),party=canon(party) if party else None,votes=v,seats=s or 0))
 return rows,meta
DATES={'1950':'1950-05-14','1954':'1954-05-02','1957':'1957-10-27','1961':'1961-10-15','1965':'1965-10-10','1969':'1969-10-12','1973':'1973-10-14','1977':'1977-06-05','1983':'1983-11-06','1987':'1987-11-29','1991':'1991-10-20','1995':'1995-12-24','1999':'1999-04-18','2002':'2002-11-03','2007':'2007-07-22','2011':'2011-06-12','2015-June':'2015-06-07','2015-November':'2015-11-01','2018':'2018-06-24','2023':'2023-05-14'}
previous={}
for key,date in DATES.items():
 y=int(date[:4]);rows,meta=tablerows(gettable('parliament-'+key));e=base(date,'assembly');valid=meta['Total']['votes'];total=meta['Total']['seats'];cast=meta.get('Total votes',{}).get('votes');registered=meta.get('Registered voters/turnout',{}).get('votes');turnout=meta.get('Registered voters/turnout',{}).get('share')
 if key in PRIMARY:
  p=PRIMARY[key];rows=[]
  for x in p['rows']:
   original=re.sub(r'\s*\([^)]*\)$','',x['name']);name=NAMES[original]
   if original=='İşçi Partisi':name='Democratic Labour Party' if y==1954 else 'Patriotic Party'
   if original=='Vatan Partisi':name='Homeland Party' if y<1960 else 'Patriotic Party'
   rows.append(dict(name=name,votes=x['votes'],seats=x['seats']))
  total=trint(p['Milletvekili sayısı']);valid=trint(p.get('Toplam geçerli oy sayısı',p.get('Geçerli oy sayısı',str(sum(r['votes'] for r in rows)))));cast=trint(p['Oy kullanan seçmen sayısı']);registered=trint(p['Kayıtlı seçmen sayısı']);turnout=round(cast/registered*100,6)
 e['totalSeats']=400 if y==1983 else total;e['majorityThreshold']=e['totalSeats']//2+1;e['turnout']=turnout
 e['snap']=key in ['1957','1987','1991','1995','1999','2002','2007','2011','2015-November','2018','2023']
 if y==2023:
  # Certified YSK bulletin pp.35–37 supersedes the inconsistent secondary table.
  values=[('Adalet Birlik Partisi',41196),('Adalet Partisi',109236),('Adalet ve Kalkınma Partisi',19392462),('Anavatan Partisi',66102),('Büyük Birlik Partisi',530770),('Cumhuriyet Halk Partisi',13802183),('Genç Parti',112972),('Güç Birliği Partisi',26359),('Hak ve Özgürlükler Partisi',42509),('Halkın Kurtuluş Partisi',31831),('İyi Parti',5275981),('Memleket Partisi',502669),('Millet Partisi',52315),('Milli Yol Partisi',17758),('Milliyetçi Hareket Partisi',5484820),('Sol Parti',77992),('Türkiye İşçi Partisi',956057),('Türkiye Komünist Hareketi',17476),('Türkiye Komünist Partisi',63809),('Vatan',52720),('Yeniden Refah Partisi',1527048),('Yenilik Partisi',11171),('Yeşiller ve Sol Gelecek Partisi',4803922),('Zafer Partisi',1216399),('Bağımsızlar',226831)]
  seats={'Adalet ve Kalkınma Partisi':268,'Cumhuriyet Halk Partisi':169,'İyi Parti':43,'Milliyetçi Hareket Partisi':50,'Türkiye İşçi Partisi':4,'Yeniden Refah Partisi':5,'Yeşiller ve Sol Gelecek Partisi':61}
  rows=[dict(name=NAMES[n],votes=v,seats=seats.get(n,0)) for n,v in values];valid=54442588;cast=55835895;registered=64145504;e['turnout']=87.05
 if key.startswith('2015'):e['title']=f'Türkiye Grand National Assembly election {"June" if "June" in key else "November"} 2015'
 e['sources']=[source('YSK: national party votes, turnout and election seats',HIST if y<1980 else POST if y<=2007 else OFFICIAL[key]),source('Detailed historical result table and bibliography',LINKS['parliament-'+key])]
 if y<1980:e['sources'].append(source('TBMM: parliamentary history and electoral systems',BOOK))
 e['voteBasis']=f'Published national party/list votes; denominator {valid:,}; overseas/customs votes included where recorded'
 e['notes']='Party/list votes and seats follow the election-era ballot labels. Coalition subtotal rows are excluded to avoid double counting. Seats are mandates won by each ballot list, including candidates of allied parties on that list; they are not a later party-membership snapshot. Previous seats compare the immediately preceding general election only where the same organisation and ballot identity can be matched. Independents and changed alliances have no inferred comparison. Colours are an editorial palette; ideological labels describe broad party traditions, not individual candidates.'
 if y<=1957:e['notes']+=' The official YSK historical compilation does not report a separate valid-ballot denominator for this election. Shares here use the sum of the published party vote rows; they should not be combined with different valid-vote figures in other historical compilations.'
 if y==1950:e['notes']+=' Party rows sum to 7,953,394, 309 more than the 7,953,085 voters printed in the same YSK compilation. Both published counts are retained; the difference is not assigned to a fictional party.'
 if y==1977:e['notes']+=' YSK reports 15,358,210 voters; the parliamentary website has a different 15,368,210 figure. The YSK series is used consistently.'
 if y==1983:e['notes']+=' Only three parties were permitted to contest this military-supervised election. The chamber had 400 positions, but the certified historical allocation records 399 elected members; the unfilled seat is not assigned to an invented party. Earlier banned parties and later reconstituted organisations are not assigned predecessor seat comparisons.'
 if y==1961:e['notes']+=' The YSK party rows sum to 10,141,243, exceeding the printed 10,138,035 valid-vote total by 3,208. Counts and the printed denominator are retained, with partial coverage; no residual is fabricated.'
 if y==1969:e['notes']+=' The YSK party rows sum to 9,089,866, exceeding the printed 9,086,296 valid-vote total by 3,570. Counts and the printed denominator are retained, with partial coverage; no residual is fabricated.'
 if y==1991:e['notes']+=' The SHP ballot included HEP candidates; the Welfare Party ballot included nationalist and reformist allies. Those shared ballot seats are not split into independent vote rows.'
 if y==2002:e['notes']+=' The November allocation predates the March 2003 Siirt repeat election, which changed the AKP/CHP seat totals. This record preserves the general-election allocation of 363 AKP and 178 CHP seats.'
 if y==2011:e['notes']+=' The final allocation uses 327 AKP seats and 35 independent seats after Hatip Dicle’s mandate was disallowed; preliminary 326/36 figures are not used.'
 if y==2023:e['notes']+=' Certified totals follow YSK’s election statistics bulletin (54,442,588 valid votes), not the inconsistent 53,962,770 total in the secondary table. AKP and CHP list seats include their allied candidates; the Green Left list is not retroactively relabelled HDP.'
 for x in sorted(rows,key=lambda r:-r['votes']):
  r=result(e,x['name'],x['votes'],round(x['votes']/valid*100,6),x['seats']);pid=r.get('partyId')
  if pid and y not in [1950,1961,1983] and x['name'] not in ['Welfare Party','Social Democratic Populist Party'] and not (y==2023 and x['name']=='Party of Greens and the Left Future'):
   r['previousSeats']=previous.get(pid)
  if (y,x['name']) in [(2002,'Justice and Development Party'),(2018,'Good Party'),(2023,'New Welfare Party'),(2023,'Victory Party'),(2023,'Homeland Party (Memleket Partisi)')]:r['previousSeats']=0
 e['summary']=max(e['results'],key=lambda r:r['votes'])['name']+' received the most national list votes.'
 vote_sum=sum(r['votes'] for r in e['results']);seat_sum=sum(r['seats'] for r in e['results'])
 e['resultCoverage']='complete' if vote_sum==valid and seat_sum==e['totalSeats'] and y not in [1950,1954,1957] else 'partial'
 audit.append(dict(id=e['id'],expectedVotes=valid,recordedVotes=vote_sum,expectedSeats=e['totalSeats'],recordedSeats=seat_sum,voters=cast,registered=registered,source=e['sources'][0]['url']))
 previous={r['partyId']:r['seats'] for r in e['results'] if 'partyId' in r}
SDATES={1961:'10-15',1964:'06-07',1966:'06-05',1968:'06-02',1973:'10-14',1975:'10-12',1977:'06-05',1979:'10-14'}
for y,day in SDATES.items():
 rows,meta=tablerows(gettable('senate-'+str(y)));valid=meta['Total']['votes'];total=meta['Total']['seats'];cast=meta['Total votes']['votes'];registered=meta['Registered voters/turnout']['votes'];e=base(f'{y}-{day}','senate',total)
 e['round']='General' if y==1961 else 'Partial renewal';e['turnout']=round(cast/registered*100,6)
 e['sources']=[source('Historical Senate result table, citing Nohlen et al., Elections in Asia and the Pacific',LINKS['senate-'+str(y)]),source('TBMM: Senate renewals and parliamentary history',BOOK),source('Constitutional Court: 1961 Constitution, Senate composition','https://www.anayasa.gov.tr/tr/mevzuat/onceki-anayasalar/1961-anayasasi')]
 e['voteBasis']=f'Valid votes in the Senate constituencies voting in this election; {valid:,} votes'
 e['notes']='Seats show only the mandates reported for this election, not the full Senate. In 1961 all 150 popularly elected seats were contested; later contests renewed one geographic cohort and, where included in the source table, vacant seats. Presidential appointees and lifetime members are outside these popular-vote result rows. Turnout applies only to the voting constituencies. Votes follow the detailed historical compilation; no independent district-by-district recount is claimed. Previous seats are blank because an exact outgoing-cohort allocation has not been established. A missing comparison is not zero.'
 if y==1968:e['notes']+=' The detailed table reports 3,595,976 voters / 5,420,255 electors (66.34%). The TBMM narrative gives 53.2%; turnout here follows the detailed table’s internally reproducible electorate, without mixing the two scopes.'
 for x in rows:result(e,x['name'],x['votes'],round(x['votes']/valid*100,6),x['seats'])
 e['summary']=f'The Senate election returned {total} popularly elected members in the constituencies voting.'
 assert sum(r['votes'] for r in e['results'])==valid;assert sum(r['seats'] for r in e['results'])==total
 audit.append(dict(id=e['id'],expectedVotes=valid,recordedVotes=valid,expectedSeats=total,recordedSeats=total,voters=cast,registered=registered,source=e['sources'][0]['url']))
# Public presidential ballots: each runoff is a separate dated election record.
for y,day in [(2014,'08-10'),(2018,'06-24'),(2023,'05-14')]:
 t=gettable('president-'+str(y),'Candidate');rows,meta=tablerows(t,'Candidate');valid=meta['Total']['votes'];e=base(f'{y}-{day}','president');e['round']='First round';e['turnout']=meta['Registered voters/turnout']['share']
 e['sources']=[source('YSK: certified national presidential result including overseas and customs ballots',PRESOFF[y]),source('Candidate result table and bibliography',LINKS['president-'+str(y)])]
 e['voteBasis']=f'Valid presidential candidate votes; {valid:,} votes; overseas/customs ballots included'
 e['notes']='Shares are recalculated from valid candidate votes, excluding blank and invalid ballots. Party labels identify the candidate’s affiliation at the election; supporting multi-party alliances are not counted as additional votes. Ideology refers to the affiliated party’s broad tradition, not a separately inferred personal classification.'
 if y==2023:e['notes']+=' Muharrem İnce withdrew before election day but remained on the ballot; his certified votes are retained. No candidate won an outright majority in this round.'
 for x in rows:
  r=result(e,x['name'],x['votes'],round(x['votes']/valid*100,6),party=x['party'],winner=x['name']=='Recep Tayyip Erdoğan' and y!=2023)
  if y==2023:r['advanced']=x['name'] in ['Recep Tayyip Erdoğan','Kemal Kılıçdaroğlu']
 if y==2023:
  e2=base('2023-05-28','president');e2.update(title='Türkiye presidential runoff election 2023',round='Runoff',turnout=84.15,voteBasis='Valid presidential runoff candidate votes; 53,339,313 votes; overseas/customs ballots included',notes=e['notes'].split(' Muharrem')[0],sources=[source('YSK: certified national presidential runoff result','https://www.ysk.gov.tr/doc/dosyalar/docs/14Mayis2023/KesinSecimSonuclari/2023CB-TumSecimSonucuIkinciTur.pdf')])
  for n,p,v in [('Recep Tayyip Erdoğan','Justice and Development Party',27834589),('Kemal Kılıçdaroğlu',"Republican People's Party",25504724)]:result(e2,n,v,round(v/53339313*100,6),party=p,winner=n=='Recep Tayyip Erdoğan')
  e2['summary']='Recep Tayyip Erdoğan won the presidential runoff.';audit.append(dict(id=e2['id'],expectedVotes=53339313,recordedVotes=53339313,expectedSeats=None,recordedSeats=None,source=e2['sources'][0]['url']))
 e['summary']='No candidate received an outright majority; the leading two candidates advanced to the runoff.' if y==2023 else 'Recep Tayyip Erdoğan won the presidential election.'
 assert sum(r['votes'] for r in e['results'])==valid
 audit.append(dict(id=e['id'],expectedVotes=valid,recordedVotes=valid,expectedSeats=None,recordedSeats=None,source=e['sources'][0]['url']))
# Decisive parliamentary presidential ballot only; shares use all ballots cast,
# including blank/invalid ballots. Public turnout is not applicable.
INDIRECT=[
 (1950,'05-22',453,1,[('Celâl Bayar','Democrat Party',387),('İsmet İnönü',"Republican People's Party",64),('Halil İbrahim Özyörük','Democrat Party',1)],'First parliamentary ballot',BOOK,'TBMM history p.194 records 64 votes for İnönü, one for Özyörük and one abstention; the secondary 66-vote İnönü figure is not used.'),
 (1954,'05-14',513,27,[('Celâl Bayar','Democrat Party',486)],'First parliamentary ballot',BOOK,'The 27 abstentions are not assigned to an invented rival candidate. The secondary table’s 27 votes for İnönü is not used.'),
 (1957,'11-01',413,0,[('Celâl Bayar','Democrat Party',413)],'First parliamentary ballot',BOOK,''),
 (1961,'10-26',607,173,[('Cemal Gürsel','Independent',434)],'First parliamentary ballot','https://www5.tbmm.gov.tr/tutanaklar/TUTANAK/TBMM/t01/c001/tbmm01001002.pdf','No other candidate stood. Blank ballots are excluded from candidate rows.'),
 (1966,'03-28',532,52,[('Cevdet Sunay','Independent',461),('Alparslan Türkeş','Republican Villagers Nation Party',11),('Ali Fuat Başgil','Independent',1),('İsmet İnönü',"Republican People's Party",1),('Celal Ertuğ','Independent',1),('Kasım Gülek','Independent',1),('Sadettin Bilgiç','Independent',1),('Turhan Dilligil','Independent',2),('Osman Turan','Independent',1)],'First parliamentary ballot','https://www5.tbmm.gov.tr/tutanaklar/TUTANAK/TBMM/t05/c005/tbmm05005005.pdf','Named write-in votes are retained. The minutes also record 47 blank ballots and five votes for an unnamed person who was not a parliamentarian; these five are not assigned to a guessed candidate.'),
 (1973,'04-06',557,30,[('Fahri Korutürk','Independent',365),('Faruk Gürler','Independent',87),('Ferruh Bozbeyli','Democratic Party',51),('Tekin Arıburun','Independent',17),('İsmet İnönü',"Republican People's Party",3),('Sabit Osman Avcı','Independent',2),('Ali Naili Erdem','Independent',1),('Rıfat Öztürkçine','Independent',1)],'15th parliamentary ballot',BOOK,'The decisive 15th ballot included 27 blank and three invalid votes. Votes for named non-candidates are retained as reported.'),
 (1989,'10-31',285,8,[('Turgut Özal','Motherland Party',263),('Fethi Çelikbaş','Motherland Party',14)],'Third parliamentary ballot','https://www5.tbmm.gov.tr/tutanaklar/TUTANAK/TBMM/d18/c033/tbmm18033024.pdf',''),
 (1993,'05-16',431,19,[('Süleyman Demirel','True Path Party',244),('Kâmran İnan','Motherland Party',94),('Lütfi Doğan','Welfare Party',47),('İsmail Cem',"Republican People's Party",27)],'Third parliamentary ballot','https://www5.tbmm.gov.tr/tutanaklar/TUTANAK/TBMM/d19/c035/tbmm19035103.pdf','The minutes record 19 blank votes in addition to the 412 named-candidate votes.'),
 (2000,'05-05',533,16,[('Ahmet Necdet Sezer','Independent',330),('Nevzat Yalçıntaş','Virtue Party',113),('Sadi Somuncuoğlu','Nationalist Movement Party',43),('Rasim Zaimoğlu','True Path Party',24),('Mehmet Mail Büyükerman','Democratic Left Party',7)],'Third parliamentary ballot','https://www5.tbmm.gov.tr/tutanaklar/TUTANAK/TBMM/d21/c032/tbmm21032090.pdf',''),
 (2007,'08-28',448,26,[('Abdullah Gül','Justice and Development Party',339),('Sabahattin Çakmakoğlu','Nationalist Movement Party',70),('Hüseyin Tayfun İçli','Democratic Left Party',13)],'Third parliamentary ballot','https://www5.tbmm.gov.tr/tutanaklar/TUTANAK/TBMM/d23/c001/tbmm23001006.pdf','The decisive August ballot followed the invalidated April process and the July parliamentary election. The minutes record 24 blank and two invalid ballots.')]
for y,day,cast,noncandidate,rows,round,url,note in INDIRECT:
 e=base(f'{y}-{day}','president',method='indirect');e['title']=f'Türkiye parliamentary presidential election {y}';e['round']=round;e['sources']=[source('TBMM: parliamentary presidential selection and decisive ballot',url),source('TBMM: parliamentary history',BOOK)]
 e['voteBasis']=f'Legislators’ votes in the decisive parliamentary ballot; shares of all {cast} ballots cast, including blank/invalid votes'
 e['notes']='This was an indirect parliamentary presidential selection, not a public national ballot. Only the decisive ballot is displayed; earlier rounds are not added to its votes. The vote-share denominator includes blank and invalid ballots, so named-candidate shares need not sum to 100%. Public turnout and popular-vote totals are not applicable. Party affiliations describe the election era, while independent/write-in candidates have no inferred ideology. '+note
 for i,(n,p,v) in enumerate(rows):result(e,n,v,round_builtin(v/cast*100,6),party=p,winner=i==0)
 e['summary']=rows[0][0]+' was elected President by Parliament.'
 assert sum(r['votes'] for r in e['results'])+noncandidate==cast
 audit.append(dict(id=e['id'],expectedVotes=cast-noncandidate,recordedVotes=sum(r['votes'] for r in e['results']),ballotsCast=cast,nonCandidateBallots=noncandidate,expectedSeats=None,recordedSeats=None,source=url))

for e in records:e['linkedElectionIds']=[x['id'] for x in records if x['id']!=e['id'] and x['startDate'][:4]==e['startDate'][:4]]
records.sort(key=lambda e:(e['startDate'],e['id']))
for name,value in [('records',records),('parties',list(profiles.values())),('reconciliation',audit)]:
 (OUT/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n')
print(f'{len(records)} elections; {len(profiles)} party profiles; {sum(len(e["results"]) for e in records)} result rows')
