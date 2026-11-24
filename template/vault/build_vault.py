#!/usr/bin/env python3
"""票券夾 PDF 產生器：python3 build_vault.py vault.json 票券夾.pdf
需要：pillow、pypdf、playwright(chromium)、Noto Sans CJK TC 字型。
第一頁＝標題＋目錄（點項目跳到票／QR）；每頁右上「↑ 目錄」回第一頁；有書籤。
圖片 type：qr（QR/條碼，小圖會像素放大）、ticket（整張票面）、shot（訂位截圖）。
"""
import sys,json,base64,io,html,os
from datetime import datetime
from PIL import Image
from pypdf import PdfReader,PdfWriter,Transformation
from pypdf.annotations import Link
from playwright.sync_api import sync_playwright

WD='一二三四五六日'; e=html.escape
def dh(d):
    t=datetime.fromisoformat(d); return f"{t.month}/{t.day}（{WD[t.weekday()]}）"
CSS="""@page{size:390px 844px;margin:0}*{box-sizing:border-box}html,body{margin:0;padding:0}
body{width:390px;font-family:'Noto Sans CJK TC','Noto Sans TC',sans-serif;color:#3E3A39;font-size:14px;line-height:1.5;background:#FFFCF6;-webkit-print-color-adjust:exact;print-color-adjust:exact}
a{color:#3E3A39;text-decoration:none}
.toc{height:844px;padding:14px 18px;break-after:page}
.toc h1{font-size:22px;margin:0;line-height:1.3}.toc .sub{font-size:12px;color:#5E5856;margin:0 0 6px}
.td{font-size:13px;margin:8px 0 2px;display:inline-block;background:#D6CAF2;border:2px solid #3E3A39;border-radius:999px;padding:0 12px}
.tl{display:flex;gap:8px;font-size:13px;padding:3px 0;border-bottom:1px dotted #bbb;align-items:baseline}
.tl i{font-style:normal;flex:none;width:42px;color:#5E5856}.tl span{flex:1}
.tl em{font-style:normal;flex:none;font-size:11px;border:1.5px solid #3E3A39;border-radius:999px;padding:0 6px;background:#F2A497}
.img{break-before:page;height:844px;background:#fff;padding:14px 12px;display:flex;flex-direction:column;align-items:center}
.img .cap{width:100%;font-size:13px;line-height:1.35;margin-bottom:8px;padding-right:70px}
.img .cap small{color:#5E5856;display:block;font-size:11px}
.img img{max-width:100%;max-height:740px;object-fit:contain}
.img img.px{width:330px;image-rendering:pixelated}
.img img.shot{max-width:100%;max-height:770px;width:auto}"""
def b64(path,fmt=None):
    im=Image.open(path)
    if fmt=='JPEG' or im.mode in('RGBA','P') and fmt is None:
        pass
    buf=io.BytesIO()
    if path.lower().endswith(('.jpg','.jpeg')): im.convert('RGB').save(buf,'JPEG',quality=80);mt='jpeg'
    else: im.save(buf,'PNG');mt='png'
    return f"data:image/{mt};base64,"+base64.b64encode(buf.getvalue()).decode(),im.size
