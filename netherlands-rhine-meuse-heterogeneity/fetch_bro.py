import json, subprocess, os, re, collections
from concurrent.futures import ThreadPoolExecutor
b=json.load(open("data/bhrg_tiles.json"))
inb=[o for o in b if 122000<=o[1]<130000 and 427000<=o[2]<433000 and o[3]==o[3] and o[4]==o[4] and o[4]-o[3]<=-2.25]
def get(o):
    f=f"data/bhrg/{o[0]}.xml"
    if not os.path.exists(f) or os.path.getsize(f)<1000:
        subprocess.run(["curl","-sS","-m","90","-o",f,f"https://publiek.broservices.nl/sr/bhrg/v3/objects/{o[0]}"])
    return f
with ThreadPoolExecutor(6) as ex: files=list(ex.map(get,inb))
names=collections.Counter()
for f in files:
    s=open(f).read(); names.update(re.findall(r'<bhrgcom:soilNameNEN5104[^>]*>(.*?)<',s))
print(len(files)); print(names.most_common(60))
