import asyncio
import sys
from playwright.async_api import async_playwright

# Hedef kanal ayarları
TARGET_URL = "https://www.startv.com.tr/canli-yayin"
Cikis_Dosyasi = "startv.m3u"

async def get_live_m3u8():
    print("[*] Star TV canlı yayın linki aranıyor...")
    async with async_playwright() as p:
        # Linux / GitHub sunucularında headless hata vermemesi için gerekli argümanlar
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage"
            ]
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        m3u8_url = None

        # Sayfanın arka planda yaptığı network isteklerini dinliyoruz
        async def handle_request(request):
            nonlocal m3u8_url
            url = request.url
            # Star TV'nin dinamik token içeren m3u8 akışını yakalıyoruz
            if "startv_720p.m3u8" in url and "sid=" in url:
                m3u8_url = url
                print(f"[+] Yayın Linki Yakalandı: {url[:60]}...")

        page.on("request", handle_request)
        
        try:
            # Sayfaya git ve ağ hareketleri durulana kadar maks 30sn bekle
            await page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"[!] Sayfa yüklenirken zaman aşımı (Yine de devam ediliyor): {e}")

        await browser.close()
        return m3u8_url

def m3u_olustur(m3u8_link):
    if not m3u8_link:
        print("[-] HATA: Güncel m3u8 linki bulunamadı! M3U oluşturulamadı.")
        sys.exit(1)

    print(f"[+] M3U Dosyası Oluşturuluyor -> {Cikis_Dosyasi}")
    
    # Standart IPTV oynatıcı formatında M3U içeriği hazırlıyoruz
    m3u_icerik = (
        "#EXTM3U\n"
        "#EXTINF:-1 tvg-id=\"StarTV\" tvg-name=\"Star TV\" tvg-logo=\"https://img-startv.mncdn.com/assets/images/logo.png\" group-title=\"Ulusal\",Star TV\n"
        f"{m3u8_link}\n"
    )
    
    # Dosyaya yazma işlemi
    with open(Cikis_Dosyasi, "w", encoding="utf-8") as f:
        f.write(m3u_icerik)
    
    print("[+] M3U başarıyla kaydedildi.")

if __name__ == "__main__":
    # Linki yakala ve M3U formatında kaydet
    guncel_link = asyncio.run(get_live_m3u8())
    m3u_olustur(guncel_link)
