import re
import os
import json
from playwright.sync_api import sync_playwright

# --- Ayarlar ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def find_working_domain(context):
    # Senin loglarda çalışan BİREBİR aynı mantık
    print("\n🔍 PapazSports yönlendiricileri test ediliyor...", flush=True)
    test_urls =["https://www.papazsports1000.pro/", "https://www.papazsports1005.pro/"]
    for num in range(1001, 1020):
        if num != 1005:
            test_urls.append(f"https://www.papazsports{num}.pro/")
            
    for test_url in test_urls:
        print(f"Deneyiyor: {test_url:<35}", end="\r", flush=True)
        try:
            res = context.request.get(test_url, timeout=5000)
            if res.status in [200, 403, 503]:
                final_url = res.url.rstrip('/')
                print(f"\n🎯 Yönlendirme Tamamlandı! Güncel Adres: {final_url}", flush=True)
                return final_url
        except Exception:
            pass
    return None

def main():
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
        
        domain = find_working_domain(context)
        
        if not domain:
            print("\n❌ Çalışan ana domain bulunamadı.", flush=True)
            browser.close()
            return

        page = context.new_page()
        
        # --- KÜTÜPHANESİZ BOT GİZLEME KALKANI ---
        # Bu kod Playwright'ın bıraktığı izleri siler, hata vermez!
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print(f"⏳ {domain} adresine giriş yapılıyor ve Cloudflare bekleniyor...", flush=True)
        
        try:
            page.goto(domain, timeout=30000, wait_until='domcontentloaded')
            page.wait_for_timeout(5000)
            
            title = page.title().lower()
            if "moment" in title or "cloudflare" in title or "attention" in title:
                print("🛡️ CF Turnstile saptandı! Sanal ekranda tıklama yapılıyor...", flush=True)
                page.mouse.move(100, 100)
                page.wait_for_timeout(1000)
                page.mouse.click(640, 360)  # Ekranın ortasındaki kutuya tıklar
                page.wait_for_timeout(8000)
        except Exception as e:
            print(f"⚠️ Sayfa yüklenirken uyarı: {e}", flush=True)

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

        print("🚀 Site içi Javascript tetiklenerek linkler toplanıyor...", flush=True)

        for channel_id, (name, tvg_id) in vip_channels.items():
            print(f"📡 Çekiliyor: {name:<15}", end=" ", flush=True)
            try:
                fetch_script = f"""
                async () => {{
                    try {{
                        let res = await fetch('/auth.php', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest' }},
                            body: 'channel={channel_id}'
                        }});
                        return await res.json();
                    }} catch (e) {{ return null; }}
                }}
                """
                data = page.evaluate(fetch_script)
                
                if data and "URL" in data and "TOKEN" in data:
                    m3u8_url = data["URL"]
                    token = data["TOKEN"]
                    
                    final_link = f"{m3u8_url}|usertoken={token}&pl=PapazSports&Origin={domain}&Referer={domain}/"

                    content =[
                        "#EXTM3U",
                        f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
                        f"#EXTVLCOPT:http-user-agent={USER_AGENT}",
                        f"#EXTVLCOPT:http-referrer={domain}/",
                        final_link
                    ]

                    clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
                    with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                        f.write("\n".join(content))

                    global_playlist.extend(content[1:])
                    print("✅", flush=True)
                else:
                    print("❌ JSON Bulunamadı/CF Engeli", flush=True)
            except Exception as e:
                print("⚠️ Hata", flush=True)
            
            # Sitenin API sini yormamak icin cok ufak bekleme
            page.wait_for_timeout(500)

        for key, (name, tvg_id, url) in direct_channels.items():
            print(f"📡 Ekleniyor: {name:<15} (Şifresiz)... ✅", flush=True)
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
        print("\n🎉 İşlem bitti. Tüm m3u8 dosyaları güncellendi.", flush=True)

if __name__ == "__main__":
    main()
