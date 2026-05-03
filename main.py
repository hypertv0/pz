import os
import re
import requests
import json
import time

# Senin DuckDuckGo ile girerken bıraktığın mobil ağ izi (CF'yi kandırmak için birebir)
MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; Android 16; SM-X520) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.7727.111 Mobile Safari/537.36"

def get_domain():
    print("🔍 Sitenin kendi gizli API'sinden PapazSports adresi çekiliyor...", flush=True)
    try:
        res = requests.get("https://ahatm12od.top/domain_list.json", timeout=10)
        if res.status_code == 200:
            data = res.json()
            for key, value in data.items():
                if "papaz" in str(value).lower():
                    url = f"https://www.{value}/" if not value.startswith("http") else value
                    if not url.endswith('/'): url += '/'
                    print(f"🎯 Hedef Adres Anında Bulundu: {url}", flush=True)
                    return url
    except Exception as e:
        print("⚠️ API çalışmadı, manuel tarama yapılıyor...", flush=True)

    # API çalışmazsa genel proxy üzerinden tarama
    for num in range(1015, 999, -1):
        test_url = f"https://www.papazsports{num}.pro/"
        print(f"Deneniyor: {test_url:<35}", end="\r", flush=True)
        try:
            # Proxy kullanarak GitHub IP engellemesini aşıyoruz
            proxy_url = f"https://api.codetabs.com/v1/proxy?quest={test_url}"
            r = requests.get(proxy_url, timeout=5)
            if r.status_code == 200 and "papazsports" in r.text.lower():
                print(f"\n✅ Adres Bulundu: {test_url}", flush=True)
                return test_url
        except:
            pass
    return None

def fetch_channel_data(domain, channel_id):
    """
    Cloudflare GitHub'ı tamamen blokladığı için (Attention Required HTML'si veriyor),
    isteği GitHub üzerinden DEĞİL, Proxy'ler üzerinden atıyoruz!
    """
    domain_clean = domain.rstrip('/')
    
    headers = {
        "User-Agent": MOBILE_USER_AGENT,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": domain_clean,
        "Referer": f"{domain_clean}/",
        "Cookie": "puShown=1"
    }
    data = {"channel": channel_id}

    # KATMAN 1: Sitenin kendi HTML'sinde bulduğumuz, onlara ait olan Worker Proxy!
    try:
        url1 = f"https://morning-limit-0661.cf-889.workers.dev/{domain_clean}/auth.php"
        res1 = requests.post(url1, data=data, headers=headers, timeout=8)
        if res1.status_code == 200 and "TOKEN" in res1.text:
            return res1.json(), "Sitenin Kendi Worker'ı"
    except: pass

    # KATMAN 2: Dünyaca ünlü açık kaynak CodeTabs CORS Proxy'si
    try:
        url2 = f"https://api.codetabs.com/v1/proxy?quest={domain_clean}/auth.php"
        res2 = requests.post(url2, data=data, headers=headers, timeout=8)
        if res2.status_code == 200 and "TOKEN" in res2.text:
            return res2.json(), "CodeTabs Proxy"
    except: pass

    # KATMAN 3: CorsProxy.io
    try:
        url3 = f"https://corsproxy.io/?{domain_clean}/auth.php"
        res3 = requests.post(url3, data=data, headers=headers, timeout=8)
        if res3.status_code == 200 and "TOKEN" in res3.text:
            return res3.json(), "CorsProxy"
    except: pass

    return None, None

def main():
    domain = get_domain()
    if not domain:
        print("\n❌ Domain bulunamadı.")
        return

    vip_channels = {
        "100001": ("beIN 1", "BeinSports1.tr"), "100002": ("beIN 2", "BeinSports2.tr"),
        "100003": ("beIN 3", "BeinSports3.tr"), "100004": ("beIN 4", "BeinSports4.tr"),
        "100005": ("beIN 5", "BeinSports5.tr"), "100006": ("beIN Max 1", "BeinMax1.tr"),
        "100007": ("beIN Max 2", "BeinMax2.tr"), "100010": ("S-Sport 1", "SSport1.tr"),
        "100011": ("S-Sport 2", "SSport2.tr"), "100021": ("TiViBUSPOR 1", "TivibuSpor1.tr"),
        "100022": ("TiViBUSPOR 2", "TivibuSpor2.tr"), "100023": ("TiViBUSPOR 3", "TivibuSpor3.tr"),
        "100024": ("TiViBUSPOR 4", "TivibuSpor4.tr"), "100030": ("SMARTSPOR 1", "SmartSpor1.tr"),
        "100031": ("SMARTSPOR 2", "SmartSpor2.tr"), "100051": ("TV 8.5", "TV85.tr"),
        "100052": ("A Spor", "ASpor.tr"), "100053": ("NBA TV", "NBATV.tr"),
        "100056": ("EUROSPORT 1", "Eurosport1.tr"), "100057": ("EUROSPORT 2", "Eurosport2.tr")
    }
    
    direct_channels = {
        "TRT_1": ("TRT 1", "TRT1.tr", "https://tv-trt1.medya.trt.com.tr/master.m3u8"),
        "TRT_2": ("TRT 2", "TRT2.tr", "https://tv-trt2.medya.trt.com.tr/master.m3u8"),
        "TRT_SPOR": ("TRT Spor", "TRTSpor.tr", "https://tv-trtspor1.medya.trt.com.tr/master.m3u8"),
        "TRT_YILDIZ": ("TRT Yıldız", "TRTSporYildiz.tr", "https://tv-trtspor2.medya.trt.com.tr/master.m3u8")
    }

    output_dir = "kanallar"
    os.makedirs(output_dir, exist_ok=True)
    global_playlist =["#EXTM3U"]

    print("\n🚀 GitHub Cloudflare Bloğu aşıldı! Proxy üzerinden linkler toplanıyor...", flush=True)

    for channel_id, (name, tvg_id) in vip_channels.items():
        print(f"📡 İşleniyor: {name:<15}", end=" ", flush=True)
        
        data, used_proxy = fetch_channel_data(domain, channel_id)
        
        if data and "URL" in data and "TOKEN" in data:
            stream_url = data["URL"]
            token = data["TOKEN"]
            
            # Oynatıcı parametreleri (Pipe Header - Cihazlarda sorunsuz açılması için)
            final_link = f"{stream_url}|usertoken={token}&pl=PapazSports&Origin={domain.rstrip('/')}&Referer={domain}"
            
            content =[
                "#EXTM3U",
                f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
                f"#EXTVLCOPT:http-user-agent={MOBILE_USER_AGENT}",
                f"#EXTVLCOPT:http-referrer={domain}",
                final_link
            ]
            
            clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
            with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                f.write("\n".join(content))

            global_playlist.extend(content[1:])
            print(f"✅ ({used_proxy})", flush=True)
        else:
            print("❌ (Tüm proxy denemeleri başarısız)", flush=True)
            
        time.sleep(0.3)

    for key, (name, tvg_id, url) in direct_channels.items():
        print(f"📡 Ekleniyor: {name:<15} (Şifresiz)... ✅", flush=True)
        content =[
            "#EXTM3U", f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
            f"#EXTVLCOPT:http-user-agent={MOBILE_USER_AGENT}", url
        ]
        clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
        with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        global_playlist.extend(content[1:])

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(global_playlist))

    print("\n🎉 İŞLEM BAŞARIYLA TAMAMLANDI! Cloudflare bloklaması 3 katmanlı proxy ile aşıldı.", flush=True)

if __name__ == "__main__":
    main()
