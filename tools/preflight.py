"""Check local navigation, rendered-page structure and application PDF links.

Run after tools/build_portfolio.py. This performs no deployment or model call.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import re
import json
import ast
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path, self.refs, self.ids, self.resources = path, [], set(), []
        self.headings, self.title, self.in_title = [], '', False
        self.feed(path.read_text())
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'): self.ids.add(a['id'])
        if tag == 'title': self.in_title = True
        if re.fullmatch('h[1-6]',tag): self.headings.append(tag)
        for key in ['href', 'src']:
            if a.get(key): self.refs.append((tag,key,a[key]))
        if tag in ['script','img','iframe','source'] and a.get('src'):
            self.resources.append(a['src'])
        if tag == 'link' and a.get('rel') in ['stylesheet','preload']:
            self.resources.append(a.get('href',''))
    def handle_endtag(self,tag):
        if tag == 'title': self.in_title = False
    def handle_data(self,data):
        if self.in_title: self.title += data

def main():
    # The local API template uses allowlisted service URLs, not static paths.
    # Resolve those links against the backend's literal route map; HTTP behavior
    # is exercised separately by scripts/test_web_lab.py.
    server_source=ROOT/'01_ai_review/scripts/web_lab.py'
    service_files={}
    if server_source.is_file():
        for node in ast.parse(server_source.read_text()).body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FILES' for t in node.targets):
                service_files=ast.literal_eval(node.value)
    pages = {p.resolve():Page(p) for p in ROOT.rglob('*.html')
             if 'tools' not in p.relative_to(ROOT).parts}
    checked, errors = 0, []
    for p, page in pages.items():
        if not page.title.strip(): errors.append(f'{p.name}: missing title')
        if page.headings.count('h1') != 1: errors.append(f'{p.name}: expected one h1')
        for resource in page.resources:
            if urlsplit(resource).scheme in ['http','https']:
                errors.append(f'{p.name}: external render dependency {resource}')
        for tag,key,ref in page.refs:
            u=urlsplit(ref)
            if u.scheme or u.netloc: continue
            if p.name=='web_lab.html' and p.parent.name=='01_ai_review' and u.path in service_files:
                target=p.parent/service_files[u.path][0]
            else:
                target=(ROOT/unquote(u.path).lstrip('/')) if u.path.startswith('/') else p.parent/unquote(u.path)
            if not u.path: target=p
            target=target.resolve()
            if target.is_dir(): target=target/'index.html'
            if not target.is_file(): errors.append(f'{p.relative_to(ROOT)}: missing {ref}');continue
            if u.fragment and target in pages and u.fragment not in pages[target].ids:
                errors.append(f'{p.relative_to(ROOT)}: missing anchor {ref}')
            checked += 1
    for name,web in [('Ingrid_Kao_Work_Samples.pdf',False),('Ingrid_Kao_Work_Samples_Web.pdf',True)]:
        for page in PdfReader(ROOT/name).pages:
            for annotation in page.get('/Annots',[]):
                action=annotation.get_object().get('/A')
                uri=str(action.get('/URI','')) if action else ''
                if not uri or urlsplit(uri).scheme: continue
                if not web: errors.append(f'{name}: relative-file URI {uri}')
                else:
                    target=(ROOT/uri).resolve()
                    if not target.is_file(): errors.append(f'{name}: missing {uri}')
                checked += 1
    report={'rendered_html_pages':len(pages),'local_links_checked':checked,'errors':errors,
            'scope':'Local build checks; browser and content review remain separate.'}
    print(json.dumps(report,indent=2))
    if errors: raise SystemExit(1)

if __name__ == '__main__': main()
