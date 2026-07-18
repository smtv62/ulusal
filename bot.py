import asyncio
import sys
from playwright.async_api import async_playwright

# Çıktı dosyamızın yeni adı
CIKIS_DOSYASI = "ulusal.m3u"

# Takip edilecek kanalların listesi (Buraya istediğiniz kadar kanal ekleyebilirsiniz)
KANALLAR = [
    {
        "isim": "Star TV",
        "url": "https://www.startv.com.tr/canli-yayin",
        "anahtar": "startv_720p.m3u8",
        "logo": "https://img-startv.mncdn.com/assets/images/logo.png"
    },
    {
        "isim": "Show TV",
        "url": "https://www.showtv.com.tr/canli-yayin",
        "anahtar": ".m3u8", # Show TV için genel m3u8 uzantısını arıyoruz
        "logo": "https://mo.ciner.com.tr/showtv/iletisim/logo.png"
    }
]

async def get_m3u8_link(browser, kanal):
    print(f"[*] {kanal['isim']} canlı yayın linki aranıyor...")
    
    # Her kanal için temiz ve bağımsız bir sayfa açıyoruz
    context = await browser.new_context()
    page = await context.new_page()
    m3u8_url = None

    # Arka plan network isteklerini dinleyen fonksiyon
    async def handle_request(request):
        nonlocal m3u8_url
        url = request.url
        
        # Link daha önce BULUNMADIYSA ve aranan anahtar kelime URL içindeyse
        # (Ayrıca .ts gibi video parçacıklarını yanlışlıkla almamak için filtreliyoruz)
        if m3u8_url is None and kanal["anahtar"] in url and ".ts" not in url:
            m3u8_url = url

    page.on("request", handle_request)
    
    try:
        # Sayfaya git ve ağ hareketleri durulana kadar maks 30sn bekle
        await page.goto(kanal["url"], wait_until="networkidle", timeout=30000)
    except Exception as e:
        print(f"[!] {kanal['isim']} sayfası tam yüklenemedi (Yine de devam ediliyor): {e}")

    await context.close()
    return m3u8_url

async def main():
    async with async_playwright() as p:
        # Linux / GitHub sunucularında hata vermemesi için argümanlar
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage"
            ]
        )
        
        # M3U dosyasının başlığını oluşturuyoruz
        m3u_icerik = "#EXTM3U\n"
        
        # Listedeki tüm kanalları sırayla gez
        for kanal in KANALLAR:
            link = await get_m3u8_link(browser, kanal)
            
            if link:
                print(f"[+] {kanal['isim']} Linki Yakalandı: {link[:60]}...")
                # Oynatıcılar (IPTV vb.) için standart formatta satırları ekle
                m3u_icerik += f'#EXTINF:-1 tvg-id="{kanal["isim"]}" tvg-name="{kanal["isim"]}" tvg-logo="{kanal["logo"]}" group-title="Ulusal",{kanal["isim"]}\n'
                m3u_icerik += f'{link}\n'
            else:
                print(f"[-] HATA: {kanal['isim']} için m3u8 linki bulunamadı.")
        
        await browser.close()
        
        # Dosyaya kaydetme işlemi
        print(f"\n[+] M3U Dosyası Oluşturuluyor -> {CIKIS_DOSYASI}")
        with open(CIKIS_DOSYASI, "w", encoding="utf-8") as f:
            f.write(m3u_icerik)
            
        print("[+] İşlem tamamlandı, M3U dosyası hazır.")

if __name__ == "__main__":
    asyncio.run(main())
