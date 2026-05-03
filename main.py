import os
import re
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def get_domain():
    print("🔍 Gizli API'den PapazSports güncel adresi çekiliyor...", flush=True)
    try:
        # Adamların kendi domain listesi API'si!
        res = requests.get("https://ahatm12od.top/domain_list.json", timeout=10)
        if res.status_code == 200:
            data = res.json()
            for key, value in data.items():
                if "papaz" in value.lower():
                    # Formatı düzeltiyoruz
                    url = f"https://www.{value}/" if not value.startswith("http") else value
                    if not url.endswith('/'): url += '/'
                    print(f"🎯 Hedef Adres Anında Bulundu: {url}", flush=True)
                    return url
    except Exception as e:
        print("⚠️ API çalışmadı, manuel tarama yapılıyor...", flush=True)
        
    # API bozulursa diye yedek tarama mekanizması
    for num in range(1015, 999, -1):
        test = f"https://www.papazsports{num}.pro/"
        print(f"Deneniyor: {test:<35}", end="\r", flush=True)
        try:
            r = requests.get(test, timeout=3)
            if r.status_code in [200, 403, 503]:
                print(f"\n✅ Adres Bulundu: {test}", flush=True)
                return test
        except:
            pass
    return None

def main():
    domain = get_domain()
    if not domain:
        print("\n❌ Domain bulunamadı.")
        return

    with sync_playwright() as p:
        # headless=False ve github'daki xvfb sanal ekranı sayesinde Cloudflare bizi İNSAN sanacak!
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--start-maximized'
            ]
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        
        # Bot Gizleme Kalkanını Aktif Ediyoruz
        stealth_sync(page)

        captured_token = None
        captured_base = None

        # Arka planda ağ trafiğini dinleyip oynatıcı şifresini kapıyoruz
        def handle_res(response):
            nonlocal captured_token, captured_base
            if "auth.php" in response.url and response.request.method == "POST":
                try:
                    data = response.json()
                    if "TOKEN" in data and "URL" in data:
                        captured_token = data["TOKEN"]
                        captured_base = data["URL"].rsplit('/', 1)[0]
                except:
                    pass

        page.on("response", handle_res)

        print("⏳ Siteye giriliyor ve Cloudflare bypass ediliyor...", flush=True)
        try:
            page.goto(domain, timeout=30000, wait_until='domcontentloaded')
            
            # Fareyi hareket ettir (CF Turnstile'ı insan olduğumuza ikna etmek için)
            page.mouse.move(100, 100)
            page.mouse.move(500, 500)
            page.wait_for_timeout(6000)

            # Ekranda hala Cloudflare varsa merkeze tıkla
            if "moment" in page.title().lower() or "cloudflare" in page.title().lower():
                print("🛡️ CF Turnstile çözülüyor...", flush=True)
                page.mouse.click(640, 360)
                page.wait_for_timeout(6000)
                
        except Exception as e:
            print("⚠️ Sayfa yükleme uyarısı, devam ediliyor...", flush=True)

        print("⏳ Ağ trafiği dinleniyor, Token bekleniyor...", flush=True)
        for _ in range(12):
            if captured_token: break
            page.wait_for_timeout(1000)

        # Eğer oynatıcı otomatik başlamazsa beIN 1 butonuna fareyle tıklarız
        if not captured_token:
            print("⚠️ Otomatik token gelmedi, sitedeki beIN 1 butonuna tıklanıyor...", flush=True)
            try:
                page.click('.channel-item[data-source="100001"]', timeout=5000)
                for _ in range(10):
                    if captured_token: break
                    page.wait_for_timeout(1000)
            except:
                pass

        if not captured_token:
            print("❌ Cloudflare aşılamadı veya Token alınamadı.", flush=True)
            browser.close()
            return

        print(f"\n🎯 BAŞARILI! Orijinal Token Yakalandı: {captured_token[:10]}...", flush=True)

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

        print("🚀 URL'ler yakalanan tek bir Token üzerinden oluşturuluyor...", flush=True)

        for channel_id, (name, tvg_id) in vip_channels.items():
            # Ana CDN urlsi ve token ile tüm kanalları kendimiz üretiyoruz
            stream_url = f"{captured_base}/{channel_id}.js"
            pipe_headers = f"usertoken={captured_token}&pl=PapazSports&Origin={domain.rstrip('/')}&Referer={domain}"
            final_link = f"{stream_url}|{pipe_headers}"

            content =[
                "#EXTM3U",
                f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
                f"#EXTVLCOPT:http-user-agent={USER_AGENT}",
                f"#EXTVLCOPT:http-referrer={domain}",
                final_link
            ]

            clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
            with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                f.write("\n".join(content))

            global_playlist.extend(content[1:])
            print(f"📡 Eklendi: {name}", flush=True)

        for key, (name, tvg_id, url) in direct_channels.items():
            print(f"📡 Eklendi: {name} (Şifresiz)", flush=True)
            content =[
                "#EXTM3U", f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
                f"#EXTVLCOPT:http-user-agent={USER_AGENT}", url
            ]
            clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
            with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                f.write("\n".join(content))
            global_playlist.extend(content[1:])

        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(global_playlist))

        browser.close()
        print("\n🎉 İşlem bitti! Mükemmel sistem çalıştı.", flush=True)

if __name__ == "__main__":
    main()
