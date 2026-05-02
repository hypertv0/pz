import re
import os
import time
import json
from playwright.sync_api import sync_playwright

# --- Ayarlar ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def find_working_domain(context):
    print("\n🔍 PapazSports güncel adresi aranıyor...", flush=True)
    # Geriye doğru tarama (1010 -> 1000)
    for num in range(1015, 999, -1):
        test_url = f"https://www.papazsports{num}.pro/"
        page = context.new_page()
        try:
            print(f"Deneyiyor: {test_url:<35}", end="\r", flush=True)
            # Sayfaya git ve Cloudflare'in (503/403) aşılmasını bekle
            response = page.goto(test_url, timeout=30000, wait_until='domcontentloaded')
            
            # Cloudflare meydan okuması için biraz zaman ver
            page.wait_for_timeout(7000)
            
            title = page.title().lower()
            # Eğer başlıkta PapazSports varsa ve Cloudflare kelimesi yoksa bulduk demektir
            if "papazsports" in title and "moment" not in title:
                final_url = page.url.rstrip('/')
                print(f"\n✅ Başarılı! Adres: {final_url}", flush=True)
                return final_url, page
        except Exception as e:
            pass
        page.close()
    return None, None

def main():
    with sync_playwright() as p:
        # Tarayıcıyı 'insan' gibi gösteren ayarlar
        browser = p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox'
        ])
        
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={'width': 1920, 'height': 1080}
        )

        domain, page = find_working_domain(context)
        if not domain:
            print("\n❌ HATA: Hiçbir domain çalışmıyor veya Cloudflare aşılamadı.", flush=True)
            return

        # VIP Kanallar
        vip_channels = {
            "100001": "beIN 1", "100002": "beIN 2", "100003": "beIN 3",
            "100004": "beIN 4", "100005": "beIN 5", "100006": "beIN Max 1",
            "100007": "beIN Max 2", "100010": "S-Sport 1", "100011": "S-Sport 2",
            "100021": "TiViBUSPOR 1", "100022": "TiViBUSPOR 2", "100023": "TiViBUSPOR 3",
            "100024": "TiViBUSPOR 4", "100030": "SMARTSPOR 1", "100031": "SMARTSPOR 2",
            "100051": "TV 8.5", "100052": "A Spor", "100053": "NBA TV",
            "100056": "EUROSPORT 1", "100057": "EUROSPORT 2"
        }

        output_dir = "kanallar"
        os.makedirs(output_dir, exist_ok=True)
        global_playlist = ["#EXTM3U"]

        print("\n🚀 Yayın linkleri sitenin içinden (evaluate) çekiliyor...", flush=True)

        for channel_id, name in vip_channels.items():
            print(f"📡 İşleniyor: {name:<20}", end=" ", flush=True)
            try:
                # Sitenin içindeki mevcut oturumu (cookie/session) kullanarak POST isteği atıyoruz
                # Cloudflare bunu sitenin kendi eylemi sandığı için engellemez.
                fetch_script = f"""
                async () => {{
                    try {{
                        let response = await fetch('/auth.php', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest' }},
                            body: 'channel={channel_id}'
                        }});
                        return await response.text();
                    }} catch (err) {{
                        return "SCRIPT_ERROR: " + err.message;
                    }}
                }}
                """
                
                raw_response = page.evaluate(fetch_script)
                
                # Detaylı Loglama
                if not raw_response or "SCRIPT_ERROR" in raw_response:
                    print(f"❌ SCRIPT HATASI: {raw_response}", flush=True)
                    continue

                try:
                    data = json.loads(raw_response)
                except:
                    print(f"❌ JSON DEĞİL! (Gelen veri ilk 50 harf: {raw_response[:50]}...)", flush=True)
                    continue

                if "URL" in data and "TOKEN" in data:
                    stream_url = data["URL"]
                    token = data["TOKEN"]
                    
                    # Başlıklar
                    final_url = f"{stream_url}|usertoken={token}&pl=PapazSports&Origin={domain}&Referer={domain}/"
                    
                    content = [
                        "#EXTM3U",
                        f'#EXTINF:-1, {name}',
                        final_url
                    ]
                    
                    clean_name = name.replace(" ", "_").replace(".", "")
                    with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                        f.write("\n".join(content))

                    global_playlist.append(f'#EXTINF:-1, {name}')
                    global_playlist.append(final_url)
                    print("✅", flush=True)
                else:
                    print(f"❌ API BOŞ: {data}", flush=True)

            except Exception as e:
                print(f"⚠️ Hata: {str(e)}", flush=True)
            
            page.wait_for_timeout(1000) # Siteyi yormayalım

        # Listeyi Kaydet
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(global_playlist))

        browser.close()
        print("\n🎉 Tüm işlemler bitti. Logları kontrol edin.", flush=True)

if __name__ == "__main__":
    main()
