from pathlib import Path
import copy
import json
import math
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import build
from cms_schema import configuration
from validate import Page,check_fields,contrast

class SiteTests(unittest.TestCase):
    def test_home_uses_standard_navigation_only(self):
        home=(ROOT/'dist/index.html').read_text()
        self.assertIn('aria-label="Main navigation"',home)
        for filename,label in build.PAGES:
            self.assertIn(f'href="{filename}"',home)
        self.assertNotIn('Explore the site as a graph',home)
        self.assertNotIn('id="site-map"',home)
        self.assertNotIn('assets/site.js',home)

    def test_full_records(self):
        # Growth, completed projects, and real photo uploads must not break CI.
        self.assertGreater(len(build.load('publications')['items']),0)
        self.assertIsInstance(build.load('publications')['in_preparation'],list)
        self.assertGreater(len(build.load('teaching')['courses']),0)
        self.assertIsInstance(build.load('teaching')['other_teaching'],list)
        self.assertGreater(len(build.load('talks')['items']),0)
        self.assertGreater(len(build.load('research')['projects']),0)

    def test_records_really_render(self):
        research=(ROOT/'dist/research.html').read_text()
        teaching=(ROOT/'dist/teaching.html').read_text()
        talks=(ROOT/'dist/talks.html').read_text()
        for p in build.load('publications')['items']:self.assertIn(build.e(p['title']),research)
        for p in build.load('publications')['in_preparation']:self.assertIn(build.e(p['title']),research)
        for course in build.load('teaching')['courses']:self.assertIn(build.e(course['code']+' · '+course['title']),teaching)
        for talk in build.load('talks')['items']:self.assertIn(build.e(talk['event']),talks)
        self.assertEqual(talks.count('class="talk"'),len(build.load('talks')['items']))

    def test_cayley_graph(self):
        edges={tuple(sorted((i,(i+s)%10))) for i in range(10) for s in (1,2,5)}
        self.assertEqual(len(edges),25)
        self.assertTrue(all(sum(i in edge for edge in edges)==5 for i in range(10)))
        eigenvalues=sorted([2*math.cos(2*math.pi*j/10)+2*math.cos(4*math.pi*j/10)+(-1)**j for j in range(10)],reverse=True)
        self.assertAlmostEqual(eigenvalues[1],math.sqrt(5)-1)
        text=(ROOT/'dist/research.html').read_text()
        self.assertIn('λ₂ &gt; 1',text)
        self.assertIn('Up to isomorphism',text)
        self.assertIn('cayley-z10.svg',text)
        self.assertNotIn('crown-graph',text)

    def test_no_fake_assets_or_connections(self):
        settings=build.load('settings')
        self.assertEqual(configuration(settings)['enabled'],settings['cms_enabled'])
        settings.update(cms_enabled=True,cms_repository='',cms_auth_url='')
        with self.assertRaises(ValueError):configuration(settings)
        self.assertNotIn('Certificate coming soon',(ROOT/'dist/data-science.html').read_text())

    def test_escaping_and_url_safety(self):
        self.assertNotIn('<script>',build.paragraphs(['<script>alert(1)</script>']))
        with self.assertRaises(ValueError):build.link('x','javascript:alert(1)')
        with self.assertRaises(ValueError):build.link('x','//evil.example')
        with self.assertRaises(ValueError):build.link('x','data:text/html,test')

    def test_add_publication_without_editing_design(self):
        data=build.load('publications');original=copy.deepcopy(data)
        data['items'].insert(0,dict(title='TEST ONLY — new paper',coauthors='A collaborator',year=2027,status='Preprint',url='https://example.com/paper',topic='fourier',abstract='',code_url=''))
        real_load=build.load
        try:
            build.load=lambda name:data if name=='publications' else real_load(name)
            rendered=build.research()
        finally:build.load=real_load
        self.assertIn('TEST ONLY — new paper',rendered)
        self.assertEqual(build.load('publications'),original)

    def test_new_course_institution_is_not_dropped(self):
        data=build.load('teaching')
        data['courses'].append(dict(code='TEST 101',title='Test course',term='Fall 2027',institution='Test university',role='Instructor',status='Scheduled',details='',url=''))
        real_load=build.load
        try:
            build.load=lambda name:data if name=='teaching' else real_load(name)
            rendered=build.teaching()
        finally:build.load=real_load
        self.assertIn('Test university',rendered)
        self.assertIn('TEST 101',rendered)

    def test_album_rendering(self):
        data=build.load('photos')
        data['albums']=[dict(title='TEST ONLY — album',location='Test location',year='2027',description='',images=[dict(image='assets/vishal-photo.jpg',alt='Test description',caption='Test caption')])]
        real_load=build.load
        try:
            build.load=lambda name:data if name=='photos' else real_load(name)
            rendered=build.photos()
        finally:build.load=real_load
        self.assertIn('TEST ONLY — album',rendered)
        self.assertIn('Test caption',rendered)

    def test_central_appearance(self):
        settings=build.load('settings')
        self.assertIn('--pine: #1F4D3A',build.theme(settings))
        settings['primary_color']='#17324D'
        self.assertIn('--pine: #17324D',build.theme(settings))
        self.assertGreaterEqual(contrast('#1F4D3A','#FAF5EB'),4.5)

    def test_visitor_pages_have_no_trackers(self):
        for filename,_ in build.PAGES:
            page=Page((ROOT/'dist'/filename).read_text())
            self.assertFalse(any(url.startswith('https://') for url in page.refs if url.endswith('.js')))
            text=(ROOT/'dist'/filename).read_text()
            self.assertNotIn('googletagmanager',text)
            self.assertNotIn('fonts.googleapis',text)
            self.assertNotIn('<iframe',text)

if __name__=='__main__':unittest.main()
