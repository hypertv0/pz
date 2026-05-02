import os
import re
from curl_cffi import requests

def get_working_domain(session):
    print("\n🔍 PapazSports güncel adresi aranıyor (Cloudflare Atlatma Modu)...", flush=True)
    
    # Öncelikle 1000 numaralı ana yönlendiriciyi test edelim.
    try:
        print("Deneyiyor: https://www.papazsports1000.pro/", flush=True)
        # allow_redirects=True sayesinde 1000'den 1005'e giden o yönlendirmeyi takip eder
        res = session.get("https://www.papazsports1000.pro/", allow_redirects=True, timeout=10)
        
        # Eğer Cloudflare korumasını (curl_cffi sayesinde) aşarsak sayfa kaynağı gelir
        if res.status_code == 200 and "papazsports" in res.text.lower() and "just a moment" not in res.text.lower():
            final_url = res.url.rstrip('/')
            print(f"🎯 Yönlendirme Başarılı! Güncel Adres: {final_url}", flush=True)
            return final_url
    except:
        pass

    # Eğer 1000 çalışmazsa yedek tarama (Geriye doğru tarayarak en günceli bulur)
    for num in range(1030, 999, -1):
        test_url = f"https://www.papazsports{num}.pro"
        print(f"Deneyiyor: {test_url:<35}", end="\r", flush=True)
        try:
            res = session.get(test_url, timeout=5)
            if res.status_code == 200 and "papazsports" in res.text.lower() and "just a moment" not in res.text.lower():
                print(f"\n🎯 Güncel Adres Tespit Edildi: {test_url}", flush=True)
                return test_url
        except Exception:
            pass
            
    return None

def main():
    # En Kritik Kısım: impersonate="chrome116"
    # Bu ayar, Python'un bir bot olduğunu gizler ve Cloudflare'e %100 gerçek bir Chrome tarayıcısı gibi görünür.
    session = requests.Session(impersonate="chrome116")
    
    domain = get_working_domain(session)
    if not domain:
        print("\n❌ Çalışan ana domain bulunamadı veya CF aşılamadı.", flush=True)
        return
        
    # Ağ trafiğinde gördüğümüz, sitenin "reklamları geçtim" cookie'si
    domain_clean = domain.replace("https://", "").replace("http://", "")
    session.cookies.set("puShown", "1", domain=domain_clean)

    vip_channels = {
        "100001": ("beIN 1", "BeinSports1.tr"),
        "100002": ("beIN 2", "BeinSports2.tr"),
        "100003": ("beIN 3", "BeinSports3.tr"),
        "100004": ("beIN 4", "BeinSports4.tr"),
        "100005": ("beIN 5", "BeinSports5.tr"),
        "100006": ("beIN Max 1", "BeinMax1.tr"),
        "100007": ("beIN Max 2", "BeinMax2.tr"),
        "100010": ("S-Sport 1", "SSport1.tr"),
        "100011": ("S-Sport 2", "SSport2.tr"),
        "100021": ("TiViBUSPOR 1", "TivibuSpor1.tr"),
        "100022": ("TiViBUSPOR 2", "TivibuSpor2.tr"),
        "100023": ("TiViBUSPOR 3", "TivibuSpor3.tr"),
        "100024": ("TiViBUSPOR 4", "TivibuSpor4.tr"),
        "100030": ("SMARTSPOR 1", "SmartSpor1.tr"),
        "100031": ("SMARTSPOR 2", "SmartSpor2.tr"),
        "100051": ("TV 8.5", "TV85.tr"),
        "100052": ("A Spor", "ASpor.tr"),
        "100053": ("NBA TV", "NBATV.tr"),
        "100056": ("EUROSPORT 1", "Eurosport1.tr"),
        "100057": ("EUROSPORT 2", "Eurosport2.tr")
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

    print("\n⏳ Cloudflare aşıldı! Doğrudan API'den veriler çekiliyor...", flush=True)

    for channel_id, (name, tvg_id) in vip_channels.items():
        print(f"📡 Çekiliyor: {name:<20} (ID: {channel_id})...", end=" ", flush=True)
        try:
            # Doğrudan arka plan dosyasına kanal id'sini POST ediyoruz
            res = session.post(
                f"{domain}/auth.php",
                data={"channel": channel_id},
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Origin": domain,
                    "Referer": f"{domain}/",
                    "Accept": "application/json, text/javascript, */*; q=0.01"
                },
                timeout=10
            )
            
            if res.status_code == 200:
                try:
                    data = res.json()
                except:
                    print("❌ Gelen yanıt JSON değil (Cloudflare blokladı)", flush=True)
                    continue
                    
                if "URL" in data and "TOKEN" in data:
                    stream_url = data["URL"]
                    token = data["TOKEN"]
                    
                    # Tivimate, ExoPlayer vb. sistemlere "Ben bu sitenin oynatıcısıyım" dedirtmek için başlıklar
                    pipe_headers = f"usertoken={token}&pl=PapazSports&Origin={domain}&Referer={domain}/"
                    final_url = f"{stream_url}|{pipe_headers}"

                    content =[
                        "#EXTM3U",
                        f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
                        final_url
                    ]
                    
                    clean_name = re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")
                    with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                        f.write("\n".join(content))

                    global_playlist.extend(content[1:])
                    print("✅ Bulundu", flush=True)
                else:
                    print("❌ JSON eksik/boş", flush=True)
            elif res.status_code == 403:
                print("❌ Cloudflare Engeli (403)", flush=True)
            else:
                print(f"❌ Sunucu Hatası ({res.status_code})", flush=True)
                
        except Exception as e:
            print(f"⚠️ Hata: Bağlantı koptu", flush=True)

    for key, (name, tvg_id, url) in direct_channels.items():
        print(f"📡 Ekleniyor: {name:<20} (Şifresiz)... ✅", flush=True)
        content =[
            "#EXTM3U",
            f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
            url
        ]
        clean_name = re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")
        with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        global_playlist.extend(content[1:])

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(global_playlist))

    print("\n🎉 İşlem bitti! Tüm yayınlar Cloudflare radarına takılmadan güvenle çekildi.", flush=True)

if __name__ == "__main__":
    main()
