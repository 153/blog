#!/usr/bin/env python3
import os
import time
import datetime
from markdown_it import MarkdownIt

# Configuration

in_dir = "./pages/"
out_dir = "./html/"
templ_dir = "./templ/"
tform = "%Y-%m-%d [%a] %H:%M UTC"
atomt = "%Y-%m-%dT%H:%M:%SZ"
root = "/blog/"
url = "https://4x13.net/blog/"
atomfile = "index.atom"

markdown = MarkdownIt()

notedb = {}
tagdb = {}
datedb = []

yeardb = {}
monthdb = {}

templates = {}

for temp in ["article", "foot", "head"]:
    with open(f"{templ_dir}{temp}.html") as html:
        html = html.read()
        templates[temp] = html

for temp in ["feed", "entry"]:
    with open(f"{templ_dir}{temp}.atom") as atom:
        atom = atom.read()
        templates[temp] = atom

# Perform initial scraping

notes = os.listdir(in_dir)
for note in notes:
    if note[-3:] != "txt":
        continue
    
    fn = in_dir + note
    note = note[:-4]
    with open(fn, "r") as data:
        data = data.read().strip().splitlines()

    notedb[note] = {"title":data[0],
                    "date":data[1],
                    "epoch":data[1],
                    "tags":data[2],
                    "post":"\n".join(data[3:])}

    # convert epoch to python
    pubtime = time.gmtime(int(data[1]))

    # make python human readable
    notedb[note]["date"] = time.strftime(tform, pubtime)

    # make article name ymd hs title for sorting/indexing
    dlist = []
    for i in range(5):
        dlist.append(str(pubtime[i]).zfill(2))
    dlist.append(note)
    datedb.append(dlist)

    # extract note tags
    if " " in data[2]:
        data[2] = data[2].split(" ")
    else:
        data[2] = [data[2]]

    # store notes by tag in tag db
    for tag in data[2]:
        if tag in tagdb:
            tagdb[tag].append(dlist)
        else:
            tagdb[tag] = [dlist]

# sort indices
datedb.sort()
for tag in tagdb:
    tagdb[tag].sort()
for note in datedb:
    if note[0] in yeardb:
        yeardb[note[0]].append(note)
    else:
        yeardb[note[0]] = [note]
    if note[0] in monthdb:
        if note[1] in monthdb[note[0]]:
            monthdb[note[0]][note[1]].append(note)
        else:
            monthdb[note[0]][note[1]] = [note]
    else:
        monthdb[note[0]] = {note[1]: [note]}

def make_article(notefn, full=False):
    note = notedb[notefn].copy()
    if " " in note["tags"]:
        tags = note["tags"].split(" ")
    else:
        tags = [note["tags"]]
    tags = [f"<a href='{root}tags/{i}/'>#{i}</a>" for i in tags]
    tags = " ".join(tags)

    if "<SPLIT>" in note["post"]:
        if full == False:
            note["post"] = note["post"].split("<SPLIT>")[0]
            note["post"] += f"\n\n [Continue reading...]({root}{notefn}.html)"
        else:
            note["post"] = note["post"].replace("<SPLIT>", "")
            
    post = markdown.render(note["post"])

    title = f"<a href='{root}{notefn}.html'>{note['title']}</a>"
        
    article = templates["article"]
    article = article.replace("$TITLE", title)\
                   .replace("$DATE", note["date"])\
                   .replace("$TAGS", tags)\
                   .replace("$BODY", post)
    return article

def write_article(notefn):
    article = make_article(notefn, True)
    article = "\n".join([templates["head"], article, templates["foot"]])
    with open(f"{out_dir}{notefn}.html", "w", encoding="utf-8") as out:
        out.write(article)

def make_index(prefix, entries):
    counter = 0
    pcnt = 0
    pages = {}
    for article in entries:
        counter += 1
        p = str(pcnt).zfill(2)
        if p not in pages:
            pages[p] = []
        pages[p].append(make_article(article[-1]))
    for p in pages:
        pages[p].reverse()
        output = "\n".join([templates["head"], *pages[p], templates["foot"]])
        with open(f"{out_dir}{prefix}/{p}.html", "w", encoding="utf-8") as out:
            out.write(output)
        if p == "00":
            with open(f"{out_dir}{prefix}/index.html", "w", encoding="utf-8") as out:
                out.write(output)

