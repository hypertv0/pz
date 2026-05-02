import re
import sys
import os
from playwright.sync_api import sync_playwright

# --- Ayarlar ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"

def find_working_domain(context):
    print("\n🔍 Çalışan PapazSports domaini aranıyor...", flush=True)
    
    # 1. Hızlı Tarama: Eski yönlendiricilere (1000 vb.) takılmamak için TERS YÖNDE (1025 -> 1000) tarıyoruz!
    for num in range(1025, 999, -1):
        test_url = f"https://www.papazsports{num}.pro/"
        print(f"Deneyiyor (Hızlı Tarama): {test_url:<35}", end="\r", flush=True)
        
        try:
            response = context.request.get(test_url, timeout=3000)
            
            if response.status in[200, 403, 503]:
                print(f"\n✅ Sunucu yanıt verdi: {test_url} - Şimdi tarayıcıda açılıyor...", flush=True)
                
                page = context.new_page()
                context.add_cookies([{"name": "puShown", "value": "1", "url": test_url}])
                
                try:
                    page.goto(test_url, timeout=20000, wait_until='domcontentloaded')
                except Exception as e:
                    print(f"⚠️ Sayfa tam yüklenemedi ancak işleme devam ediliyor...", flush=True)
                
                page.wait_for_timeout(4000)
                
                title = page.title().lower()
                if "cloudflare" in title or "just a moment" in title or "bekleyin" in title:
                    print("⏳ Cloudflare koruması saptandı, tam olarak geçilmesi bekleniyor...", flush=True)
                    page.wait_for_timeout(8000)
                    title = page.title().lower()
                
                if "papazsports" in title and not any(x in title for x in["cloudflare", "just a moment"]):
                    # Yönlendirme (Redirect) yapılmışsa GÜNCEL linki adres çubuğundan al!
                    final_url = page.url.rstrip('/')
                    print(f"🎯 Gerçek Güncel Adres Tespit Edildi: {final_url}", flush=True)
                    return final_url, page
                else:
                    print("⚠️ Bu adres sadece bir yönlendirici veya kapalı, atlanıyor...", flush=True)
                    page.close()
                
        except Exception:
            pass
            
    return None, None

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 720}
        )

        domain, page = find_working_domain(context)
        if not domain:
            print("\n❌ Çalışan ana domain bulunamadı.", flush=True)
            return

        print("⏳ Arka plan işlemleri için site API'si hazırlanıyor...", flush=True)
        page.wait_for_timeout(2000)

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
        global_playlist =["#EXTM3U"]

        for channel_id, (name, tvg_id) in vip_channels.items():
            print(f"📡 Çekiliyor: {name:<20} (ID: {channel_id})...", end=" ", flush=True)
            try:
                js_fetch_code = """
                async (chan_id) => {
                    try {
                        const formData = new URLSearchParams();
                        formData.append('channel', chan_id);
                        const response = await fetch('/auth.php', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                'X-Requested-With': 'XMLHttpRequest',
                                'Accept': '*/*'
                            },
                            body: formData.toString()
                        });
                        const text = await response.text();
                        try {
                            return JSON.parse(text);
                        } catch (e) {
                            return { error: 'Gelen Yanıt JSON değil: ' + text.substring(0, 40) };
                        }
                    } catch (e) {
                        return { error: e.message };
                    }
                }
                """
                
                # Parametreyi dışarıdan güvenle gönderiyoruz
                data = page.evaluate(js_fetch_code, channel_id)
                
                if data and "URL" in data and "TOKEN" in data:
                    stream_url = data["URL"]
                    token = data["TOKEN"]
                    
                    # Oynatıcıların istediği başlıklar (Origin ve Referer eklendi)
                    pipe_headers = f"usertoken={token}&pl=PapazSports&Origin={domain}&Referer={domain}/"
                    final_url = f"{stream_url}|{pipe_headers}"

                    content =[
                        "#EXTM3U",
                        f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
                        f"#EXTVLCOPT:http-user-agent={USER_AGENT}",
                        f"#EXTVLCOPT:http-referrer={domain}/",
                        final_url
                    ]

                    clean_name = re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")
                    with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                        f.write("\n".join(content))

                    global_playlist.extend(content[1:])
                    print("✅ Bulundu", flush=True)
                    
                elif data and "error" in data:
                    print(f"❌ (Hata: {data['error']})", flush=True)
                else:
                    print("❌ (Geçersiz Yanıt)", flush=True)
                    
            except Exception as e:
                print(f"⚠️ Hata oluştu", flush=True)

        for key, (name, tvg_id, url) in direct_channels.items():
            print(f"📡 Ekleniyor: {name:<20} (Şifresiz)... ✅", flush=True)
            content =[
                "#EXTM3U",
                f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
                f"#EXTVLCOPT:http-user-agent={USER_AGENT}",
                url
            ]
            clean_name = re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")
            with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                f.write("\n".join(content))
            global_playlist.extend(content[1:])

        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(global_playlist))

        browser.close()
        print("\n🎉 İşlem bitti! Canlı maçlar ExoPlayer ve Tivimate için m3u formatına döküldü.", flush=True)

if __name__ == "__main__":
    main()
