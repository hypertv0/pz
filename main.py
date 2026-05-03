import os
import re
import json
import time
from curl_cffi import requests

# Senin bizzat DuckDuckGo ile girerken kullandığın ve CF'nin güvendiği User-Agent
USER_AGENT = "Mozilla/5.0 (Linux; Android 16; SM-X520) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.7727.111 Mobile Safari/537.36"

def get_working_domain(session):
    print("🔍 Güncel Adres Aranıyor...", flush=True)
    # Senin loglarda %100 çalışan 1000 -> 1005 yönlendirme sistemin
    try:
        res = session.get("https://www.papazsports1000.pro/", allow_redirects=True, timeout=10)
        final_url = res.url.rstrip('/')
        if "papazsports" in final_url:
            print(f"🎯 Yönlendirme Başarılı! Güncel Adres: {final_url}", flush=True)
            return final_url
    except:
        pass
    return "https://www.papazsports1005.pro"

def get_global_token(session, domain):
    """
    Bu fonksiyon, GitHub IP'si engelli olduğu için farklı proxy'ler üzerinden 
    SADECE BİR KERE geçerli bir TOKEN almaya çalışır.
    """
    print("🚀 Global Token alınmaya çalışılıyor (Proxy Katmanları Deneniyor)...", flush=True)
    
    target_api = f"{domain}/auth.php"
    # Sitenin kendi Proxy'si ve 2 adet yedek global proxy
    proxies = [
        f"https://api.codetabs.com/v1/proxy?quest={target_api}",
        f"https://morning-limit-0661.cf-889.workers.dev/{domain}/auth.php",
        f"https://api.allorigins.win/raw?url={target_api}"
    ]

    payload = {"channel": "100001"} # Sadece beIN 1 için bir kere soruyoruz
    
    for p_url in proxies:
        print(f"🔗 Deneniyor: {p_url[:50]}...", flush=True)
        try:
            # POST isteği ile Token'i söküp alıyoruz
            res = session.post(p_url, data=payload, headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{domain}/",
                "Origin": domain
            }, timeout=12)
            
            if res.status_code == 200 and "TOKEN" in res.text:
                data = res.json()
                print("✅ Token Başarıyla Yakalandı!", flush=True)
                return data # {"URL": "...", "TOKEN": "..."}
        except:
            continue
    return None

def main():
    # curl_cffi ile gerçek Chrome parmak izi
    session = requests.Session(impersonate="chrome120")
    
    domain = get_working_domain(session)
    
    # Sitenin aradığı o meşhur çerez
    domain_clean = domain.replace("https://", "").replace("www.", "").split('/')[0]
    session.cookies.set("puShown", "1", domain=domain_clean)

    # Önce tek bir token alalım
    auth_data = get_global_token(session, domain)
    
    if not auth_data:
        print("\n❌ HATA: Cloudflare tüm proxy yollarını GitHub için kapatmış.", flush=True)
        return

    token = auth_data["TOKEN"]
    # CDN base adresini URL'den çekiyoruz (Örn: https://cdn.../token/timestamp)
    base_cdn_url = auth_data["URL"].rsplit('/', 1)[0]

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

    output_dir = "kanallar"
    os.makedirs(output_dir, exist_ok=True)
    global_playlist = ["#EXTM3U"]

    print("\n⚡ Token kullanılarak tüm kanallar oluşturuluyor...", flush=True)

    for channel_id, (name, tvg_id) in vip_channels.items():
        # Sunucuya hiç sormadan linki kendimiz Token ile inşa ediyoruz!
        stream_url = f"{base_cdn_url}/{channel_id}.js"
        pipe_headers = f"usertoken={token}&pl=PapazSports&Origin={domain}&Referer={domain}/"
        final_link = f"{stream_url}|{pipe_headers}"

        content = [
            "#EXTM3U",
            f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
            final_link
        ]
        
        clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
        with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        global_playlist.extend(content[1:])
        print(f"📡 {name:<15} ✅", flush=True)

    # Şifresiz TRT kanalları
    trt_list = {
        "TRT 1": "https://tv-trt1.medya.trt.com.tr/master.m3u8",
        "TRT Spor": "https://tv-trtspor1.medya.trt.com.tr/master.m3u8",
        "TRT Yıldız": "https://tv-trtspor2.medya.trt.com.tr/master.m3u8"
    }
    for trt_name, trt_url in trt_list.items():
        global_playlist.append(f'#EXTINF:-1, {trt_name}')
        global_playlist.append(trt_url)

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(global_playlist))

    print("\n🎉 MÜKEMMEL! Tüm kanallar tek bir Token üzerinden başarıyla oluşturuldu.", flush=True)

if __name__ == "__main__":
    main()
