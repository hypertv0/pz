import re
import os
import json
import time
from playwright.sync_api import sync_playwright

# --- Ayarlar ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def find_working_domain(context):
    print("\n🔍 PapazSports güncel adresi hızlı tarama ile aranıyor...", flush=True)
    
    # 1. Aşama: Hızlı HTTP sinyalleri ile hangi domainin ayakta olduğunu bul (Tarayıcı açmaz)
    active_url = None
    for num in range(1015, 999, -1):
        test_url = f"https://www.papazsports{num}.pro/"
        print(f"Deneyiyor: {test_url:<35}", end="\r", flush=True)
        try:
            # Sadece header çekiyoruz, sayfa yüklemiyoruz (çok hızlıdır)
            with context.request.get(test_url, timeout=3000) as response:
                # Cloudflare 403/503 verse bile bu domain "yaşıyor" demektir
                if response.status in [200, 403, 503]:
                    active_url = test_url
                    print(f"\n✅ Sinyal Alındı: {active_url} (Durum: {response.status})", flush=True)
                    break
        except:
            continue

    if not active_url:
        return None, None

    # 2. Aşama: Sadece bulduğumuz adreste tarayıcıyı açıyoruz
    page = context.new_page()
    try:
        print(f"🚀 Tarayıcı {active_url} adresine giriş yapıyor...", flush=True)
        page.goto(active_url, timeout=30000, wait_until='domcontentloaded')
        
        # Cloudflare/Yönlendirme için bekleme
        page.wait_for_timeout(6000)
        
        final_url = page.url.rstrip('/')
        title = page.title().lower()
        
        if "papazsports" in title or "maç izle" in title:
            print(f"🎯 Giriş Başarılı: {final_url}", flush=True)
            return final_url, page
        else:
            print(f"⚠️ Sayfa başlığı hatalı: {title}", flush=True)
    except Exception as e:
        print(f"⚠️ Tarayıcı hatası: {str(e)}", flush=True)
    
    return None, None

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(user_agent=USER_AGENT)

        domain, page = find_working_domain(context)
        if not domain:
            print("\n❌ Çalışan ana domain bulunamadı.", flush=True)
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

        print("\n🚀 API kanalları çekiliyor...", flush=True)

        for channel_id, name in vip_channels.items():
            print(f"📡 {name:<15}", end=" ", flush=True)
            try:
                # Sitenin içindeki fetch mekanizmasını kullanıyoruz
                fetch_script = f"""
                async () => {{
                    try {{
                        let response = await fetch('/auth.php', {{
                            method: 'POST',
                            headers: {{ 
                                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                'X-Requested-With': 'XMLHttpRequest'
                            }},
                            body: 'channel={channel_id}'
                        }});
                        return await response.text();
                    }} catch (e) {{ return "ERROR:" + e.message; }}
                }}
                """
                
                raw_response = page.evaluate(fetch_script)
                
                if raw_response and "URL" in raw_response:
                    data = json.loads(raw_response)
                    stream_url = data["URL"]
                    token = data["TOKEN"]
                    
                    # Oynatıcı başlıkları (Pipe formatı)
                    final_link = f"{stream_url}|usertoken={token}&pl=PapazSports&Origin={domain}&Referer={domain}/"
                    
                    content = ["#EXTM3U", f'#EXTINF:-1, {name}', final_link]
                    clean_name = name.replace(" ", "_").replace(".", "").replace("-", "_")
                    
                    with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                        f.write("\n".join(content))

                    global_playlist.append(f'#EXTINF:-1, {name}')
                    global_playlist.append(final_link)
                    print("✅", flush=True)
                else:
                    print("❌ (Link Yok)", flush=True)
            except:
                print("⚠️ Hata", flush=True)

        # Playlist Kaydet
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(global_playlist))

        browser.close()
        print("\n🎉 İşlem başarıyla tamamlandı. Dosyalar güncel.")

if __name__ == "__main__":
    main()
