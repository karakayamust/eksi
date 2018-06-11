import requests
from bs4 import BeautifulSoup as bs
from pymongo import MongoClient


def hata(mesaj): #hata mesajini ekrana basan fonksiyon
    print(mesaj)


def httpIstek(url):#requests modulunu kullanarak web icerigini alir.
    cevap = requests.get(url)
    if cevap.status_code != 200:
        hata("Sayfa su cevap kodunu dondu:", cevap.status_code)
        return None
    return cevap


def htmlFormatla(http_cevap): #beautifulsoap modulunu kullanarak web icerigini html formatina gore parse eder.
    return bs(http_cevap.content, "html.parser")


def gundemGetir(html_cevap): #eksisozluk anasayfasinda sol taraftaki gundem menusunu ceken fonksiyon
    #"ul" tag'ine sahip, "class" attribute'u "topic-list partial" olan elementi bul;
    #Bu elementin icinde "li" taglilerden "id" attribute'una sahip olmayanlari al.
    #Sponsorlu icerikler "id"ye sahip.
    return html_cevap.find("ul", attrs={"class": "topic-list partial"}).find_all("li", id=False)

def istenenBasliklariGetir(gundem,anahtar_kelime,url): #verilen anahtar kelimeyi iceren basliklari getirir.
    basliklar = []
    linkler = []
    for i in range(len(gundem)):
        #find fonksiyonu verilen pattern bulunamazsa "-1" varsayilan degerini donuyor.
        if (gundem[i].a.text.find(anahtar_kelime) != -1):
            basliklar.append(gundem[i].text) #baslik isimleri
            link = gundem[i].a['href'] #baslik linkleri
            #gundemdeki baslik linkleri, icinde "popular" gecen bir url ile tutuluyor.
            #Ornek: "https://eksisozluk.com/base-42--5544086?a=popular"
            #Bu linkler sadece o gune ait entryleri getiriyor.
            #Tum entryler icin ilk sayfanin url adresi uretilir:
            #Ornek: "https://eksisozluk.com/base-42--5544086?&p=1"
            link = link[:-9]
            linkler.append(url + link + "&p=1")
    if not basliklar:
        hata("Gundemde anahtar kelimeyi iceren baslik bulunamadi!")
        exit()
    return basliklar,linkler


def sayfaSayisiBul(link): #birinci sayfada bulunan "pager"dan basliga ait kac sayfa oldugunu bulur.
    baslik=httpIstek(link)
    baslik=htmlFormatla(baslik)
    return int(baslik.find("div", attrs={"class":"pager"})['data-pagecount'])

def sayfaLinkiUret(link): #her sayfa icin url uretir.
    linkler = []
    son_sayfa=sayfaSayisiBul(link)
    link=link[:-1]
    for i in range(son_sayfa):
        linkler.append(link + str(i + 1))

    return linkler

def entryleriGetir(baslik): #her sayfanin icindeki tum enrtyleri getirir.
    cevap1 = []
    cevap2 = []
    entryler = []
    entry_no = []
    tarih = []
    sayfa_linkleri=sayfaLinkiUret(baslik)
    for link in sayfa_linkleri:
        s=htmlFormatla(httpIstek(link))
        cevap1.extend(s.find_all("div", attrs={"class":"content"})) #entry
        cevap2.extend(s.find_all("a", attrs={"class":"entry-date permalink"}))  #entry_no ve tarih
        for i in range(len(cevap1)):
            entryler.append(cevap1[i].text) #entry icerigi
            entry_no.append(cevap2[i]['href'].split("/entry/", 1)[1]) #entry_no
            tarih.append(cevap2[i].text) #entry tarihi

    return list(map(list, zip(entry_no,entryler,tarih)))

def entryleriDuzenle(basliklar,linkler): #entryleri ve ait oldugu baslik isimlerini tek listede birlestirir.
    baslik = []
    entryler = []
    for i in range(len(linkler)):
        entryler.extend(entryleriGetir(linkler[i]))
        for entry in entryler:
            baslik.append(basliklar[i])

    return list(map(list, zip(baslik, entryler)))

def mongodbYaz(basliklar,linkler): #koleksiyon ve dokumanlari olusturup, mongodb'ye kaydeder.
    conn = MongoClient()
    db = conn["eksi"]
    entryler = entryleriDuzenle(basliklar, linkler)
    i = 0
    for link in linkler:
        db.create_collection(link) #ismi baslik linki olan koleksiyon olusturur.
        collection = db[link]
        for j in range(len(entryler)):
            if (basliklar[i] == entryler[j][0]): #her entry icin ayri dokuman olusturur.
                document = {}
                document["baslik"] = entryler[j][0]
                document["entry_no"] = entryler[j][1][0]
                document["entry"] = entryler[j][1][1]
                document["tarih"] = entryler[j][1][2]
                collection.insert(document) #dokumani veritabanina kaydeder.
        i = i + 1