def make_pages_all():
    for page in datedb:
        write_article(page[-1])
    
def make_index_all():
    make_index("", datedb)
    
def make_index_year(year):
    if not os.path.isdir(f"{out_dir}{year}/"):
        os.mkdir(f"{out_dir}{year}/")
    articles = yeardb[year]
    make_index(year, articles)

def make_index_month(year, month):
    if not os.path.isdir(f"{out_dir}{year}/{month}/"):
        os.mkdir(f"{out_dir}{year}/{month}/")
    articles = monthdb[year][month]
    make_index(f"{year}/{month}", articles)

def make_index_tag(tag):
    if not os.path.isdir(f"{out_dir}tags"):
        os.mkdir(f"{out_dir}tags")
    if not os.path.isdir(f"{out_dir}tags/{tag}"):
        os.mkdir(f"{out_dir}tags/{tag}")
    make_index(f"tags/{tag}", tagdb[tag])

def make_archive():
    if not os.path.isdir(f"{out_dir}archive"):
        os.mkdir(f"{out_dir}archive")
    index = ["<article><ul>"]
    for year in sorted(yeardb):
        index.append(f"<li><a href='{root}{year}/'>{year}</a>"
                     f" - {len(yeardb[year])} articles")
        index.append("<ul>")
        for month in sorted(monthdb[year]):
            index.append(f"<li><a href='{root}{year}/{month}/'>{year}-{month}</a>"
                         f" - {len(monthdb[year][month])} articles")
        index.append("</ul>")
    index.append("</ul></article>")
    index = "\n".join(index)
    with open(f"{out_dir}archive/index.html", "w", encoding="utf-8") as archive:
        archive.write(templates["head"] + index + templates["foot"])

def make_tags():
    index = ["<article><ul>"]
    tags = [[tag, len(tagdb[tag])] for tag in tagdb]
    tags.sort(key=lambda x: x[1], reverse=True)
    for tag in tags:
        index.append(f"<li><a href='{root}tags/{tag[0]}/'>{tag[0]}</a>"
                     f" - {tag[1]} articles")
    index.append("</ul></article>")
    index = "\n".join(index)
    with open(f"{out_dir}tags/index.html", "w", encoding="utf-8") as tagpage:
        tagpage.write(templates["head"] + index + templates["foot"])

def make_feed():
    articles = datedb[::-1]
    updated = notedb[articles[0][-1]]["epoch"]
    updated = time.gmtime(int(updated))
    updated = time.strftime(atomt, updated)
                          
    feed = templates["feed"].replace("UPDATED", updated)
    feed = feed.replace("URL", url).replace("ATOMFILE", url+atomfile)
    output = [feed]
    for article in articles:
        data = notedb[article[-1]]
        title = data["title"]
        link = url + article[-1] + ".html"
        updated = data["epoch"]
        updated = time.gmtime(int(updated))
        updated = time.strftime(atomt, updated)
        if "<SPLIT>" in data["post"]:
            data["post"] = data["post"].replace("<SPLIT>", "")
        content = markdown.render(data["post"])
        content = content.replace("&", "&amp;")\
            .replace("<", "&lt;")\
            .replace(">", "&gt;")
        result = templates["entry"].replace("TITLE", title)\
            .replace("LINK", link)\
            .replace("TIME", updated)\
            .replace("CONTENT", content)
        output.append(result)
    output.append("</feed>")
    output = "\n".join(output)
    with open(f"{out_dir}index.atom", "w", encoding="utf-8") as out:
        out.write(output)

make_pages_all()
make_index_all()
for year in yeardb:
    make_index_year(year)
    for month in monthdb[year]:
        make_index_month(year, month)

make_archive()

for tag in tagdb:
    make_index_tag(tag)
make_tags()

make_feed()
