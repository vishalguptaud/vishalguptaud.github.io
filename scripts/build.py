"""Dependency-free static site builder. Only dist/ is published.

Content is plain JSON, edited by the CMS or the included browser editor.
All user text is HTML-escaped. No credentials belong in this project.
"""
from pathlib import Path
from html import escape
from urllib.parse import urlparse
import json
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
PAGES=[('index.html','Home'),('research.html','Research'),('teaching.html','Teaching'),
       ('mentoring.html','Mentoring'),('data-science.html','Data Science'),
       ('talks.html','Talks'),('photos.html','Photos')]

def load(name): return json.loads((ROOT/'content'/f'{name}.json').read_text())
def e(value): return escape(str(value), quote=True)
def safe_url(value):
    value=str(value).strip()
    if not value: return ''
    if urlparse(value).scheme not in ('','https','http','mailto'): raise ValueError('Unsafe URL scheme')
    if value.startswith('//') or '\\' in value: raise ValueError('Unsafe URL')
    return e(value)
def link(label,url,cls=''):
    if not url: return ''
    ext=' target="_blank" rel="noopener noreferrer"' if urlparse(url).scheme in ('http','https') else ''
    return f'<a href="{safe_url(url)}"'+(f' class="{e(cls)}"' if cls else '')+f'{ext}>{e(label)}</a>'
def paragraphs(values,cls=''):
    return ''.join(f'<p'+(f' class="{e(cls)}"' if cls else '')+f'>{e(p).replace("ℤ_N","ℤ<sub>N</sub>")}</p>' for p in values if p)
def links(values,cls='link-list'):
    return f'<ul class="{e(cls)}">'+''.join('<li>'+link(x['label'],x['url'])+'</li>' for x in values if x.get('url'))+'</ul>'
def figure(images,caption='',cls=''):
    if not images: return ''
    pics=''
    for img in images:
        dimensions=''
        path=ROOT/'static'/img['image']
        if path.suffix=='.svg' and path.is_file():
            box=re.search(r'viewBox="[0-9. -]+ ([0-9.]+) ([0-9.]+)"',path.read_text())
            if box: dimensions=f' width="{box.group(1)}" height="{box.group(2)}"'
        pics+=f'<a class="figure-zoom" href="{safe_url(img["image"])}" target="_blank" rel="noopener" aria-label="Enlarge figure: {e(img["alt"])}"><img src="{safe_url(img["image"])}" alt="{e(img["alt"])}"{dimensions} loading="lazy"></a>'
    return f'<figure class="math-figure {e(cls)}"><div class="figure-panels">{pics}</div>'+(f'<figcaption>{e(caption)}</figcaption>' if caption else '')+'</figure>'

def intro(kicker,title,text=''):
    return f'<header class="page-heading"><p class="eyebrow">{e(kicker)}</p><h1>{e(title)}</h1>'+(f'<p class="lead">{e(text)}</p>' if text else '')+'</header>'

def shell(filename,title,description,body,settings):
    nav=''.join(f'<a href="{path}"'+(' aria-current="page"' if path==filename else '')+f'>{label}</a>' for path,label in PAGES)
    canonical=''
    if settings['base_url']:
        canonical=f'<link rel="canonical" href="{safe_url(settings["base_url"].rstrip("/")+"/"+("" if filename=="index.html" else filename))}">'
    robots='index,follow' if settings['allow_indexing'] else 'noindex,nofollow'
    social=[link('GitHub',settings.get('github_url','')),link('Google Scholar',settings.get('scholar_url','')),link('LinkedIn',settings.get('linkedin_url',''))]
    social=' · '.join(s for s in social if s)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | {e(settings['name'])}</title><meta name="description" content="{e(description)}">
