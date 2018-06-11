# encoding=utf8
import sys
#Turkce'ye ozgu karakaterler iceren basliklar icin:
reload(sys)
sys.setdefaultencoding('utf8')

import funcs as f

url="https://eksisozluk.com"
anahtar_kelime = raw_input("Anahtar kelimeyi giriniz:")
basliklar,linkler = f.istenenBasliklariGetir(f.gundemGetir(f.htmlFormatla(f.httpIstek(url))),anahtar_kelime,url)

f.mongodbYaz(basliklar,linkler)