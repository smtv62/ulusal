import asyncio
import subprocess
import sys
from playwright.async_api import async_playwright

# Takip edilecek hedef canlı yayın sayfası
TARGET_URL = "https://www.startv.com.tr/canli-yayin"
Cikis_Dosyasi = "startv_kayit.mp4"

async def get_live_m3u8():
    print("[*] Star TV canlı yayın linki aranıyor...")
    async with async_playwright() as p:
        # GitHub Actions (Linux) üzerinde kararlı çalışması için gerekli argümanlar
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage"
            ]
        )
        
        # İstekleri dinlemek için yeni bir sayfa açıyoruz
        context = await browser.new_context()
        page = await context.new_page()
        
        m3u8_url = None

        # Network isteklerini yakalayan fonksiyon
        async def handle_request(request):
            nonlocal m3u8_url
            url = request.url
            # Star TV'nin dinamik sid içeren 720p veya ana m3u8 akışını yakalıyoruz
            if "startv_720p.m3u8" in url and "sid=" in url:
                m3u8_url = url
                print(f"[+] Yayın Linki Yakalandı: {url[:60]}...")

        # Dinleyiciyi sayfaya bağlıyoruz
        page.on("request", handle_request)
        
        try:
            # Sayfaya git ve network sakinleşene kadar (maksimum 30 saniye) bekle
            await page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
        except Exception as e:
            # Sayfa tamamen yüklenmese bile link geldiyse hata bastırıp devam ediyoruz
            print(f"[!] Sayfa yüklenirken zaman aşımı veya hata oluştu (Yine de kontrol ediliyor): {e}")

        await browser.close()
        return m3u8_url

def start_recording(m3u8_link):
    if not m3u8_link:
        print("[-] HATA: Güncel m3u8 linki bulunamadı! Bot kapatılıyor.")
        sys.exit(1)

    print(f"[+] Kayıt başlatılıyor -> Dosya adı: {Cikis_Dosyasi}")
    
    # streamlink komutu: En iyi kalitede (best) yayını yakalar ve dosyaya yazar
    # HLS akışlarında kopmaları önlemek için canlı yayını taze tutan parametreler eklenmiştir
    komut = [
        "streamlink",
        m3u8_link,
        "best",
        "-o", Cikis_Dosyasi,
        "--hls-live-restart", # Yayına olabildiğince güncel canlı noktadan başla
        "--retry-streams", "5"  # Bağlantı koparsa 5 saniye arayla tekrar dene
    ]
    
    try:
        # Kaydı başlatır. GitHub Actions süresi bitene kadar (6 saat) veya yayın durana kadar çalışır.
        subprocess.run(komut, check=True)
    except KeyboardInterrupt:
        print("[!] Kayıt kullanıcı tarafından durduruldu.")
    except subprocess.CalledProcessError as e:
        print(f"[-] Streamlink hatası: {e}")
        sys.exit(1)

# Ana Çalıştırıcı Bölüm
if __name__ == "__main__":
    # Async fonksiyonu çalıştır ve m3u8 linkini al
    guncel_link = asyncio.run(get_live_m3u8())
    
    # Link bulunduysa kaydı başlat
    start_recording(guncel_link)