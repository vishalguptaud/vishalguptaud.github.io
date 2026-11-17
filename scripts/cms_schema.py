"""One schema drives the authenticated CMS and the local file editor."""
import re

def field(name,label=None,widget='string',**kw):
    return dict(name=name,label=label or name.replace('_',' ').capitalize(),widget=widget,**kw)
def text(name,label=None): return field(name,label,'text',required=False)
def url(name,label=None,required=False): return field(name,label,required=required,hint='An https:// URL, or a relative page/asset path. Leave blank if unavailable.')
def object_list(name,label,fields,singular=None):
    return field(name,label,'list',fields=fields,label_singular=singular or label.rstrip('s'),summary='{{fields.title}}',collapsed=True,required=False)
def string_list(name,label):
    return field(name,label,'list',field=field('paragraph','Paragraph','text'),required=False)
def link_fields(): return [field('label','Link label'),url('url','Destination URL',True)]
def figure_fields(): return [field('image','Figure file','image'),field('alt','Accessible image description')]

def editor_schema():
    links=lambda name='links',label='Links': object_list(name,label,link_fields(),'Link')
    return [
      {'name':'publications','label':'Publications','fields':[
        object_list('items','Publications and preprints',[
          field('title','Paper title'),field('coauthors','Coauthors (excluding yourself)',required=False),
          field('year','Year','number',value_type='int',min=1900,max=2200),field('status','Journal / status'),
          url('url','Paper URL',True),field('topic','Research topic',required=False),
          text('abstract','Abstract (optional)'),url('code_url','Code URL')],'Publication'),
        object_list('in_preparation','In preparation',[field('title','Working title'),field('coauthors','Coauthors')],'Work') ]},
      {'name':'teaching','label':'Teaching','fields':[
        text('intro','Introduction'),field('office_hours_title','Office-hours term'),text('office_hours','Office hours'),
        object_list('courses','Courses',[
          field('code','Course code'),field('title','Course title'),field('term','Semester / term'),
          field('institution','Institution'),field('role','Role'),
          field('status','Status','select',options=['Current','Scheduled','Past']),
          text('details','Details, sections, or responsibilities'),url('url','Course / materials URL')],'Course'),
        object_list('other_teaching','Review sessions',[field('title'),field('institution'),field('term'),text('details')],'Session'),
        url('evaluations_url','Course evaluations URL')]},
      {'name':'talks','label':'Talks','fields':[
        text('intro','Introduction'),object_list('items','Talks',[
          field('group','Year or group',hint='Use a year such as 2027, or Expository talks.'),
          field('date','Date'),field('title','Mathematical talk title (if known)',required=False),
          field('event','Conference, seminar, or workshop'),field('location','Institution / location'),
          url('event_url','Event URL'),field('event_link_label','Event link label',required=False),
          url('slides_url','Slides URL'),url('video_url','Recording URL'),text('abstract','Abstract (optional)')],'Talk')]},
      {'name':'research','label':'Research projects','fields':[
        text('intro','Broad research overview'),object_list('projects','Research projects',[
          field('id','Section identifier',hint='Keep this stable so existing section links continue working.'),
          field('title','Project heading'),string_list('paragraphs','Description paragraphs'),
          text('highlight','Highlighted result (optional)'),field('highlight_credit','Result attribution',required=False),
          links(),object_list('figures','Figures',figure_fields(),'Figure'),text('caption','Figure caption')],'Project'),
        text('related_text','Related work'),links('related_links','Related-work links')]},
      {'name':'home','label':'Homepage','fields':[
        text('intro','Broad research introduction'),text('biography','Biography'),links('advisor_links','Advisor links'),
        field('research_title','Research section heading'),text('research_intro','Research section text'),
        object_list('education','Education',[field('degree'),field('institution'),field('dates'),text('details')],'Degree'),
        object_list('highlights','Highlights',[field('title'),field('label','Date / program'),text('text','Description'),
                     url('page','Destination page',True),field('link_label','Link label')],'Highlight')]},
      {'name':'mentoring','label':'Mentoring','fields':[
        text('intro','Introduction'),object_list('projects','Student projects',[
          field('title'),string_list('paragraphs','Description paragraphs'),text('collaborators','Collaborators / students'),links()],'Project'),
        text('student_information','Information for prospective students'),links('program_links','Program links')]},
      {'name':'data-science','label':'Data science','fields':[
        text('intro','Introduction'),object_list('projects','Data-science projects',[
          field('title'),field('award','Recognition',required=False),field('date'),field('collaborators'),
          string_list('paragraphs','Description paragraphs'),
          object_list('facts','Project facts',[field('label'),field('text','Value')],'Fact'),links(),
          url('certificate_url','Certificate URL'),field('figure','Project figure','image',required=False),
          field('figure_alt','Figure description',required=False),text('figure_caption','Figure caption')],'Project')]},
      {'name':'photos','label':'Photographs','fields':[
        text('intro','Introduction'),text('empty_text','Text before any albums are added'),
        object_list('albums','Albums',[
          field('title','Event / album title'),field('location'),field('year'),text('description'),
          object_list('images','Photographs',[field('image','Photograph','image'),field('alt','Accessible description'),text('caption')],'Photograph')],'Album')]},
      {'name':'settings','label':'Profile and appearance','fields':[
        field('name'),field('role'),field('department'),field('institution'),field('email'),
        field('secondary_email','Alternative email',required=False),field('office'),url('cv_url','Google Drive CV URL',True),
        url('github_url','GitHub profile URL'),url('linkedin_url','LinkedIn URL'),url('scholar_url','Google Scholar URL'),
        url('base_url','Website base URL (after migration)'),
        field('allow_indexing','Allow search-engine indexing','boolean',hint='This is not access control. The current review remains owner-private through hosting.'),
        field('portrait','Portrait','image'),field('portrait_alt','Portrait description'),
        field('primary_color','Pine / primary color','color',enableAlpha=False),
        field('accent_color','Clay / accent color','color',enableAlpha=False),
        field('background_color','Page background','color',enableAlpha=False),
        field('heading_font','Heading font','select',options=['Georgia','Times New Roman','Arial','Verdana']),
        field('body_font','Body font','select',options=['Arial','Verdana','Georgia','Times New Roman']),
        field('cms_enabled','Advanced: enable authenticated CMS','boolean',hint='Only enable after repository and OAuth setup are complete.'),
        field('cms_repository','Advanced: GitHub owner/repository',required=False),
        url('cms_auth_url','Advanced: OAuth authentication service URL'),
        field('cms_branch','Advanced: content branch') ]},
    ]

def configuration(settings):
    enabled=settings['cms_enabled']
    if enabled:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',settings['cms_repository']):
            raise ValueError('CMS activation needs a real owner/repository, not a placeholder.')
        if not settings['cms_auth_url'].startswith('https://'):
            raise ValueError('CMS activation needs an HTTPS OAuth service.')
    collections=[{'name':s['name'],'label':s['label'],'files':[
       {'name':s['name'],'label':s['label'],'file':'content/'+s['name']+'.json','fields':s['fields']}],
       'format':'json','extension':'json'} for s in editor_schema()]
    return {'enabled':enabled,'config':{
        'load_config_file':False,
        'backend':{'name':'github','repo':settings['cms_repository'],'branch':settings['cms_branch'],
                   'base_url':settings['cms_auth_url'],'auth_endpoint':'auth'},
        'media_folder':'static/assets/uploads','public_folder':'assets/uploads',
        'media_libraries':{},'collections':collections}}
