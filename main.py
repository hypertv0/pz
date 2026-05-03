import re
import os
import json
from playwright.sync_api import sync_playwright

# --- Ayarlar ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def main():
    with sync_playwright() as p:
        # CF atlatmak için Stealth (Gizlilik) argümanları
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-web-security'
            ]
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        # Tarayıcıyı "Ben bir bot değilim" diye kandıran JS hilesi
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        captured_token = None
        captured_cdn_base = None

        # ARKA PLAN AĞ DİNLEYİCİSİ: Site kendi kendine auth.php'yi çağırdığında araya girip cevabı çalarız!
        def handle_response(response):
            nonlocal captured_token, captured_cdn_base
            if "auth.php" in response.url and response.request.method == "POST":
                try:
                    data = response.json()
                    if "TOKEN" in data and "URL" in data:
                        captured_token = data["TOKEN"]
                        # URL'yi parçala (Örn: https://cdn.../100001.js kısmındaki 100001.js'yi at)
                        captured_cdn_base = data["URL"].rsplit('/', 1)[0]
                except:
                    pass

        page.on("response", handle_response)

        print("\n🔍 PapazSports güncel adresi aranıyor...", flush=True)
        active_domain = None

        # Eskisi gibi çalışmayan yönlendiricilere takılmamak için TERS yönde (1015 -> 1000) tarıyoruz
        for num in range(1015, 999, -1):
            test_url = f"https://www.papazsports{num}.pro/"
            print(f"Deneyiyor: {test_url:<35}", end="\r", flush=True)
            try:
                res = page.goto(test_url, timeout=12000)
                # Sayfa yanıt verdiyse (CF 403 veya Başarılı 200) içeri girip bekleyelim
                if res and res.status in[200, 403, 503]:
                    page.wait_for_timeout(3000)
                    title = page.title().lower()
                    if "papaz" in title or "moment" in title or "cloudflare" in title:
                        active_domain = page.url.rstrip('/')
                        print(f"\n✅ Domain bulundu: {active_domain}", flush=True)
                        break
            except Exception:
                pass

        if not active_domain:
            print("\n❌ Çalışan alan adı bulunamadı.")
            browser.close()
            return

        print("⏳ Cloudflare koruması ve oynatıcının yüklenmesi bekleniyor (Maks 20 sn)...", flush=True)
        
        # Sitenin otomatik olarak ilk kanalı yüklemesini (ve auth.php'ye istek atmasını) bekliyoruz
        for _ in range(20):
            if captured_token:
                break
            page.wait_for_timeout(1000)

        # Eğer otomatik yüklemediyse, ekrandaki kanal butonuna (beIN 1) tıklayarak manuel tetikliyoruz
        if not captured_token:
            print("⚠️ Oynatıcı otomatik başlamadı, kanal listesinden tetikleniyor...", flush=True)
            try:
                page.click('.channel-item', timeout=5000)
                for _ in range(10):
                    if captured_token: break
                    page.wait_for_timeout(1000)
            except:
                pass

        if not captured_token:
            print("❌ Oynatıcıdan token çalınamadı. Cloudflare geçilememiş olabilir.", flush=True)
            browser.close()
            return

        print(f"\n🎯 BAŞARILI! Global Token Havada Yakalandı: {captured_token}", flush=True)

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

        print("🚀 URL'ler tek bir Token üzerinden otomatik oluşturuluyor...", flush=True)

        # Ağ trafiğini meşgul edip banlanmak yerine, yakaladığımız 1 token ile BÜTÜN kanalları matematikle üretiyoruz!
        for channel_id, (name, tvg_id) in vip_channels.items():
            print(f"📡 {name:<18} ✅")
            
            # Kanal URLsini kendimiz oluşturuyoruz (Örn: https://cdn.../1777.../100002.js)
            stream_url = f"{captured_cdn_base}/{channel_id}.js"
            
            # Ağ loglarında (OPTIONS/GET isteklerinde) istenen Header bilgileri
            pipe_headers = f"usertoken={captured_token}&pl=PapazSports&Origin={active_domain}&Referer={active_domain}/"
            final_link = f"{stream_url}|{pipe_headers}"

            content =[
                "#EXTM3U",
                f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
                f"#EXTVLCOPT:http-user-agent={USER_AGENT}",
                f"#EXTVLCOPT:http-referrer={active_domain}/",
                final_link
            ]

            clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
            with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                f.write("\n".join(content))

            global_playlist.extend(content[1:])

        for key, (name, tvg_id, url) in direct_channels.items():
            print(f"📡 {name:<18} (Şifresiz) ✅")
            content =[
                "#EXTM3U",
                f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
                f"#EXTVLCOPT:http-user-agent={USER_AGENT}",
                url
            ]
            clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
            with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                f.write("\n".join(content))
            global_playlist.extend(content[1:])

        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(global_playlist))

        browser.close()
        print("\n🎉 İŞLEM BİTTİ! Tüm kanallar banlanma riski olmadan, 1 saniyede dosyaya döküldü.", flush=True)

if __name__ == "__main__":
    main()
