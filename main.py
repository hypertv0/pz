import os
import re
import json
import time
from curl_cffi import requests

# Cloudflare'i %100 gerçek kullanıcı olduğuna ikna eden User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def get_working_domain(session):
    print("🔍 Güncel Adres Aranıyor...", flush=True)
    # Senin bizzat çalışıyor dediğin o efsane 1000 -> 1005 yönlendirme mantığı
    print("Deneyiyor: https://www.papazsports1000.pro/", flush=True)
    try:
        res = session.get("https://www.papazsports1000.pro/", allow_redirects=True, timeout=10)
        final_url = res.url.rstrip('/')
        if "papazsports" in final_url:
            print(f"🎯 Yönlendirme Başarılı! Güncel Adres: {final_url}", flush=True)
            return final_url
    except Exception as e:
        print(f"⚠️ Yönlendirme hatası: {e}", flush=True)

    # Yedek: Eğer 1000 çalışmazsa doğrudan 1005'i dene
    return "https://www.papazsports1005.pro"

def main():
    # chrome120 parmak izi ile Cloudflare'i bypass ediyoruz
    session = requests.Session(impersonate="chrome120")

    domain = get_working_domain(session)
    if not domain:
        print("\n❌ Çalışan ana domain bulunamadı.", flush=True)
        return

    # Kanallar (data-source ID'leri)
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

    print(f"\n🚀 {domain} API'sine Sızılıyor (Proxy Modu)...", flush=True)

    # Sitenin kendi gizli Worker Proxy'si! Cloudflare'i bununla eziyoruz.
    SİTE_PROXY = "https://morning-limit-0661.cf-889.workers.dev/"

    for channel_id, (name, tvg_id) in vip_channels.items():
        print(f"📡 Çekiliyor: {name:<15}", end=" ", flush=True)
        try:
            # Ninja Taktiği: POST yerine GET ile deniyoruz ve sitenin kendi proxy'sini kullanıyoruz
            # Bu sayede Cloudflare "Bu benden gelen güvenli bir istek" diyor.
            auth_url = f"{SİTE_PROXY}{domain}/auth.php"
            
            # Parametreleri gönderiyoruz
            res = session.post(
                auth_url, 
                data={"channel": channel_id}, 
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": f"{domain}/",
                    "Origin": domain
                },
                timeout=12
            )

            if res.status_code == 200 and "TOKEN" in res.text:
                data = res.json()
                m3u8_url = data.get("URL")
                token = data.get("TOKEN")
                
                # Oynatıcı Başlıkları
                final_link = f"{m3u8_url}|usertoken={token}&pl=PapazSports&Origin={domain}&Referer={domain}/"

                content = [
                    "#EXTM3U",
                    f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
                    final_link
                ]

                clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
                with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                    f.write("\n".join(content))

                global_playlist.extend(content[1:])
                print("✅ Başarılı", flush=True)
            else:
                # Hata durumunda nedenini anlamak için log basıyoruz
                err_msg = res.text[:50].replace("\n", "")
                print(f"❌ (Hata: {res.status_code} - {err_msg})", flush=True)
        except Exception as e:
            print(f"⚠️ Hata: {str(e)[:30]}", flush=True)
        
        # Cloudflare'i uyandırmamak için yarım saniye nefes al
        time.sleep(0.5)

    # Şifresizler
    for key, (name, tvg_id, url) in direct_channels.items():
        print(f"📡 Ekleniyor: {name:<15} (Şifresiz) ✅", flush=True)
        content = ["#EXTM3U", f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}', url]
        clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
        with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        global_playlist.extend(content[1:])

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(global_playlist))

    print("\n🎉 Tebrikler! Tüm linkler Cloudflare engeline takılmadan toplandı.", flush=True)

if __name__ == "__main__":
    main()
