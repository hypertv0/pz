import os
import re
import requests
import json

# SENİN KURDUĞUN EFSANE CLOUDFLARE WORKER ADRESİ
WORKER_URL = "https://pz.hypercors.workers.dev"

def get_working_domain():
    print(f"\n🔍 Cloudflare Worker üzerinden güncel PapazSports adresi aranıyor...", flush=True)
    
    # 1. Aşama: Worker üzerinden ana domaini bulma 
    # (Worker 1000 numarasına girip yönlendirmeyi takip edip güncel adresi dönecek)
    domain = None
    try:
        print("Deneyiyor: https://www.papazsports1000.pro/", flush=True)
        api_url = f"{WORKER_URL}?url=https://www.papazsports1000.pro/"
        res = requests.get(api_url, timeout=15)
        
        # JS kodumuz başarılı yönlendirmede URL'yi metin olarak dönüyor
        if res.status_code == 200 and "papazsports" in res.text:
            domain = res.text.strip().rstrip('/')
            print(f"🎯 Worker Yönlendirmeyi Şipşak Buldu: {domain}", flush=True)
            return domain
    except Exception as e:
        print(f"⚠️ 1000.pro'ya ulaşılamadı, alternatifler taranıyor...", flush=True)

    # Eğer 1000 çalışmazsa yedek tarama (Geriye doğru tarayarak en günceli bulur)
    for num in range(1030, 999, -1):
        test_url = f"https://www.papazsports{num}.pro/"
        print(f"Deneyiyor: {test_url:<35}", end="\r", flush=True)
        try:
            api_url = f"{WORKER_URL}?url={test_url}"
            res = requests.get(api_url, timeout=10)
            if res.status_code == 200 and "papazsports" in res.text:
                domain = res.text.strip().rstrip('/')
                print(f"\n🎯 Güncel Adres Tespit Edildi: {domain}", flush=True)
                return domain
        except Exception:
            pass
            
    return None

def main():
    domain = get_working_domain()
    
    if not domain:
        print("\n❌ Maalesef domain bulunamadı veya Worker yanıt vermedi.", flush=True)
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

    print(f"\n🚀 Worker üzerinden {domain} API'sine bağlanılıyor. Linkler çekiliyor...", flush=True)

    for channel_id, (name, tvg_id) in vip_channels.items():
        print(f"📡 Çekiliyor: {name:<18}", end=" ", flush=True)
        try:
            # Sitenin auth.php adresini Worker'a "POST Et" emriyle yolluyoruz
            api_url = f"{WORKER_URL}?url={domain}/auth.php"
            
            # Worker bizim yerimize arka planda PapazSports'a sahte (spoof) headerlar ile istek atacak
            res = requests.post(api_url, data={"channel": channel_id}, timeout=15)
            
            if res.status_code == 200:
                try:
                    data = res.json()
                    stream_url = data.get("URL")
                    token = data.get("TOKEN")
                    
                    if stream_url and token:
                        # Oynatıcı Referansları (Headers)
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
                        print("❌ (Gelen JSON'da URL veya Token Yok)", flush=True)
                except Exception as e:
                    print(f"❌ (Worker'dan dönen veri JSON değil: CF Engeli Olabilir)", flush=True)
            else:
                print(f"❌ (Sunucu Hatası: {res.status_code})", flush=True)
        except Exception as e:
            print("⚠️ Zaman Aşımı", flush=True)

    # TRT Şifresiz Kanallar
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

    print("\n🎉 İşlem Bitti! Tüm yayınlar Worker Proxy sayesinde milisaniyeler içinde çekildi.", flush=True)

if __name__ == "__main__":
    main()
