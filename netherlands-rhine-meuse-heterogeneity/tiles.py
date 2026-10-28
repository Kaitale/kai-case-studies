import pyproj, json, subprocess, re, numpy as np, sys
from concurrent.futures import ThreadPoolExecutor
t=pyproj.Transformer.from_crs(28992,4326,always_xy=True); tb=pyproj.Transformer.from_crs(4258,28992,always_xy=True)
def q(x0,y0,s=5000):
    lo=t.transform(x0,y0); hi=t.transform(x0+s,y0+s)
    body={"area":{"boundingBox":{"lowerCorner":{"lat":lo[1],"lon":lo[0]},"upperCorner":{"lat":hi[1],"lon":hi[0]}}}}
    r=subprocess.run(["curl","-sS","-m","180","-X","POST","-H","Content-Type: application/json","-d",json.dumps(body),"https://publiek.broservices.nl/sr/bhrg/v3/characteristics/searches"],capture_output=True,text=True)
    s_=r.stdout; out=[]
    for d in re.findall(r"<dispatchDocument>(.*?)</dispatchDocument>",s_,re.S):
        i=re.search(r"<brocom:broId>(.*?)<",d).group(1); p=re.search(r"<gml:pos>(.*?)<",d).group(1).split(); dep=re.search(r'<finalDepthBoring uom="m">(.*?)<',d); off=re.search(r'<offset uom="m">(.*?)<',d)
        X,Y=tb.transform(float(p[1]),float(p[0])); out.append((i,X,Y,float(dep.group(1)) if dep else np.nan,float(off.group(1)) if off else np.nan))
    return (x0,y0,out, "rejection" in s_[:800])
jobs=[(x,y) for x in range(115000,165000,5000) for y in range(415000,450000,5000)]
with ThreadPoolExecutor(6) as ex: res=list(ex.map(lambda a:q(*a),jobs))
allb=[]
for x0,y0,out,rej in res:
    deep=[o for o in out if o[3]==o[3] and o[4]==o[4] and (o[4]-o[3])<=-7.5]
    allb+=out
    print(x0//1000,y0//1000,len(out),"deep(base<=-7.5NAP):",len(deep),"REJ" if rej else "")
json.dump(allb,open("data/bhrg_tiles.json","w"))