def pages_for(entry,base):
    out=[]
    for m in entry['images']:
        p=os.path.join(base,m['path']);typ=m.get('type','shot')
        uri,(w,h)=b64(p)
        if typ=='shot' and h>w*2.3:      # 超長截圖切段
            im=Image.open(p).convert('RGB');seg=int(w*2.1);n=-(-h//seg);step=-(-h//n)
            for k in range(n):
                buf=io.BytesIO();im.crop((0,k*step,w,min(h,(k+1)*step))).save(buf,'JPEG',quality=78)
                out.append(('shot',"data:image/jpeg;base64,"+base64.b64encode(buf.getvalue()).decode()))
        else:
            cls='qr' if typ=='qr' else typ
            if typ=='qr' and w<=200: cls='qrpx'
            out.append((cls,uri))
    out.sort(key=lambda t:0 if t[0] in('qr','qrpx','ticket') else 1)   # QR/票面排最前
    return out
def main(cfg_path,out_pdf):
    cfg=json.load(open(cfg_path,encoding='utf-8'));base=os.path.dirname(os.path.abspath(cfg_path))
    E=sorted([x for x in cfg['entries'] if x.get('images')],key=lambda x:(x['date'],x['time']))
    cities=cfg.get('dates',{})
    h=['<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><style>'+CSS+'</style></head><body>']
    t=[f'<div class="toc"><h1>{e(cfg["title"])}</h1><p class="sub">{e(cfg.get("subtitle",""))}</p>'];last=''
    for i,x in enumerate(E):
        if x['date']!=last: last=x['date'];t.append(f'<div class="td">{dh(x["date"])} {e(cities.get(x["date"],""))}</div><br>')
        q=any(m.get('type')in('qr','ticket') for m in x['images'])
        t.append(f'<a class="tl" href="#e{i}"><i>{x["time"]}</i><span>{e(x["title"])}</span>'+('<em>QR</em>' if q else '')+'</a>')
    t.append('</div>');h.append(''.join(t))
    for i,x in enumerate(E):
        first=True
        for cls,uri in pages_for(x,base):
            idh=f' id="e{i}"' if first else '';first=False
            c={'qrpx':'px','qr':'','ticket':'','shot':'shot'}[cls]
            h.append(f'<div class="img"{idh}><div class="cap"><b>{e(x["title"])}</b><small>{dh(x["date"])} {x["time"]}</small></div><img class="{c}" src="{uri}"></div>')
    h.append('</body></html>')
    raw=out_pdf+'.raw.pdf';back=out_pdf+'.back.pdf'
    with sync_playwright() as pw:
        b=pw.chromium.launch();p=b.new_page()
        p.set_content(''.join(h));p.pdf(path=raw,width='390px',height='844px',print_background=True)
        p.set_content('<style>@page{size:390px 844px;margin:0}html,body{margin:0;width:390px;height:844px;background:transparent}*{font-family:"Noto Sans CJK TC",sans-serif}</style><div style="position:absolute;right:10px;top:8px;font-size:12px;line-height:1;padding:5px 11px;border:2px solid #3E3A39;border-radius:999px;background:#D6CAF2;color:#3E3A39">↑ 目錄</div>')
        p.pdf(path=back,width='390px',height='844px',print_background=True,page_ranges='1');b.close()
    r=PdfReader(raw);nd=r.named_destinations
    tocs=[]
    for a in r.pages[0].get('/Annots',[]):
        a=a.get_object();d=a.get('/Dest') or (a.get('/A') or {}).get('/D')
        if d is not None: tocs.append((list(map(float,a['/Rect'])),int(str(d).lstrip('/')[1:]),r.get_destination_page_number(nd[str(d)])))
    w=PdfWriter();ov=PdfReader(back).pages[0]
    for pg in r.pages:
        if '/Annots' in pg: del pg['/Annots']
        w.add_page(pg)
    W,H=float(w.pages[0].mediabox.width),float(w.pages[0].mediabox.height)
    for i,pg in enumerate(w.pages):
        if i>0:
            pg.merge_transformed_page(ov,Transformation().scale(W/float(ov.mediabox.width),H/float(ov.mediabox.height)))
            w.add_annotation(i,Link(rect=(W-72,H-30,W-4,H-4),target_page_index=0))
    w.add_outline_item('目錄',0)
    for rect,i,pn in tocs:
        w.add_annotation(0,Link(rect=rect,target_page_index=pn));w.add_outline_item(E[i]['title'],pn)
    w.write(out_pdf);os.remove(raw);os.remove(back)
    print(out_pdf,len(w.pages),'頁，目錄',len(tocs),'項')
if __name__=='__main__': main(sys.argv[1],sys.argv[2])
