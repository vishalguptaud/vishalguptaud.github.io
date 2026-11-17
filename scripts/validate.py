"""Check content schemas, link destinations, contrast, and public-file hygiene."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from cms_schema import editor_schema

def check_fields(value,fields,path):
    if not isinstance(value,dict): raise ValueError(path+' must be an object')
    for f in fields:
        key=f['name']; p=path+'.'+key
        if key not in value: raise ValueError(p+' is missing')
        v=value[key]; kind=f['widget']
        if kind=='list':
            if not isinstance(v,list): raise ValueError(p+' must be a list')
            for i,item in enumerate(v):
                if 'fields' in f: check_fields(item,f['fields'],p+f'[{i}]')
                elif not isinstance(item,str): raise ValueError(p+' items must be text')
        elif kind=='boolean':
            if not isinstance(v,bool): raise ValueError(p+' must be true or false')
        elif kind=='number':
            if isinstance(v,bool) or not isinstance(v,(int,float)): raise ValueError(p+' must be a number')
            if f.get('min',-1e100)>v or f.get('max',1e100)<v: raise ValueError(p+' is outside its allowed range')
        else:
            if not isinstance(v,str): raise ValueError(p+' must be text')
            if kind=='select' and v not in f['options']: raise ValueError(p+' is not an allowed choice')
            if kind=='color' and not re.fullmatch(r'#[0-9A-Fa-f]{6}',v): raise ValueError(p+' must be a hex color')
            if kind=='image' and v:
                if not v.startswith('assets/') or '..' in Path(v).parts: raise ValueError(p+' must be a local assets/ image path')
                if not (ROOT/'static'/v).is_file(): raise ValueError(p+' image does not exist: '+v)

def luminance(color):
    parts=[int(color[i:i+2],16)/255 for i in (1,3,5)]
    parts=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in parts]
    return sum(v*w for v,w in zip(parts,(.2126,.7152,.0722)))
def contrast(a,b):
    hi,lo=sorted([luminance(a),luminance(b)],reverse=True)
    return (hi+.05)/(lo+.05)

class Page(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True);self.ids=[];self.refs=[];self.h1=0;self.images=[];self.links=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='h1':self.h1+=1
        for key in ('src','href'):
            if key in a:self.refs.append(a[key])
        if tag=='img':self.images.append(a)
        if tag=='a':self.links.append(a)

def validate():
    for section in editor_schema():
        value=json.loads((ROOT/'content'/f'{section["name"]}.json').read_text())
        check_fields(value,section['fields'],section['name'])
    settings=json.loads((ROOT/'content/settings.json').read_text())
    pairs=[('body text','#26372F',settings['background_color']),
           ('headings',settings['primary_color'],settings['background_color']),
           ('accent text',settings['accent_color'],settings['background_color']),
           ('navigation','#FFFDF7',settings['primary_color'])]
    for label,a,b in pairs:
        ratio=contrast(a,b)
        if ratio<4.5:raise ValueError(f'{label} contrast is {ratio:.2f}:1; choose colors giving at least 4.5:1.')
    research=json.loads((ROOT/'content/research.json').read_text())
    ids=[p['id'] for p in research['projects']]
    if len(ids)!=len(set(ids)):raise ValueError('Research section identifiers must be unique.')
    if not all(re.fullmatch('[a-z][a-z0-9-]*',i) for i in ids):raise ValueError('Research identifiers must use lowercase letters, digits, and hyphens.')
    dist=ROOT/'dist';pages={p.resolve():Page(p.read_text()) for p in dist.rglob('*.html')}
    references=0
    for path,page in pages.items():
        if page.h1!=1:raise ValueError(str(path)+' must have one main heading')
        if len(page.ids)!=len(set(page.ids)):raise ValueError(str(path)+' has duplicate IDs')
        for image in page.images:
            if not image.get('alt'):raise ValueError(str(path)+' has an image without a description')
        for ref in page.refs:
            parts=urlsplit(ref)
            if parts.scheme:
                if parts.scheme not in ('http','https','mailto'):raise ValueError('Unsafe external URL: '+ref)
                continue
            target=(path.parent/unquote(parts.path)).resolve() if parts.path else path
            if target.is_dir():target=target/'index.html'
            if not target.is_relative_to(dist.resolve()):raise ValueError('Link escapes the published directory: '+ref)
            if not target.exists():raise ValueError(f'Broken local reference in {path.name}: {ref}')
            if parts.fragment and target in pages and parts.fragment not in pages[target].ids:
                raise ValueError('Missing section target: '+ref)
            references+=1
    for forbidden in ('content','scripts','tests','.git','.github','.openai'):
        if (dist/forbidden).exists():raise ValueError('Source-only directory was copied into the website: '+forbidden)
    if b'Exif\x00\x00' in (dist/'assets/vishal-photo.jpg').read_bytes():raise ValueError('Portrait still contains EXIF metadata')
    for path in dist.rglob('*.svg'):
        if '<script' in path.read_text().lower():raise ValueError('Unexpected script in SVG: '+path.name)
    print(f'Validated 9 content files, {len(pages)} HTML pages, {references} local references, image descriptions, and palette contrast.')
    print('Contrast: '+', '.join(f'{label} {contrast(a,b):.2f}:1' for label,a,b in pairs))

if __name__=='__main__':validate()
