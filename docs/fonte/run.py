from gen import *
names = {"PE":"figura-09-modulo-produtos-estoque","CF":"figura-10-modulo-compras-fornecedores",
         "VC":"figura-11-modulo-vendas-caixa","FF":"figura-12-modulo-financeiro-fiado",
         "PA":"figura-13-modulo-pessoas-acesso"}
for mk,fn in names.items():
    full,ctx,rels = module(mk)
    build(fn, full, ctx, rels, rankdir="LR" if mk=="PA" else "TB")
build("figura-08-der-visao-geral", list(E), rels=R, mode="name", dpi=150)
build("der-completo-atributos", list(E), rels=R, mode="full", dpi=150, legend=True)
build("figura-14-der-visao-geral-a3", list(E), rels=R, mode="name", dpi=300,
      title="DER completo, visão geral — Supermercado Parque Boturussu (21 entidades, 36 relacionamentos)",
      extra='size="16.54,11.69" ratio=compress')
from PIL import Image
p=f"{OUT}/figura-14-der-visao-geral-a3.png"; im=Image.open(p).convert("RGB")
W,H=4961,3508; s=min((W-160)/im.width,(H-160)/im.height)
if s<1: im=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
c=Image.new("RGB",(W,H),"white"); c.paste(im,((W-im.width)//2,(H-im.height)//2)); c.save(p,dpi=(300,300))
print(im.size)
