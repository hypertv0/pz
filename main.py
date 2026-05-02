import re
import os
import json
import time
from playwright.sync_api import sync_playwright

# --- Ayarlar ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def find_working_domain(page):
    print("\n🔍 PapazSports güncel adresi aranıyor (Tarayıcı Modu)...", flush=True)
    
    # 1010'dan geriye doğru tarıyoruz (1005'i hızlı bulması için)
    for num in range(1010, 999, -1):
        test_url = f"https://www.papazsports{num}.pro/"
        print(f"Deneniyor: {test_url:<35}", end=" ", flush=True)
        
        try:
            # wait_until='commit' çok daha hızlıdır, sayfanın sadece yanıt vermesi yeterli
            response = page.goto(test_url, timeout=12000, wait_until='domcontentloaded')
            
            # Sayfa içeriğinde veya başlığında PapazSports kontrolü
            page.wait_for_timeout(2000)
            title = page.title().lower()
            
            if "papaz" in title or "spor" in title:
                # Cloudflare kontrolü
                if "just a moment" not in title and "waiting" not in title:
                    final_url = page.url.rstrip('/')
                    print(f"✅ BULUNDU: {final_url}", flush=True)
                    return final_url
                else:
                    print("⏳ CF Bekleniyor...", flush=True)
                    page.wait_for_timeout(5000)
                    if "papaz" in page.title().lower():
                        return page.url.rstrip('/')
            else:
                print("❌", flush=True)
        except:
            print("🚫", flush=True)
            continue
            
    return None

def main():
    with sync_playwright() as p:
        # Cloudflare'i aşmak için en önemli tarayıcı ayarları
        browser = p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox'
        ])
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()

        domain = find_working_domain(page)
        
        if not domain:
            print("\n❌ Çalışan ana domain bulunamadı. Lütfen numaraları kontrol et.", flush=True)
            browser.close()
            return

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

        print(f"\n🚀 {domain} üzerinden yayınlar çekiliyor...", flush=True)

        for channel_id, name in vip_channels.items():
            print(f"📡 {name:<18}", end=" ", flush=True)
            try:
                # Sitenin içinden (JS evaluate) auth.php çağrısı yapıyoruz
                # Detaylı loglama eklendi
                fetch_script = f"""
                async () => {{
                    try {{
                        let res = await fetch('/auth.php', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest' }},
                            body: 'channel={channel_id}'
                        }});
                        let text = await res.text();
                        return text;
                    }} catch (e) {{ return "ERROR:" + e.message; }}
                }}
                """
                
                raw_response = page.evaluate(fetch_script)
                
                if raw_response and "URL" in raw_response:
                    data = json.loads(raw_response)
                    stream_url = data["URL"]
                    token = data["TOKEN"]
                    
                    # Oynatıcı parametreleri (Header Pipe)
                    final_link = f"{stream_url}|usertoken={token}&pl=PapazSports&Origin={domain}&Referer={domain}/"
                    
                    content = ["#EXTM3U", f'#EXTINF:-1 tvg-id="{name}" tvg-name="{name}",{name}', final_link]
                    clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
                    
                    with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                        f.write("\n".join(content))

                    global_playlist.append(f'#EXTINF:-1 tvg-id="{name}" tvg-name="{name}",{name}')
                    global_playlist.append(final_link)
                    print(f"✅ (Token: {token[:6]}...)", flush=True)
                else:
                    print(f"❌ Yanıt: {raw_response[:30]}", flush=True)
            except Exception as e:
                print(f"⚠️ Hata: {str(e)[:30]}", flush=True)

        # Playlist'i kaydet
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(global_playlist))

        browser.close()
        print("\n🎉 İşlem bitti. Dosyalar ExoPlayer / IPTV için hazır.", flush=True)

if __name__ == "__main__":
    main()
