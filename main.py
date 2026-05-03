import os
import re
from curl_cffi import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def get_working_domain(session):
    print("🔍 Gizli API ve Yönlendirici ile Güncel Adres Aranıyor...", flush=True)
    
    # 1. YÖNTEM: Sitenin kendi HTML'sinde bulduğumuz güncel adres API'si
    try:
        res = session.get("https://ahatm12od.top/domain_list.json", timeout=10)
        if res.status_code == 200:
            data = res.json()
            for key, value in data.items():
                if "papaz" in str(value).lower():
                    url = f"https://www.{value}/" if not value.startswith("http") else value
                    if not url.endswith('/'): url += '/'
                    print(f"🎯 Gizli API'den Hedef Adres Bulundu: {url}", flush=True)
                    return url.rstrip('/')
    except Exception:
        pass

    # 2. YÖNTEM: Senin bizzat deneyip onayladığın o çalışan yönlendirici mantığı!
    print("Deneyiyor: https://www.papazsports1000.pro/", flush=True)
    try:
        # allow_redirects=True sayesinde 1000'e girip nereye yönlendirirse onu alır (Örn: 1005)
        res = session.get("https://www.papazsports1000.pro/", allow_redirects=True, timeout=10)
        final_url = res.url.rstrip('/')
        if "papazsports" in final_url:
            print(f"🎯 Yönlendirme Tamamlandı! Güncel Adres: {final_url}", flush=True)
            return final_url
    except Exception:
        pass

    return None

def main():
    # EN ÖNEMLİ KISIM: impersonate="chrome120"
    # Bu özellik standart requests'te yoktur. CF'yi aşmamızı sağlar.
    session = requests.Session(impersonate="chrome120")

    domain = get_working_domain(session)
    if not domain:
        print("\n❌ Çalışan ana domain bulunamadı.", flush=True)
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
    global_playlist = ["#EXTM3U"]

    print(f"\n🚀 {domain} API'sine doğrudan bağlanılıyor...", flush=True)

    # Ağ loglarında (Network) görünen zorunlu başlıklar
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": domain,
        "Referer": f"{domain}/",
        "Cookie": "puShown=1"
    }

    for channel_id, (name, tvg_id) in vip_channels.items():
        print(f"📡 Çekiliyor: {name:<18}", end=" ", flush=True)

        try:
            # 1. Deneme: Doğrudan API
            url = f"{domain}/auth.php"
            res = session.post(url, data={"channel": channel_id}, headers=headers, timeout=10)

            # 2. Deneme (Yedek): Eğer Cloudflare bizi doğrudan engellerse, 
            # Sitenin HTML kodunda tespit ettiğim KENDİ worker'larına post atıyoruz!
            if res.status_code != 200 or "TOKEN" not in res.text:
                cors_url = f"https://morning-limit-0661.cf-889.workers.dev/{domain}/auth.php"
                res = session.post(cors_url, data={"channel": channel_id}, headers=headers, timeout=10)

            if res.status_code == 200:
                try:
                    data = res.json()
                    stream_url = data.get("URL")
                    token = data.get("TOKEN")

                    if stream_url and token:
                        # Oynatıcı parametreleri (Pipe Header - Cihazlarda sorunsuz açılması için)
                        pipe_headers = f"usertoken={token}&pl=PapazSports&Origin={domain}&Referer={domain}/"
                        final_link = f"{stream_url}|{pipe_headers}"

                        content =[
                            "#EXTM3U",
                            f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
                            final_link
                        ]

                        clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
                        with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                            f.write("\n".join(content))

                        global_playlist.extend(content[1:])
                        print("✅", flush=True)
                    else:
                        print("❌ (JSON'da URL/Token Yok)", flush=True)
                except Exception:
                    print("❌ (Geçersiz JSON, CF Engeli)", flush=True)
            else:
                print(f"❌ (HTTP {res.status_code})", flush=True)

        except Exception:
            print("⚠️ Zaman Aşımı", flush=True)

    for key, (name, tvg_id, url) in direct_channels.items():
        print(f"📡 Ekleniyor: {name:<18} (Şifresiz) ✅", flush=True)
        content =[
            "#EXTM3U", f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}', url
        ]
        clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
        with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        global_playlist.extend(content[1:])

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(global_playlist))

    print("\n🎉 İşlem
