"""HawkOpsec — minimal i18n. English source strings, Turkish lookup table."""
import json
import os

_CONFIG_DIR = os.path.expanduser("~/.config/hawkopsec")
_CONFIG = os.path.join(_CONFIG_DIR, "config.json")
_lang = "en"

TR = {
    # nav
    "DASHBOARD": "PANO", "NETWORK": "AĞ", "IDENTITY": "KİMLİK",
    "HARDENING": "SERTLEŞTİRME", "TRACES": "İZLER", "ACTIVITY": "GÜNLÜK",
    # section eyebrows + titles
    "system status": "sistem durumu", "Operations Board": "Operasyon Panosu",
    "anonymity & perimeter": "anonimlik & çevre", "Network": "Ağ",
    "machine fingerprint": "makine parmak izi", "Identity": "Kimlik",
    "kernel · services · hardware": "çekirdek · servis · donanım",
    "Hardening": "Sertleştirme",
    "forensic hygiene": "adli hijyen", "Traces": "İzler",
    "change log": "değişiklik günlüğü", "Activity": "Günlük",
    # group labels
    "security mode": "güvenlik modu", "live status": "canlı durum",
    "operations": "işlemler", "network interfaces — MAC": "ağ arayüzleri — MAC",
    "host identity": "makine kimliği",
    # dashboard
    "One tap applies a full profile — the tool starts Tor and everything else itself.":
        "Tek dokunuş tüm profili uygular — Tor'u ve gerisini araç kendi başlatır.",
    # status labels
    "CONNECTION": "BAĞLANTI", "PUBLIC IP": "GENEL IP", "DNS": "DNS",
    "FIREWALL": "GÜVENLİK DUVARI", "IPV6": "IPV6", "MAC": "MAC",
    "MACHINE-ID": "MAKİNE-ID", "BLUETOOTH": "BLUETOOTH",
    # status values
    "TOR ROUTED": "TOR ÜZERİNDEN", "DIRECT": "DOĞRUDAN", "VIA TOR": "TOR İLE",
    "ACTIVE": "AKTİF", "OFF": "KAPALI", "DISABLED": "DEVRE DIŞI",
    "ENABLED": "AÇIK", "SPOOFED": "SAHTE", "HARDWARE": "DONANIM",
    "REAL": "GERÇEK", "BLOCKED": "ENGELLİ", "ON": "AÇIK", "SYSTEM": "SİSTEM",
    "UNREACHABLE": "ERİŞİLEMEDİ", "hardware id": "donanım kimliği",
    # buttons
    "CHECK IP": "IP KONTROL", "ANON BROWSER": "ANON TARAYICI",
    "RESET SYSTEM": "SIFIRLA", "PANIC": "PANİK", "REFRESH": "YENİLE",
    "APPLY": "UYGULA", "RESTORE": "GERİ AL", "RANDOMIZE": "RASTGELE",
    "CLEAN": "TEMİZLE", "SELECT": "SEÇ",
    # network rows
    "Tor transparent proxy": "Tor şeffaf proxy",
    "Route all TCP through Tor with a kill-switch, IPv6 block and per-destination stream isolation.":
        "Tüm TCP'yi Tor'a yönlendirir; kill-switch, IPv6 bloğu ve hedef-başına devre izolasyonu.",
    "DNS-over-TLS": "DNS-over-TLS",
    "Encrypt DNS via systemd-resolved (ignored while Tor routing is on).":
        "systemd-resolved ile şifreli DNS (Tor açıkken yok sayılır).",
    "Firewall — default-deny inbound": "Güvenlik duvarı — gelen varsayılan-reddet",
    "Drop all unsolicited inbound; keep established/related.":
        "İstenmeyen tüm gelen bağlantıları düşürür; kurulu/ilişkili olanları tutar.",
    "Disable IPv6": "IPv6'yı kapat",
    "Remove a common deanonymization leak path system-wide.":
        "Yaygın bir kimlik-açığa-çıkarma sızıntı yolunu sistem genelinde kaldırır.",
    "Harden Firefox (WebRTC off, anti-fingerprint)":
        "Firefox sertleştir (WebRTC kapalı, parmak izi karşıtı)",
    "Write a user.js: disable WebRTC, resistFingerprinting, WebGL and geo. Tor Browser is still the real fix for browser fingerprinting.":
        "user.js yazar: WebRTC, WebGL, geo kapalı + resistFingerprinting. Tarayıcı parmak izi için asıl çözüm yine Tor Browser.",
    # identity
    "Hostname": "Makine adı", "Machine-ID": "Makine-ID",
    "Force timezone to UTC": "Saat dilimini UTC'ye zorla",
    "Report UTC everywhere to shrink your locale fingerprint.":
        "Her yerde UTC bildirerek yerel parmak izini küçültür.",
    "Persistent MAC (NetworkManager)": "Kalıcı MAC (NetworkManager)",
    "Randomize MAC on every connect via NetworkManager, so it survives reconnects.":
        "Her bağlanışta NetworkManager ile MAC'i rastgeleleştirir; yeniden bağlanmada da kalır.",
    # hardening
    "Kernel / sysctl hardening": "Çekirdek / sysctl sertleştirme",
    "rp_filter, no redirects, SYN cookies, kptr/dmesg restrict, ptrace_scope=2, full ASLR.":
        "rp_filter, redirect yok, SYN cookies, kptr/dmesg kısıtlama, ptrace_scope=2, tam ASLR.",
    "Disable crash reporting": "Çökme raporlamayı kapat",
    "Set systemd-coredump Storage=none and stop any apport/whoopsie services.":
        "systemd-coredump Storage=none yapar, apport/whoopsie servislerini durdurur.",
    "journald to RAM (volatile)": "journald'i RAM'e al (volatile)",
    "Keep system logs in memory, not on disk.":
        "Sistem loglarını diske değil bellekte tutar.",
    "Disable Bluetooth": "Bluetooth'u kapat",
    "rfkill-block Bluetooth to remove a wireless attack surface.":
        "Kablosuz saldırı yüzeyini kaldırmak için Bluetooth'u rfkill ile engeller.",
    "Disable swap": "Swap'ı kapat",
    "swapoff to stop secrets and keys leaking to disk.":
        "Sırların ve anahtarların diske sızmasını engellemek için swapoff.",
    "USB lockdown": "USB kilidi",
    "Block newly-connected USB devices (BadUSB defense); existing stay working.":
        "Yeni takılan USB'leri engeller (BadUSB savunması); takılı olanlar çalışır.",
    "RAM wipe on shutdown": "Kapanışta RAM temizliği",
    "Drop caches, swapoff and wipe memory at shutdown (cold-boot mitigation).":
        "Kapanışta cache boşaltır, swapoff yapar ve belleği siler (cold-boot önlemi).",
    # traces
    "Clean user traces": "Kullanıcı izlerini temizle",
    "Shell history, recent files, thumbnails and trash in your home.":
        "Ev dizinindeki shell geçmişi, son dosyalar, küçük resimler ve çöp.",
    "Clean system traces": "Sistem izlerini temizle",
    "Vacuum journald, wipe coredumps, login records and package cache.":
        "journald'i boşaltır; coredump, giriş kayıtları ve paket cache'ini siler.",
    "Strip file metadata (EXIF)": "Dosya meta verisini sil (EXIF)",
    "Remove EXIF/metadata from selected files (mat2 or exiftool).":
        "Seçili dosyalardan EXIF/meta veriyi kaldırır (mat2 veya exiftool).",
    "Secure-delete (shred)": "Güvenli sil (shred)",
    "Overwrite then delete selected files/folders so they can't be recovered.":
        "Seçili dosya/klasörlerin üzerine yazıp siler; geri getirilemez.",
    "One-shot operations — not reverted by RESET.":
        "Tek seferlik işlemler — SIFIRLA bunları geri almaz.",
    # activity
    "No changes recorded yet. Applied actions will appear here with timestamps.":
        "Henüz kayıt yok. Uygulanan işlemler zaman damgasıyla burada görünecek.",
    # greeting + confirms
    "HawkOpsec ready. Actions request elevation via polkit.":
        "HawkOpsec hazır. İşlemler polkit ile yetki ister.",
    "Reset system": "Sistemi sıfırla",
    "Revert every change and return to the original state?":
        "Tüm değişiklikleri geri alıp orijinal duruma dönülsün mü?",
    "Panic": "Panik",
    "Cut all network, kill sensitive apps and drop caches now?":
        "Tüm ağ kesilsin, hassas uygulamalar kapatılsın ve cache boşaltılsın mı?",
    "Reset to baseline and apply now?":
        "Baz duruma sıfırlayıp şimdi uygulansın mı?",
    "Secure delete": "Güvenli sil",
    "Apply": "Uygula",
    "Select files to strip metadata": "Meta verisi silinecek dosyaları seç",
    "Select files to shred": "Parçalanacak (shred) dosyaları seç",
    "Permanently shred the selected item(s)? This cannot be undone.":
        "Seçili öğeler kalıcı olarak parçalanacak (shred) — geri alınamaz. Devam?",
    # mode descriptions
    "Everything off. Reverts all changes and restores your original configuration — identical to RESET SYSTEM.":
        "Her şey kapalı. Tüm değişiklikleri geri alır, orijinal yapılandırmayı geri yükler — SIFIRLA ile aynı.",
    "Everyday hardening: kernel hardening, default-deny firewall, encrypted DNS (DoT), IPv6 off, no crash reports, logs kept in RAM. No Tor — fully usable for daily work.":
        "Günlük sertleştirme: çekirdek sertleştirme, varsayılan-reddet güvenlik duvarı, şifreli DNS (DoT), IPv6 kapalı, çökme raporu yok, loglar RAM'de. Tor yok — günlük kullanıma uygun.",
    "SECURE plus MAC randomization (incl. persistent via NetworkManager) and Bluetooth off. Built for untrusted / public wifi. Still no Tor.":
        "GÜVENLİ + MAC rastgeleleştirme (NetworkManager ile kalıcı dahil) ve Bluetooth kapalı. Güvenilmez/halka açık wifi için. Yine Tor yok.",
    "PUBLIC plus random machine-id and hostname, swap off and USB lockdown. Strong anti-fingerprinting without routing through Tor.":
        "AÇIK + rastgele machine-id ve makine adı, swap kapalı ve USB kilidi. Tor'suz güçlü parmak izi karşıtı.",
    "HARDENED plus UTC timezone and system-wide Tor routing with a leak kill-switch. Full anonymity — the tool starts Tor for you.":
        "SERT + UTC saat dilimi ve sistem geneli Tor yönlendirme + kill-switch. Tam anonimlik — Tor'u araç senin için başlatır.",
    "GHOST plus RAM wipe on shutdown (cold-boot mitigation). Maximum protection; heaviest profile.":
        "HAYALET + kapanışta RAM temizliği (cold-boot önlemi). Maksimum koruma; en ağır profil.",
    # mode display names (short)
    "BASELINE": "BAZ", "SECURE": "GÜVENLİ", "PUBLIC": "AÇIK",
    "HARDENED": "SERT", "GHOST": "HAYALET", "PARANOID": "PARANOYA",
    # console words + action labels
    "Done.": "Bitti.",
    "Tor": "Tor", "Firewall": "Güvenlik duvarı", "IPv6": "IPv6",
    "DNS restore": "DNS geri al", "Timezone": "Saat dilimi",
    "NM MAC": "Kalıcı MAC", "System clean": "Sistem temizliği",
    "Strip metadata": "Meta veri sil", "Anonymous browser": "Anonim tarayıcı",
    "Harden Firefox": "Firefox sertleştir", "IP check": "IP kontrol",
    "Mode": "Mod", "Baseline reset": "Baz sıfırlama",
    "Kernel hardening": "Çekirdek sertleştirme", "IPv6 off": "IPv6 kapalı",
    "Crash reporting off": "Çökme raporu kapalı", "journald volatile": "journald RAM",
    "Persistent MAC": "Kalıcı MAC", "Bluetooth off": "Bluetooth kapalı",
    "Swap off": "Swap kapalı", "USB lockdown": "USB kilidi",
    "Timezone UTC": "Saat dilimi UTC", "Tor routing": "Tor yönlendirme",
    "RAM wipe": "RAM temizliği",
    "Checking exit IP …": "Çıkış IP kontrol ediliyor …",
    "IP check failed": "IP kontrol başarısız",
    "Exit IP": "Çıkış IP", "Tor confirmed": "Tor doğrulandı",
    "NOT via Tor": "Tor DEĞİL",
    # in-app uninstaller
    "UNINSTALL": "KALDIR",
    "Uninstall HawkOpsec": "HawkOpsec'i kaldır",
    "Revert all changes and remove HawkOpsec completely? The app will close.":
        "Tüm değişiklikler geri alınıp HawkOpsec tamamen kaldırılsın mı? Uygulama kapanacak.",
    "Uninstalling — reverting changes and removing files …":
        "Kaldırılıyor — değişiklikler geri alınıyor ve dosyalar siliniyor …",

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


def tr(s):
    if _lang == "tr" and s in TR:
        return TR[s]
    return s
