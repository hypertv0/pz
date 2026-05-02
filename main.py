import re
import os
import json
import time
from playwright.sync_api import sync_playwright

# --- Ayarlar ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"

def find_working_domain(context):
    print("\n🔍 Çalışan PapazSports domaini aranıyor...", flush=True)
    # Senin istediğin o eski, basit tarama aralığı ve mantığı
    for num in range(1000, 1020):
        test_url = f"https://www.papazsports{num}.pro/"
        page = context.new_page()
        try:
            print(f"Deneniyor: {test_url}", flush=True)
            # Sayfaya git ve sadece yanıtın gelmesini bekle
            response = page.goto(test_url, timeout=15000, wait_until='domcontentloaded')
            
            # İşte o meşhur çalışan kontrol satırı:
            if response and response.ok:
                final_url = page.url.rstrip('/')
                # Cloudflare kontrolü
                if not any(x in page.title().lower() for x in ["cloudflare", "just a moment", "bekleyin"]):
                    print(f"✅ BULUNDU: {final_url}", flush=True)
                    return final_url, page
            
            page.close()
        except:
            page.close()
            pass
    return None, None

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)

        domain, page = find_working_domain(context)
        
        if not domain:
            print("❌ Domain bulunamadı.", flush=True)
            return

        # Kanallar (Gönderdiğin HTML kodundaki ID'lere göre tam liste)
        channels = {
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

        print(f"\n📡 {domain} üzerinden yayın linkleri toplanıyor...", flush=True)

        for channel_id, name in channels.items():
            print(f"📡 Çekiliyor: {name:<15}", end=" ", flush=True)
            try:
                # Sitenin kendi içinden (evaluate) auth.php'ye kanal ID'sini soruyoruz
                # Bu yöntem ağ trafiği dinlemekten çok daha garantidir
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
                    
                    # Oynatıcıların (Tivimate/ExoPlayer) yayını açması için gereken başlıklar
                    final_link = f"{m3u8_url}|usertoken={token}&pl=PapazSports&Referer={domain}/"

                    content = [
                        "#EXTM3U",
                        f'#EXTINF:-1 tvg-id="{name}" tvg-name="{name}",{name}',
                        final_link
                    ]

                    # Dosyaya Kaydet
                    clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
                    with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                        f.write("\n".join(content))

                    # Genel Listeye Ekle
                    global_playlist.append(f'#EXTINF:-1 tvg-id="{name}" tvg-name="{name}",{name}')
                    global_playlist.append(final_link)
                    
                    print("✅", flush=True)
                else:
                    print("❌", flush=True)
            except:
                print("⚠️ Hata", flush=True)

        # Genel Playlisti Kaydet
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(global_playlist))

        browser.close()
        print("\n🎉 İşlem bitti. Tüm m3u8 dosyaları güncellendi.", flush=True)

if __name__ == "__main__":
    main()
