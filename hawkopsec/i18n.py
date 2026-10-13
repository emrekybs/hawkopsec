"""HawkOpsec — minimal i18n. English source strings, Turkish lookup table."""
import json
import os

_CONFIG_DIR = os.path.expanduser("~/.config/hawkopsec")
_CONFIG = os.path.join(_CONFIG_DIR, "config.json")
_lang = "en"

TR = {
    # ---- navigation -------------------------------------------------------
    "Overview": "Genel Durum", "Network": "Ağ", "Identity": "Kimlik",
    "Hardening": "Sertleştirme", "Leak test": "Sızıntı Testi", "Traces": "İzler",
    "Activity": "Kayıtlar", "Uninstall": "Kaldır", "Console": "Konsol", "Clear": "Temizle",

    # ---- page subtitles ---------------------------------------------------
    "Pick a profile — HawkOpsec resets to baseline, then applies every step itself, including starting Tor.":
        "Bir profil seç — HawkOpsec önce her şeyi sıfırlar, sonra Tor'u başlatmak dahil tüm adımları kendisi uygular.",
    "Anonymity and perimeter: Tor routing, encrypted DNS, inbound firewall.":
        "Anonimlik ve çevre güvenliği: Tor yönlendirme, şifreli DNS, gelen trafik duvarı.",
    "Machine fingerprint: what the local network and the sites you visit can tie back to you.":
        "Makine parmak izi: yerel ağın ve ziyaret ettiğin sitelerin seni tanıyabileceği bilgiler.",
    "Kernel, services and hardware. Every toggle is reverted by Reset system.":
        "Çekirdek, servisler ve donanım. Buradaki her ayarı “Sistemi sıfırla” geri alır.",
    "Forensic hygiene. These are one-shot operations — Reset system does not undo them.":
        "Adli iz temizliği. Bunlar tek seferlik işlemler — “Sistemi sıfırla” bunları geri almaz.",
    "Every change HawkOpsec made to this system, from the helper log.":
        "HawkOpsec'in bu sistemde yaptığı her değişiklik, yardımcı servis kaydından.",
    "Run before every dark-web session. Read-only — nothing on the system changes until you press Fix.":
        "Her dark web oturumundan önce çalıştır. Sadece okur — “Düzelt”e basmadıkça sistemde hiçbir şey değişmez.",

    # ---- groups -----------------------------------------------------------
    "Security profile": "Güvenlik profili", "Live status": "Anlık durum",
    "Network interfaces": "Ağ arayüzleri", "Host identity": "Makine kimliği",
    "Leak tests": "Sızıntı testleri", "Dark-web pre-flight": "Dark web öncesi kontrol",

    # ---- modes ------------------------------------------------------------
    "BASELINE": "Varsayılan", "SECURE": "Güvenli", "PUBLIC": "Halka Açık Ağ",
    "HARDENED": "Sertleştirilmiş", "GHOST": "Hayalet", "PARANOID": "Paranoya",
    "Everything off": "Her şey kapalı", "Daily use": "Günlük kullanım",
    "Untrusted Wi-Fi": "Güvenilmeyen Wi-Fi", "Less fingerprint": "Az parmak izi",
    "Tor + kill-switch": "Tor + ağ kesici", "Tor + RAM wipe": "Tor + RAM silme",
    "Everything off. Reverts all changes and restores your original configuration — identical to Reset system.":
        "Her şey kapalı. Tüm değişiklikleri geri alır ve orijinal yapılandırmanı geri yükler — “Sistemi sıfırla” ile aynı.",
    "Everyday hardening: kernel hardening, default-deny firewall, encrypted DNS (DoT), IPv6 off, no crash reports, logs kept in RAM. No Tor — fully usable for daily work.":
        "Günlük sertleştirme: çekirdek sertleştirme, gelen trafiği reddeden güvenlik duvarı, şifreli DNS (DoT), IPv6 kapalı, çökme raporu yok, kayıtlar RAM'de. Tor yok — günlük işler için tam kullanılabilir.",
    "SECURE plus MAC randomization (incl. persistent via NetworkManager) and Bluetooth off. Built for untrusted / public Wi-Fi. Still no Tor.":
        "Güvenli profil + MAC rastgeleleştirme (NetworkManager ile kalıcı) ve Bluetooth kapalı. Güvenilmeyen / halka açık Wi-Fi için. Yine Tor yok.",
    "PUBLIC plus random machine-id and hostname, swap off and USB lockdown. Strong anti-fingerprinting without routing through Tor.":
        "Halka açık ağ profili + rastgele makine kimliği ve makine adı, swap kapalı, USB kilidi. Tor kullanmadan güçlü parmak izi azaltma.",
    "HARDENED plus UTC timezone, webcam off and system-wide Tor routing with a leak kill-switch. The tool starts Tor for you.":
        "Sertleştirilmiş profil + UTC saat dilimi, kamera kapalı ve sızıntıya karşı ağ kesicili sistem geneli Tor yönlendirme. Tor'u araç kendisi başlatır.",
    "GHOST plus RAM wipe on shutdown (cold-boot mitigation). Maximum protection; heaviest profile.":
        "Hayalet profil + kapanışta RAM silme (soğuk başlatma saldırısına karşı). En yüksek koruma; en ağır profil.",
    "Applying profile: {m}": "Profil uygulanıyor: {m}",
    "Reset to baseline and apply now?": "Önce varsayılana sıfırlanıp şimdi uygulansın mı?",
    "Apply": "Uygula",

    # ---- live status ------------------------------------------------------
    "Connection": "Bağlantı", "Public IP": "Genel IP", "DNS": "DNS",
    "Firewall": "Güvenlik duvarı", "IPv6": "IPv6", "MAC address": "MAC adresi",
    "Machine ID": "Makine kimliği", "Hostname": "Makine adı", "Timezone": "Saat dilimi",
    "Webcam": "Kamera",
    "Tor routed": "Tor üzerinden", "Direct": "Doğrudan", "Via Tor": "Tor üzerinden",
    "Active": "Etkin", "Off": "Kapalı", "Disabled": "Kapalı", "Enabled": "Açık",
    "Spoofed": "Sahte", "Hardware": "Gerçek", "Real": "Gerçek", "System": "Sistem",
    "Available": "Açık", "Unreachable": "Erişilemedi", "checking …": "kontrol ediliyor …",
    "spoofed": "sahte", "hardware ID": "donanım kimliği",

    # ---- buttons ----------------------------------------------------------
    "Check IP": "IP'yi kontrol et", "Run leak test": "Sızıntı testi",
    "Open Tor Browser": "Tor Browser'ı aç", "Reset system": "Sistemi sıfırla",
    "Panic": "Panik", "Refresh": "Yenile", "Restore": "Geri al",
    "Randomize": "Rastgele yap", "Clean": "Temizle", "Select files": "Dosya seç",
    "Run": "Çalıştır", "Run all checks": "Tüm kontrolleri çalıştır", "Fix": "Düzelt",
    "Forget": "Unut",

    # ---- network ----------------------------------------------------------
    "Tor transparent proxy": "Tor şeffaf vekil sunucu",
    "Route all TCP and DNS through Tor with a kill-switch, IPv6 block and per-destination stream isolation.":
        "Tüm TCP ve DNS trafiğini Tor'dan geçirir; ağ kesici, IPv6 engeli ve hedef başına ayrı devre.",
    "DNS-over-TLS": "Şifreli DNS (DoT)",
    "Encrypt DNS via systemd-resolved (ignored while Tor routing is on).":
        "DNS sorgularını systemd-resolved ile şifreler (Tor açıkken devre dışı).",
    "Firewall — default-deny inbound": "Güvenlik duvarı — gelen trafiği reddet",
    "Drop all unsolicited inbound; keep established/related.":
        "İstenmeyen tüm gelen bağlantıları düşürür; kurulmuş bağlantılar çalışmaya devam eder.",
    "Disable IPv6": "IPv6'yı kapat",
    "Remove a common deanonymization leak path system-wide.":
        "Kimliği açığa çıkaran yaygın bir sızıntı yolunu sistem genelinde kapatır.",
    "Harden Firefox": "Firefox'u sertleştir",
    "Write a user.js: WebRTC, WebGL and geolocation off, resistFingerprinting on. Tor Browser is still the real fix for browser fingerprinting.":
        "user.js yazar: WebRTC, WebGL ve konum kapalı, parmak izi direnci açık. Tarayıcı parmak izi için asıl çözüm yine Tor Browser.",
    "DNS / IP leak test": "DNS / IP sızıntı testi",
    "Check which resolvers see your queries and whether your real IP or IPv6 escapes the tunnel.":
        "Sorgularını hangi DNS sunucularının gördüğünü, gerçek IP'nin ya da IPv6'nın tünelden kaçıp kaçmadığını kontrol eder.",

    # ---- identity ---------------------------------------------------------
    "Force timezone to UTC": "Saat dilimini UTC'ye sabitle",
    "Report UTC everywhere to shrink your locale fingerprint.":
        "Her yerde UTC bildirerek konum parmak izini küçültür.",
    "Persistent MAC (NetworkManager)": "Kalıcı MAC (NetworkManager)",
    "Randomize MAC on every connect via NetworkManager, so it survives reconnects.":
        "Her bağlantıda MAC'i NetworkManager ile rastgele yapar; yeniden bağlanınca da korunur.",

    # ---- hardening --------------------------------------------------------
    "Kernel / sysctl hardening": "Çekirdek (sysctl) sertleştirme",
    "rp_filter, no redirects, SYN cookies, kptr/dmesg restrict, ptrace_scope=2, full ASLR.":
        "rp_filter, yönlendirme kabulü yok, SYN cookies, kptr/dmesg kısıtlama, ptrace_scope=2, tam ASLR.",
    "Disable crash reporting": "Çökme raporlarını kapat",
    "Set systemd-coredump Storage=none and stop any apport/whoopsie services.":
        "systemd-coredump'ı Storage=none yapar, apport/whoopsie servislerini durdurur.",
    "Keep journald in RAM": "Sistem kayıtlarını RAM'de tut",
    "System logs stay in memory, never on disk.": "Sistem kayıtları belleğe yazılır, diske asla.",
    "Disable Bluetooth": "Bluetooth'u kapat",
    "rfkill-block Bluetooth to remove a wireless attack surface.":
        "Bluetooth'u rfkill ile engeller, kablosuz saldırı yüzeyini kaldırır.",
    "Disable webcam": "Kamerayı kapat",
    "Unload the UVC camera driver and block it from loading again.":
        "UVC kamera sürücüsünü kaldırır ve yeniden yüklenmesini engeller.",
    "Disable swap": "Swap'ı kapat",
    "swapoff to stop secrets and keys leaking to disk.":
        "Parolaların ve anahtarların diske sızmaması için swap'ı kapatır.",
    "USB lockdown": "USB kilidi",
    "Block newly-connected USB devices (BadUSB defense); existing stay working.":
        "Yeni takılan USB aygıtlarını engeller (BadUSB savunması); takılı olanlar çalışır.",
    "RAM wipe on shutdown": "Kapanışta RAM silme",
    "Drop caches, swapoff and wipe memory at shutdown (cold-boot mitigation).":
        "Kapanışta önbelleği boşaltır, swap'ı kapatır ve belleği siler (soğuk başlatma saldırısına karşı).",

    # ---- traces -----------------------------------------------------------
    "Clean user traces": "Kullanıcı izlerini temizle",
    "Shell history, recent files, thumbnails and trash in your home.":
        "Ev dizinindeki komut geçmişi, son dosyalar, küçük resimler ve çöp kutusu.",
    "Clean system traces": "Sistem izlerini temizle",
    "Vacuum journald, wipe coredumps, login records and package cache.":
        "Sistem kayıtlarını boşaltır; çökme dökümlerini, giriş kayıtlarını ve paket önbelleğini siler.",
    "Strip file metadata": "Dosya üst verisini sil",
    "Remove EXIF and other metadata from selected files (mat2 or exiftool).":
        "Seçili dosyalardan EXIF ve diğer üst verileri kaldırır (mat2 veya exiftool).",
    "Secure delete": "Güvenli silme",
    "Overwrite then delete selected files so they can't be recovered. On SSDs this is best-effort — full-disk encryption is the real protection.":
        "Seçili dosyaların üzerine yazıp siler, geri getirilemez. SSD'lerde garanti değildir — asıl koruma tam disk şifrelemedir.",
    "Select files to strip metadata": "Üst verisi silinecek dosyaları seç",
    "Select files to shred": "Kalıcı silinecek dosyaları seç",
    "Permanently shred the selected item(s)? This cannot be undone.":
        "Seçili öğeler kalıcı olarak silinsin mi? Bu işlem geri alınamaz.",
    "No changes recorded yet. Applied actions will appear here with timestamps.":
        "Henüz kayıt yok. Uygulanan işlemler burada saatleriyle görünecek.",

    # ---- leak test page ---------------------------------------------------
    "Not run yet": "Henüz çalıştırılmadı", "Not run yet.": "Henüz çalıştırılmadı.",
    "Takes 10–30 seconds; uses bash.ws for the DNS test.":
        "10–30 saniye sürer; DNS testi için bash.ws kullanılır.",
    "Running …": "Çalışıyor …", "Checking …": "Kontrol ediliyor …",
    "Audit failed": "Denetim başarısız",
    "Ready": "Hazır", "Risky — review the warnings": "Riskli — uyarıları gözden geçir",
    "Not ready": "Hazır değil",
    "{p} of {t} checks passed · {f} failed · {w} warnings · {ts}":
        "{t} kontrolden {p} tanesi geçti · {f} hata · {w} uyarı · {ts}",
    "Your real ISP is remembered as a name + salted hash (never the raw IP) while in BASELINE, so leaks can be recognised later.":
        "Gerçek internet sağlayıcın, Varsayılan moddayken ad + tuzlu özet olarak saklanır (IP'nin kendisi asla); böylece sonraki sızıntılar tanınabilir.",
    "Saved ISP fingerprint deleted.": "Kayıtlı sağlayıcı parmak izi silindi.",
    "PASS": "TAMAM", "WARN": "UYARI", "FAIL": "HATA", "INFO": "BİLGİ", "SKIP": "ATLANDI",

    # check titles
    "Exit IP": "Çıkış IP", "DNS leak": "DNS sızıntısı", "IPv6 leak": "IPv6 sızıntısı",
    "Kill-switch (UDP)": "Ağ kesici (UDP)", ".onion resolution": ".onion çözümleme",
    "Tor service": "Tor servisi", "Tor Browser": "Tor Browser",
    "WebRTC (Firefox)": "WebRTC (Firefox)", "Clock sync": "Saat eşitleme",
    "Open ports": "Açık portlar", "Identity-linked apps": "Kimliğe bağlı uygulamalar",
    "Disk encryption": "Disk şifreleme", "Swap": "Swap", "Session user": "Oturum kullanıcısı",
    "VPN": "VPN",

    # check details
    "Could not reach any IP service: {err}": "Hiçbir IP servisine ulaşılamadı: {err}",
    "Your REAL IP is visible while Tor mode is on: {where}":
        "Tor modu açıkken GERÇEK IP'n görünüyor: {where}",
    "Traffic exits through Tor: {where}": "Trafik Tor üzerinden çıkıyor: {where}",
    "Tor status could not be verified: {where}": "Tor durumu doğrulanamadı: {where}",
    "Tor mode is on but the exit is NOT a Tor relay: {where}":
        "Tor modu açık ama çıkış noktası bir Tor düğümü DEĞİL: {where}",
    "Direct connection — this IP is visible to every site: {where}":
        "Doğrudan bağlantı — bu IP her siteye görünür: {where}",
    "DNS leak test service unreachable: {err}": "DNS sızıntı test servisine ulaşılamadı: {err}",
    "No resolver reached the test server — DNS may be broken.":
        "Test sunucusuna hiçbir DNS sunucusu ulaşmadı — DNS çalışmıyor olabilir.",
    "Your real ISP's resolver answered: {servers}":
        "Gerçek internet sağlayıcının DNS sunucusu yanıt verdi: {servers}",
    "Queries go to your ISP's resolver in plain text: {servers}":
        "Sorgular şifresiz olarak sağlayıcının DNS sunucusuna gidiyor: {servers}",
    "Resolvers seen: {servers}. Run a check once in BASELINE so HawkOpsec can recognise your real ISP.":
        "Görülen DNS sunucuları: {servers}. Gerçek sağlayıcını tanıyabilmesi için bir kez Varsayılan modda kontrol çalıştır.",
    "No resolver belongs to your ISP: {servers}":
        "Hiçbir DNS sunucusu senin sağlayıcına ait değil: {servers}",
    "No global IPv6 address — nothing can leak over IPv6.":
        "Genel IPv6 adresi yok — IPv6 üzerinden sızıntı olamaz.",
    "Global IPv6 present on {ifs} but outbound IPv6 is blocked.":
        "{ifs} üzerinde genel IPv6 var ama giden IPv6 trafiği engelli.",
    "IPv6 traffic bypasses Tor/VPN and exposes {ip6}. Disable IPv6.":
        "IPv6 trafiği Tor/VPN'i atlıyor ve {ip6} adresini açığa çıkarıyor. IPv6'yı kapat.",
    "Only meaningful while Tor routing is on.": "Sadece Tor yönlendirme açıkken anlamlı.",
    "A UDP packet left the machine outside Tor (NTP reply received).":
        "Bir UDP paketi Tor dışından makineden çıktı (NTP yanıtı alındı).",
    "Non-Tor UDP is dropped by the kill-switch.": "Tor dışı UDP trafiği ağ kesici tarafından düşürülüyor.",
    "Only tested in Tor mode — resolving .onion without Tor leaks it to your ISP.":
        "Sadece Tor modunda test edilir — Tor olmadan .onion çözümlemek adresi sağlayıcına sızdırır.",
    ".onion names do not resolve through Tor: {err}": ".onion adresleri Tor üzerinden çözümlenmiyor: {err}",
    ".onion names are mapped by Tor ({ip}).": ".onion adresleri Tor tarafından eşleniyor ({ip}).",
    ".onion resolved outside Tor's virtual range ({ip}).": ".onion, Tor'un sanal aralığı dışında çözümlendi ({ip}).",
    "tor.service running, SOCKS 127.0.0.1:9050 open.": "tor.service çalışıyor, SOCKS 127.0.0.1:9050 açık.",
    "Tor mode is on but the Tor service is not answering.": "Tor modu açık ama Tor servisi yanıt vermiyor.",
    "System Tor is not running.": "Sistem Tor'u çalışmıyor.",
    "Not installed. Use Tor Browser for .onion — never a normal browser.":
        "Kurulu değil. .onion için Tor Browser kullan — asla normal bir tarayıcı değil.",
    "Installed but never started — open it once, then set Security Level to Safest.":
        "Kurulu ama hiç açılmamış — bir kez aç, sonra Güvenlik Düzeyini “En Güvenli” yap.",
    "Installed, Security Level: {lvl} (JavaScript off).": "Kurulu, Güvenlik Düzeyi: {lvl} (JavaScript kapalı).",
    "Security Level is {lvl}. Set it to Safest before visiting .onion sites.":
        "Güvenlik Düzeyi: {lvl}. .onion sitelere girmeden önce “En Güvenli” yap.",
    "Safest": "En Güvenli", "Safer": "Daha Güvenli", "Standard": "Standart",
    "No Firefox profile found.": "Firefox profili bulunamadı.",
    "WebRTC can reveal your real IP in {n} profile(s). Use “Harden Firefox”.":
        "{n} profilde WebRTC gerçek IP'ni açığa çıkarabilir. “Firefox'u sertleştir”i kullan.",
    "WebRTC disabled in every Firefox profile.": "WebRTC tüm Firefox profillerinde kapalı.",
    "System clock reports UTC.": "Sistem saati UTC bildiriyor.",
    "Timezone is {tz} — it narrows down your location. Force UTC.":
        "Saat dilimi {tz} — bu konumunu daraltır. UTC'ye sabitle.",
    "Clock is NTP-synchronised (Tor rejects skewed clocks).":
        "Saat NTP ile eşitli (Tor kaymış saatleri reddeder).",
    "Clock is not synchronised — Tor may fail and skew is a fingerprint.":
        "Saat eşitli değil — Tor bağlanamayabilir ve saat kayması bir parmak izidir.",
    "Randomized ({h}).": "Rastgele ({h}).",
    "Real hostname “{h}” is broadcast on the LAN (DHCP, mDNS).":
        "Gerçek makine adı “{h}” yerel ağa yayınlanıyor (DHCP, mDNS).",
    "Hardware MAC is hidden.": "Donanım MAC adresi gizli.",
    "Hardware MAC is visible to the local network / Wi-Fi operator.":
        "Donanım MAC adresi yerel ağa / Wi-Fi sahibine görünüyor.",
    "Inbound default-deny is active.": "Gelen trafiği reddetme kuralı etkin.",
    "No HawkOpsec firewall is active.": "HawkOpsec güvenlik duvarı etkin değil.",
    "No service listens on a network interface.": "Ağ arayüzünü dinleyen servis yok.",
    "Services reachable from the network: {ports}": "Ağdan erişilebilen servisler: {ports}",
    "Close these before the session: {apps}": "Oturumdan önce bunları kapat: {apps}",
    "No messenger / sync / remote-desktop app is running.":
        "Mesajlaşma / eşitleme / uzak masaüstü uygulaması çalışmıyor.",
    "No camera device available.": "Kullanılabilir kamera aygıtı yok.",
    "{n} camera device(s) active. Disable the webcam or cover it.":
        "{n} kamera aygıtı etkin. Kamerayı kapat ya da üstünü kapat.",
    "A LUKS/dm-crypt volume is in use.": "LUKS/dm-crypt şifreli birim kullanılıyor.",
    "No encrypted volume found — a seized disk exposes everything.":
        "Şifreli birim bulunamadı — el konulan bir disk her şeyi açığa çıkarır.",
    "lsblk not available.": "lsblk bulunamadı.",
    "No unencrypted swap on disk.": "Diskte şifresiz swap yok.",
    "Unencrypted swap ({dev}) can write RAM contents to disk.":
        "Şifresiz swap ({dev}) bellek içeriğini diske yazabilir.",
    "HawkOpsec GUI is running as root — browse as a normal user.":
        "HawkOpsec arayüzü root olarak çalışıyor — normal kullanıcıyla gezin.",
    "Running as an unprivileged user.": "Yetkisiz (normal) kullanıcıyla çalışıyor.",
    "VPN interface up: {ifs}. Tor runs on top of it.": "VPN arayüzü açık: {ifs}. Tor bunun üzerinden çalışır.",
    "No VPN — your ISP can see that you connect to Tor (use bridges if that matters).":
        "VPN yok — sağlayıcın Tor'a bağlandığını görebilir (önemliyse köprü kullan).",

    # ---- errors from backend.explain_error -------------------------------
    "DNS resolution failed (network or resolver not ready)":
        "DNS çözümlenemedi (ağ ya da DNS henüz hazır değil)",
    "timed out": "zaman aşımı",
    "connection refused (Tor/firewall blocking?)": "bağlantı reddedildi (Tor/güvenlik duvarı engelliyor olabilir)",
    "connection reset (endpoint blocked or Tor circuit dropped)":
        "bağlantı sıfırlandı (adres engelli ya da Tor devresi düştü)",
    "no network": "ağ yok",

    # ---- console / action labels -----------------------------------------
    "HawkOpsec ready. Actions request elevation via polkit.":
        "HawkOpsec hazır. İşlemler polkit üzerinden yetki ister.",
    "Done.": "Tamamlandı.",
    "Checking exit IP": "Çıkış IP'si kontrol ediliyor",
    "IP check failed": "IP kontrolü başarısız",
    "Tor confirmed": "Tor doğrulandı", "NOT via Tor": "Tor üzerinden DEĞİL",
    "Tor status unknown": "Tor durumu bilinmiyor",
    "Tor": "Tor", "DNS restore": "DNS geri alma", "Persistent MAC": "Kalıcı MAC",
    "System clean": "Sistem temizliği", "Strip metadata": "Üst veri silme",
    "Anonymous browser": "Anonim tarayıcı", "Mode": "Mod", "Baseline reset": "Varsayılana sıfırlama",
    "Kernel hardening": "Çekirdek sertleştirme", "IPv6 off": "IPv6 kapalı",
    "Crash reporting off": "Çökme raporu kapalı", "journald volatile": "Kayıtlar RAM'de",
    "Bluetooth off": "Bluetooth kapalı", "Swap off": "Swap kapalı",
    "Machine-ID": "Makine kimliği", "Timezone UTC": "Saat dilimi UTC", "Tor routing": "Tor yönlendirme", "RAM wipe": "RAM silme",

    # ---- confirms ---------------------------------------------------------
    "Revert every change and return to the original state?":
        "Tüm değişiklikler geri alınıp orijinal duruma dönülsün mü?",
    "Cut all network, kill sensitive apps and drop caches now?":
        "Tüm ağ bağlantısı kesilsin, hassas uygulamalar kapatılsın ve önbellek boşaltılsın mı?",
    "Uninstall HawkOpsec": "HawkOpsec'i kaldır",
    "Revert all changes and remove HawkOpsec completely? The app will close.":
        "Tüm değişiklikler geri alınıp HawkOpsec tamamen kaldırılsın mı? Uygulama kapanacak.",
    "Uninstalling — reverting changes and removing files …":
        "Kaldırılıyor — değişiklikler geri alınıyor, dosyalar siliniyor …",

    # ---- browser / traces (v2) -------------------------------------------
    "Browser": "Tarayıcı", "System": "Sistem", "Open": "Aç",
    "RAM browser": "RAM tarayıcı", "RAM-only browser": "Sadece RAM'de çalışan tarayıcı",
    "Firefox with a throw-away profile in memory: history, cookies, cache and sessions never touch the disk and the profile is deleted on close.":
        "Bellekte geçici bir profille Firefox: geçmiş, çerez, önbellek ve oturumlar diske hiç yazılmaz; kapatınca profil silinir.",
    "Clean browser traces": "Tarayıcı izlerini temizle",
    "History, cookies, cache, sessions, site storage and form data of Firefox and Chromium-family browsers. Bookmarks and saved passwords are kept.":
        "Firefox ve Chromium tabanlı tarayıcıların geçmişi, çerezleri, önbelleği, oturumları, site depolaması ve form verileri. Yer imleri ve kayıtlı parolalar korunur.",
    "Delete history, cookies, cache and sessions of all browsers? Bookmarks and saved passwords are kept. Close your browsers first.":
        "Tüm tarayıcıların geçmişi, çerezleri, önbelleği ve oturumları silinsin mi? Yer imleri ve kayıtlı parolalar korunur. Önce tarayıcıları kapat.",
    "Firefox: wipe on close": "Firefox: kapanınca temizle", "Firefox wipe on close": "Firefox kapanınca temizle",
    "Make your normal Firefox delete history, cookies, cache and form data every time it closes, and stop writing the cache to disk.":
        "Normal Firefox'un her kapanışta geçmişi, çerezleri, önbelleği ve form verilerini silmesini ve önbelleği diske yazmamasını sağlar.",
    "Clear clipboard": "Panoyu temizle",
    "Copied .onion links, addresses and passwords stay in the clipboard until overwritten. Panic clears it too.":
        "Kopyalanan .onion bağlantıları, adresler ve parolalar üzerine yazılana kadar panoda kalır. Panik de panoyu temizler.",
    "Vacuum journald, flush the DNS cache, wipe coredumps, login records and package cache.":
        "Sistem kayıtlarını boşaltır, DNS önbelleğini temizler; çökme dökümlerini, giriş kayıtlarını ve paket önbelleğini siler.",
    "Browser history on disk": "Diskteki tarayıcı geçmişi",
    "No browsing history stored by regular browsers.": "Normal tarayıcılarda kayıtlı gezinti geçmişi yok.",
    "Regular browsers keep history on disk ({where}). Clean it or use the RAM-only browser.":
        "Normal tarayıcılar geçmişi diskte tutuyor ({where}). Temizle ya da RAM tarayıcıyı kullan.",
    "Every Firefox profile clears history, cookies and cache on close.":
        "Tüm Firefox profilleri kapanışta geçmişi, çerezleri ve önbelleği siliyor.",
    "{n} Firefox profile(s) keep history and cookies after closing.":
        "{n} Firefox profili kapandıktan sonra geçmişi ve çerezleri tutuyor.",
    "System helper not installed — privileged actions are disabled.":
        "Sistem yardımcısı kurulu değil — yetki gerektiren işlemler kapalı.",
    "Finish installation": "Kurulumu tamamla",
    "HawkOpsec needs to install its root helper, polkit policy and menu entry once (same as: sudo hawkopsec-setup). Do it now?":
        "HawkOpsec'in bir kereye mahsus root yardımcısını, polkit kuralını ve menü kaydını kurması gerekiyor (sudo hawkopsec-setup ile aynı). Şimdi kurulsun mu?",
    "System setup": "Sistem kurulumu",
}


def load_lang():
    global _lang
    try:
        _lang = json.load(open(_CONFIG)).get("lang", "en")
    except (OSError, json.JSONDecodeError):
        _lang = "en"


def set_lang(l):
    global _lang
    _lang = l
    try:
        os.makedirs(_CONFIG_DIR, exist_ok=True)
        json.dump({"lang": l}, open(_CONFIG, "w"))
    except OSError:
        pass


def lang():
    return _lang


def mode_label(name):
    """Profile names: Turkish from the table, English in title case."""
    if _lang == "tr" and name in TR:
        return TR[name]
    return name.capitalize()


def tr(s):
    if _lang == "tr" and s in TR:
        return TR[s]
    return s
