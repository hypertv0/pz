import os
import re
import time
from curl_cffi import requests

def get_working_domain(session):
    print("\n🔍 PapazSports güncel adresi aranıyor (Agresif Mod)...", flush=True)
    
    # 1005'ten başlayıp geriye ve ileriye doğru tarayalım
    check_list = [1005, 1006, 1004, 1007, 1003, 1008, 1002, 1009, 1001, 1010, 1000]
    for num in range(1011, 1025): check_list.append(num)

    for num in check_list:
        test_url = f"https://www.papazsports{num}.pro"
        # Canlı log: Her denemeyi anında görelim
        print(f"Deneyiyor: {test_url:<35}", end=" ", flush=True)
        
        try:
            # Cloudflare'i kandırmak için sanki Google Aramadan gelmişiz gibi davranıyoruz
            res = session.get(
                test_url, 
                timeout=8, 
                allow_redirects=True,
                headers={"Referer": "https://www.google.com/search?q=papazsports"}
            )
            
            status = res.status_code
            body = res.text.lower()
            
            # Başarılı giriş veya Cloudflare meydan okuması (503/403) fark etmez, 
            # domain yaşıyorsa içine bakıyoruz
            if status in [200, 503, 403]:
                # Eğer sayfa içinde papazsports geçiyorsa veya 1000.pro bizi bir yere attıysa
                if "papazsports" in body or "papazsports" in res.url:
                    final_url = res.url.rstrip('/')
                    print(f"✅ [Kod: {status}] -> {final_url}", flush=True)
                    return final_url
                else:
                    print(f"⚠️ [Kod: {status}] (PapazSports değil)", flush=True)
            else:
                print(f"❌ [Kod: {status}]", flush=True)
                
        except Exception as e:
            print(f"🚫 (Erişim Yok)", flush=True)
            
    return None

def main():
    # Chrome 120 parmak izi ile başla
    session = requests.Session(impersonate="chrome120")
    
    # Headerları logdaki gibi birebir taklit et
    session.headers.update({
        "Accept": "*/*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty"
    })

    domain = get_working_domain(session)
    if not domain:
        print("\n❌ Maalesef hiçbir güncel domain bulunamadı veya tüm IP'ler bloklu.", flush=True)
        return
        
    domain_clean = domain.replace("https://", "").replace("www.", "")
    session.cookies.set("puShown", "1", domain=domain_clean)

    # Kanallar (Senin gönderdiğin HTML'den birebir çekildi)
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

    output_dir = "kanallar"
    os.makedirs(output_dir, exist_ok=True)
    global_playlist = ["#EXTM3U"]

    print("\n⏳ Linkler toplanıyor (Anlık)...", flush=True)

    for channel_id, (name, tvg_id) in vip_channels.items():
        print(f"📡 Çekiliyor: {name:<20}", end=" ", flush=True)
        try:
            # POST isteği ile auth.php'den token alıyoruz
            # Referer ve Origin çok önemli
            auth_res = session.post(
                f"{domain}/auth.php",
                data={"channel": channel_id},
                headers={
                    "Origin": domain,
                    "Referer": f"{domain}/"
                },
                timeout=12
            )
            
            if auth_res.status_code == 200:
                try:
                    data = auth_res.json()
                    stream_url = data.get("URL")
                    token = data.get("TOKEN")
                    
                    if stream_url and token:
                        # IPTV oynatıcıları için Header Pipe formatı
                        final_url = f"{stream_url}|usertoken={token}&pl=PapazSports&Referer={domain}/"

                        content = [
                            "#EXTM3U",
                            f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
                            final_url
                        ]
                        
                        clean_name = re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")
                        with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                            f.write("\n".join(content))

                        global_playlist.extend(content[1:])
                        print(f"✅ [Token: {token[:8]}...]", flush=True)
                    else:
                        print("❌ [JSON Boş]", flush=True)
                except:
                    print(f"❌ [Bot Koruması - JSON Alınamadı]", flush=True)
            else:
                print(f"❌ [Hata: {auth_res.status_code}]", flush=True)
                
            # Sunucuyu yormamak ve yakalanmamak için minik bir bekleme
            time.sleep(0.5)
            
        except Exception:
            print("⚠️ [Zaman Aşımı]", flush=True)

    # Playlist'i kaydet
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(global_playlist))

    print("\n🎉 İşlem tamamlandı. Dosyalar güncellendi.", flush=True)

if __name__ == "__main__":
    main()