<meta name="robots" content="{robots}"><meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' https: data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-src 'none'; form-action 'none'">
{canonical}<link rel="icon" type="image/svg+xml" href="assets/favicon.svg"><link rel="stylesheet" href="assets/site.css"><link rel="stylesheet" href="assets/theme.css"></head>
<body><a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap header-inner"><a class="brand" href="index.html">{e(settings['name'])}</a><nav aria-label="Main navigation">{nav}</nav></div></header>
<main id="main" class="wrap">{body}</main>
<footer class="site-footer"><div class="wrap footer-inner"><p>{e(settings['department'])} · {e(settings['institution'])}<br>{e(settings['office'])}</p><div>{link(settings['email'],'mailto:'+settings['email'])}<br>{social}</div><p><a href="privacy.html">Privacy</a></p></div></footer></body></html>'''

def home(settings):
    d=load('home')
    actions=link('Research','research.html','button')+link('CV',settings['cv_url'],'text-action')+link('GitHub',settings['github_url'],'text-action')
    biography=e(d['biography'])
    for advisor in d['advisor_links']:
        biography=biography.replace(e(advisor['label']),link(advisor['label'],advisor['url']),1)
    edu=''.join(f'<li><h3>{e(x["degree"])}</h3><p>{e(x["institution"])} · {e(x["dates"])}</p>'+(f'<p class="secondary">{e(x["details"])}</p>' if x['details'] else '')+'</li>' for x in d['education'])
    highlights=''.join(f'<article><p class="eyebrow">{e(x["label"])}</p><h3>{e(x["title"])}</h3><p>{e(x["text"])}</p>{link(x["link_label"]+" →",x["page"])}</article>' for x in d['highlights'])
    return f'''<section class="home-hero"><div><p class="eyebrow">Mathematics · {e(settings['institution'])}</p><h1>{e(settings['name'])}</h1><p class="role">{e(settings['role'])}</p><p class="lead">{e(d['intro'])}</p><p class="bio">{biography}</p><div class="actions">{actions}</div></div>
<figure class="portrait"><img src="{safe_url(settings['portrait'])}" alt="{e(settings['portrait_alt'])}" width="900" height="900" fetchpriority="high"></figure></section>
<section class="home-research ruled"><div><p class="eyebrow">A look at the mathematics</p><h2>{e(d['research_title'])}</h2><p>{e(d['research_intro'])}</p>{link('Research projects →','research.html')}</div>{figure([{'image':'assets/spectral-comparison.svg','alt':'Two graphs of order six and size six with spectral radii two and one plus square root of two.'}])}</section>
<section class="ruled"><h2>Projects and student research</h2><div class="highlights">{highlights}</div></section>
<section class="ruled"><h2>Education</h2><ul class="education">{edu}</ul></section>'''

def research():
    d=load('research'); pub=load('publications')
    body=intro('Research','Research',d['intro'])
    body+='<nav aria-label="Research projects"><ul class="jump-links">'+''.join('<li>'+link(x['title'],'#'+x['id'])+'</li>' for x in d['projects'])+'</ul></nav>'
    for project in d['projects']:
        highlight=''
        if project['highlight']:
            highlight='<aside class="theorem">'+paragraphs([project['highlight']])+paragraphs([project['highlight_credit']],'secondary')+'</aside>'
        wide=' project-wide' if len(project['figures'])!=1 else ''
        body+=f'<section class="project{wide}" id="{e(project["id"])}"><div><h2>{e(project["title"])}</h2>{paragraphs(project["paragraphs"])}{highlight}{links(project["links"])}</div>{figure(project["figures"],project["caption"])}</section>'
    body+='<section class="ruled"><h2>Related work</h2>'+paragraphs([d['related_text']])+links(d['related_links'])+'</section>'
    body+='<section class="ruled" id="publications"><h2>Publications and preprints</h2><ol class="publication-list">'
    for p in pub['items']:
        status=p['status']+(f' ({p["year"]})' if str(p['year']) not in p['status'] else '')
        meta=('With '+p['coauthors']+'. ' if p['coauthors'] else '')+status+'.'
        abstract='<details><summary>Abstract</summary>'+paragraphs([p['abstract']])+'</details>' if p['abstract'] else ''
        code=link('Code',p['code_url']) if p['code_url'] else ''
        body+='<li><h3>'+link(p['title'],p['url'])+'</h3><p class="secondary">'+e(meta)+'</p>'+code+abstract+'</li>'
    body+='</ol></section>'
    if pub['in_preparation']:
        body+='<section class="ruled"><h2>In preparation</h2><ul class="plain-records">'+''.join('<li><h3>'+e(p['title'])+'</h3><p class="secondary">With '+e(p['coauthors'])+'.</p></li>' for p in pub['in_preparation'])+'</ul></section>'
    return body

def teaching():
    d=load('teaching'); body=intro('Teaching','Teaching',d['intro'])
    body+='<aside class="notice"><h2>'+e(d['office_hours_title'])+'</h2><p>Office hours: '+e(d['office_hours'])+'</p></aside>'
    groups=[('University of Rochester','Instructor'),('University of Delaware','Instructor'),('University of Delaware','Teaching Assistant')]
    for inst,role in groups:
        items=[c for c in d['courses'] if c['institution']==inst and c['role']==role]
        if not items: continue
        body+='<section class="record-group"><h2>'+e(role)+' · '+e(inst)+'</h2><ul class="course-list">'
        for c in items:
            status=' · '+c['status'] if c['status']!='Past' else ''
            name=e(c['code']+' · '+c['title'])
            if c['url']: name=link(c['code']+' · '+c['title'],c['url'])
            body+='<li><div class="record-date">'+e(c['term'])+'</div><div><h3>'+name+'</h3><p class="secondary">'+e(c['role']+status)+'</p>'+paragraphs([c['details']],'secondary')+'</div></li>'
        body+='</ul></section>'
    # Additional institutions/roles added later must not silently disappear.
    extras=[c for c in d['courses'] if (c['institution'],c['role']) not in groups]
    if extras:
        body+='<section class="record-group"><h2>Additional teaching</h2><ul class="course-list">'
        for c in extras:
            body+='<li><div class="record-date">'+e(c['term'])+'</div><div><h3>'+e(c['code']+' · '+c['title'])+'</h3>'+paragraphs([c['institution'],c['role'],c['details']],'secondary')+link('Course materials',c['url'])+'</div></li>'
        body+='</ul></section>'
    body+='<section class="record-group"><h2>Review sessions</h2><ul class="course-list">'
    for c in d['other_teaching']:
        body+='<li><div class="record-date">'+e(c['term'])+'</div><div><h3>'+e(c['title'])+'</h3>'+paragraphs([c['institution'],c['details']],'secondary')+'</div></li>'
    body+='</ul></section><div class="actions">'+link('Course evaluations',d['evaluations_url'],'button')+'</div>'
    return body

def mentoring():
    d=load('mentoring'); body=intro('Student research','Research and mentoring',d['intro'])
    for p in d['projects']:
        body+='<section class="text-project ruled"><h2>'+e(p['title'])+'</h2>'+paragraphs(p['paragraphs'])+paragraphs([p['collaborators']],'secondary')+links(p['links'])+'</section>'
    body+='<aside class="notice"><h2>Information for students</h2>'+paragraphs([d['student_information']])+links(d['program_links'])+'</aside>'
    return body

def data_science():
    d=load('data-science'); body=intro('Data science','Data science',d['intro'])
    for p in d['projects']:
        facts=''.join('<div><dt>'+e(f['label'])+'</dt><dd>'+e(f['text'])+'</dd></div>' for f in p['facts'])
        certificate=link('Erdős Institute certificate',p['certificate_url'])
        body+='<section class="data-project"><div><p class="award">'+e(p['award'])+'</p><h2>'+e(p['title'])+'</h2>'+paragraphs(p['paragraphs'])+paragraphs(['With '+p['collaborators']+'. '+p['date']+'.'],'secondary')+links(p['links'],'inline-links')+certificate+'</div><aside class="facts"><h3>The project</h3><dl>'+facts+'</dl></aside></section>'
        if p['figure']: body+=figure([{'image':p['figure'],'alt':p['figure_alt']}],p['figure_caption'])
    body+='<section class="ruled"><h2>Research with students</h2><p>I also co-supervise the StemForAll Sales Modeling project, which studies sales forecasting and inventory problems.</p>'+link('Project and mentoring →','mentoring.html')+'</section>'
    return body

def talks():
    d=load('talks'); body=intro('Talks','Talks and lectures',d['intro'])
    groups=list(dict.fromkeys(t['group'] for t in d['items']))
    years=sorted([g for g in groups if g.isdigit()],key=int,reverse=True)
    groups=years+[g for g in groups if not g.isdigit()]
    for group in groups:
        body+='<section class="record-group"><h2>'+e(group)+'</h2><div class="talk-list">'
        for t in d['items']:
            if t['group']!=group: continue
            title=t['title'] or t['event']
            event=paragraphs([t['event']],'secondary') if t['title'] else ''
            resources=[{'label':t['event_link_label'] or 'Event website','url':t['event_url']},
                       {'label':'Slides','url':t['slides_url']},{'label':'Recording','url':t['video_url']}]
            abstract='<details><summary>Abstract</summary>'+paragraphs([t['abstract']])+'</details>' if t['abstract'] else ''
            body+='<article class="talk"><p class="record-date">'+e(t['date'])+'</p><div><h3>'+e(title)+'</h3>'+event+paragraphs([t['location']])+links(resources,'inline-links')+abstract+'</div></article>'
        body+='</div></section>'
    return body

def photos():
    d=load('photos'); body=intro('Conferences, workshops, and summer schools','Photographs',d['intro'])
    if not d['albums']: return body+'<p class="empty-note">'+e(d['empty_text'])+'</p>'
    for a in d['albums']:
        body+='<section class="ruled"><h2>'+e(a['title'])+'</h2>'+paragraphs([a['location']+' · '+a['year']],'secondary')+paragraphs([a['description']])+'<div class="photo-grid">'
        for image in a['images']:
            body+='<figure>'+link('', '')+f'<a href="{safe_url(image["image"])}" target="_blank" rel="noopener"><img src="{safe_url(image["image"])}" alt="{e(image["alt"])}" loading="lazy"></a><figcaption>{e(image["caption"])}</figcaption></figure>'
        body+='</div></section>'
    return body

def privacy():
    return intro('About this website','Privacy')+'''<div class="reading-width"><p>This website does not add analytics, advertising, social-media widgets, externally hosted fonts, or visitor accounts. The hosting provider may process connection information, including IP addresses, under its own policies.</p><p>Following a link to another website, including Google Drive, GitHub, or a video platform, takes you to that service and its privacy practices. Links to restricted Drive files do not grant access to those files.</p><p>Anything displayed publicly here, including photographs and documents, may be downloaded or copied. Private originals, confidential research, and student records should not be published here.</p><p>The editing tools are separate from the visitor pages. The browser-based local editor downloads files; it cannot publish changes to the live website. Authorized publishing through the connected CMS requires repository permissions.</p></div>'''

def theme(settings):
    colors={k:settings[k] for k in ('primary_color','accent_color','background_color')}
    for value in colors.values():
        if not re.fullmatch(r'#[0-9a-fA-F]{6}',value): raise ValueError('Colors must be six-digit hex values')
    allowed={'Georgia':"Georgia, 'Times New Roman', serif",'Arial':"Arial, Helvetica, sans-serif",'Verdana':"Verdana, Arial, sans-serif",'Times New Roman':"'Times New Roman', Georgia, serif"}
    return ':root {\n'+f'  --pine: {colors["primary_color"]};\n  --clay: {colors["accent_color"]};\n  --cream: {colors["background_color"]};\n  --heading-font: {allowed[settings["heading_font"]]};\n  --body-font: {allowed[settings["body_font"]]};\n'+'}\n'

def build():
    settings=load('settings')
    DIST.mkdir(exist_ok=True)
    shutil.copytree(ROOT/'static',DIST,dirs_exist_ok=True)
    (DIST/'assets/theme.css').write_text(theme(settings))
    # Figures share the site's three principal colors. Rebuild from originals
    # so repeated palette changes do not accumulate substitutions.
    for svg_path in (DIST/'assets').glob('*.svg'):
        original=(ROOT/'static/assets'/svg_path.name).read_text()
        replacements={'#1f4d3a':settings['primary_color'],
                      '#a64b2a':settings['accent_color'],
                      '#faf5eb':settings['background_color']}
        original=re.sub(r'#[0-9a-fA-F]{6}',lambda m:replacements.get(m.group(0).lower(),m.group(0)),original)
        svg_path.write_text(original)
    renderers=[home,research,teaching,mentoring,data_science,talks,photos]
    for (filename,label),renderer in zip(PAGES,renderers):
        body=renderer(settings) if renderer is home else renderer()
        description=settings['name']+' — '+label+'. Mathematics, research, teaching, and student projects.'
        (DIST/filename).write_text(shell(filename,label,description,body,settings))
    (DIST/'privacy.html').write_text(shell('privacy.html','Privacy','Privacy information for this website.',privacy(),settings))
    (DIST/'404.html').write_text(shell('404.html','Page not found','Page not found.',intro('404','Page not found')+'<p>The page may have moved.</p><p><a href="index.html">Return to the homepage →</a></p>',settings))
    (DIST/'robots.txt').write_text('User-agent: *\n'+('Allow: /\nDisallow: /admin/\nDisallow: /edit/\n' if settings['allow_indexing'] else 'Disallow: /\n'))
    (DIST/'.nojekyll').touch()
    data={p.stem:json.loads(p.read_text()) for p in sorted((ROOT/'content').glob('*.json'))}
    (DIST/'edit').mkdir(exist_ok=True)
    (DIST/'edit/content.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    from cms_schema import configuration, editor_schema
    (DIST/'edit/schema.json').write_text(json.dumps(editor_schema(),ensure_ascii=False,indent=2)+'\n')
    (DIST/'admin/settings.json').write_text(json.dumps(configuration(settings),ensure_ascii=False,indent=2)+'\n')
    print('Built 7 content pages, privacy page, 404 page, editing tools, and CMS configuration in dist/.')

if __name__=='__main__': build()
