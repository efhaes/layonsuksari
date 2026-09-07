from django.contrib.auth.models import User
from django.db import models
from django.core.validators import RegexValidator
import re
import requests

class DesaEncryptionKey(models.Model):
    public_key_jwk = models.TextField(help_text="JWK public key RSA-OAEP, format JSON.")
    wrapped_private_key = models.TextField(
        help_text="JSON: {ciphertext, iv, salt, iterations} — private key terenkripsi passphrase harian kantor."
    )
    wrapped_private_key_recovery = models.TextField(
        help_text="JSON: {ciphertext, iv, salt, iterations} — private key terenkripsi kode pemulihan kantor."
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kunci Enkripsi Kantor Desa"
        verbose_name_plural = "Kunci Enkripsi Kantor Desa"

    def __str__(self):
        return "Kunci Kantor Desa"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.filter(pk=1).first()


class UserEncryptionKey(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='encryption_key')
    public_key_jwk = models.TextField(help_text="JWK public key RSA-OAEP milik warga, format JSON.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Kunci — {self.user.username}"


class ChatThread(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chat_thread')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    warga_typing_at = models.DateTimeField(null=True, blank=True)
    staff_typing_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Chat — {self.user.username}"

class ChatMessage(models.Model):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages')
    pengirim = models.ForeignKey(User, on_delete=models.CASCADE)

    ciphertext = models.TextField(help_text="AES-GCM ciphertext, base64.")
    iv = models.CharField(max_length=32, help_text="IV AES-GCM (12 byte), base64.")
    wrapped_key_warga = models.TextField(help_text="AES key dibungkus public key warga, base64.")
    wrapped_key_desa = models.TextField(help_text="AES key dibungkus public key Kantor Desa, base64.")

    dibaca_staff = models.BooleanField(default=False)
    dibaca_warga = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Pesan #{self.pk} — thread {self.thread_id}"

    
STATUS_CHOICES = [
    ('diajukan', 'Diajukan'),
    ('diproses', 'Sedang Diproses'),
    ('ditolak', 'Ditolak'),
    ('selesai', 'Sudah Diproses'),
]


def resolve_maps_embed_url(share_url):
    try:
        resp = requests.get(
            share_url,
            allow_redirects=True,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0 (compatible; VillageSiteBot/1.0)"},
        )
        final_url = resp.url
    except requests.RequestException:
        return None

    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
    if not match:
        match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', final_url)

    if not match:
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', resp.text or "")
        if not match:
            match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', resp.text or "")

    if not match:
        return None

    lat, lng = match.group(1), match.group(2)
    return f"https://maps.google.com/maps?q={lat},{lng}&z=16&output=embed"

class TentangDesa(models.Model):
    sejarah_singkat = models.TextField(
        help_text="Cerita asal-usul nama desa, sejarah singkat, dll."
    )
    potensi_kearifan_lokal = models.TextField(
        help_text="Potensi alam, sosial-budaya, ekonomi desa."
    )
    lokasi_embed_url = models.URLField(
        blank=True, null=True,
        help_text="Paste link share dari Google Maps (klik tombol Bagikan di Maps, "
                   "copy link-nya). Contoh: https://maps.app.goo.gl/xxxxxxx"
    )
    lokasi_embed_cache = models.URLField(
        blank=True, null=True, editable=False,
        help_text="Auto-generated dari lokasi_embed_url, jangan diedit manual.",
    )
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tentang Desa"
        verbose_name_plural = "Tentang Desa"

    def __str__(self):
        return "Tentang Desa Sukasari"

    def save(self, *args, **kwargs):
        self.pk = 1  # singleton

        try:
            old = TentangDesa.objects.get(pk=1)
        except TentangDesa.DoesNotExist:
            old = None

        url_changed = (old is None) or (old.lokasi_embed_url != self.lokasi_embed_url)
        cache_missing = not self.lokasi_embed_cache

        if not self.lokasi_embed_url:
            self.lokasi_embed_cache = ""
        elif url_changed or cache_missing:
            resolved = resolve_maps_embed_url(self.lokasi_embed_url)
            if resolved:
                self.lokasi_embed_cache = resolved
            elif url_changed:
                self.lokasi_embed_cache = ""

        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={"sejarah_singkat": "", "potensi_kearifan_lokal": ""}
        )
        return obj

class VisiItem(models.Model):
    tentang = models.ForeignKey(TentangDesa, related_name="visi_items", on_delete=models.CASCADE)
    teks = models.CharField(max_length=255)
    urutan = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["urutan"]
        verbose_name = "Poin Visi"
        verbose_name_plural = "Poin Visi"

    def __str__(self):
        return self.teks


class MisiItem(models.Model):
    tentang = models.ForeignKey(TentangDesa, related_name="misi_items", on_delete=models.CASCADE)
    teks = models.CharField(max_length=255)
    urutan = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["urutan"]
        verbose_name = "Poin Misi"
        verbose_name_plural = "Poin Misi"

    def __str__(self):
        return self.teks

from django.core.exceptions import ValidationError

class StrukturOrganisasi(models.Model):
    class Slot(models.TextChoices):
        BPD = "bpd", "B.P.D"
        KEPALA_DESA = "kepala_desa", "Kepala Desa"
        SEKRETARIS_DESA = "sekretaris_desa", "Sekretaris Desa"
        KASI_PEMERINTAHAN = "kasi_pemerintahan", "Kasi Pemerintahan"
        KASI_KESEJAHTERAAN = "kasi_kesejahteraan", "Kasi Kesejahteraan"
        KASI_PELAYANAN = "kasi_pelayanan", "Kasi Pelayanan"
        KAUR_TATAUSAHADANUMUM = "kaur_tatausahadannumum", "Kaur Tata Usaha dan Umum"
        KAUR_KEUANGAN = "kaur_keuangan", "Kaur Keuangan"
        KAUR_PERENCANAAN = "kaur_perencanaan", "Kaur Perencanaan"
        KEPALA_WILAYAH = "kepala_wilayah", "Kepala Dusun"

    SLOT_SINGLETON = {
        Slot.BPD, Slot.KEPALA_DESA, Slot.SEKRETARIS_DESA,
        Slot.KASI_PEMERINTAHAN, Slot.KASI_KESEJAHTERAAN, Slot.KASI_PELAYANAN,
        Slot.KAUR_TATAUSAHADANUMUM, Slot.KAUR_KEUANGAN, Slot.KAUR_PERENCANAAN,
    }
    nama = models.CharField(max_length=100)
    jabatan = models.CharField(max_length=100)
    foto = models.ImageField(upload_to="struktur_organisasi/", blank=True, null=True)
    slot = models.CharField(max_length=30, choices=Slot.choices)
    urutan = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["slot", "urutan"]
        verbose_name = "Struktur Organisasi"
        verbose_name_plural = "Struktur Organisasi"

    def clean(self):
        if self.slot in self.SLOT_SINGLETON:
            bentrok = StrukturOrganisasi.objects.filter(slot=self.slot).exclude(pk=self.pk).exists()
            if bentrok:
                raise ValidationError({"slot": f"Slot '{self.get_slot_display()}' cuma boleh diisi 1 orang."})

    def __str__(self):
        return f"{self.nama} — {self.get_slot_display()}"

class ProfilDesa(models.Model):
    foto = models.ImageField(upload_to='profil_desa/', verbose_name="Foto Kantor Desa")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Foto Kantor Desa"
        verbose_name_plural = "Foto Kantor Desa"

    def __str__(self):
        return "Foto Kantor Desa Sukasari"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

NIK_VALIDATOR = RegexValidator(
    r'^[1-9]\d{15}$',
    message="NIK harus terdiri dari 16 digit angka dan tidak boleh diawali nol"
)
WHATSAPP_VALIDATOR = RegexValidator(
    regex=r'^(?:\+62|62|08)\d{8,13}$',
    message="Nomor WhatsApp harus diawali +62, 62, atau 08 dan terdiri dari 10–15 digit angka"
)

class SuratKematian(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_jenazah = models.CharField(max_length=100)
    nik_jenazah = models.CharField(max_length=16)
    tanggal_kematian = models.DateField()
    tempat_kematian = models.CharField(max_length=100)
    penyebab_kematian = models.CharField(max_length=255, blank=True, null=True)
    nama_pelapor = models.CharField(max_length=100)
    nik_pelapor = models.CharField(max_length=16)
    hubungan_pelapor = models.CharField(max_length=100)
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")
    fotokopi_ktp_jenazah = models.FileField(upload_to='syarat/kematian/ktp_jenazah/', verbose_name="Fotokopi KTP Almarhum/Almarhumah")
    fotokopi_kk = models.FileField(upload_to='syarat/kematian/kk/', verbose_name="Fotokopi Kartu Keluarga")
    surat_keterangan_kematian = models.FileField(upload_to='syarat/kematian/keterangan_kematian/', verbose_name="Surat Keterangan Kematian dari Dokter/Rumah Sakit")
    surat_pengantar_rt_rw = models.FileField(upload_to='syarat/kematian/pengantar_rt_rw/', verbose_name="Surat Pengantar RT/RW")
    fotokopi_ktp_pelapor = models.FileField(upload_to='syarat/kematian/ktp_pelapor/', verbose_name="Fotokopi KTP Pelapor")
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='diajukan')
    hasil_surat = models.FileField(upload_to='hasil_surat/akta_kematian/', blank=True, null=True)

    alasan_penolakan = models.TextField(blank=True, null=True, verbose_name="Alasan Penolakan")

    def __str__(self):
        return f"{self.nama_jenazah} - {self.nik_jenazah}"

class SuratKelahiran(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_lengkap = models.CharField(max_length=100)
    tempat_lahir = models.CharField(max_length=100)
    tanggal_lahir = models.DateField()
    jenis_kelamin = models.CharField(max_length=10, choices=[('L', 'Laki-laki'), ('P', 'Perempuan')])
    nama_ayah = models.CharField(max_length=100)
    nama_ibu = models.CharField(max_length=100)
    alamat = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")
    alasan_penolakan = models.TextField(blank=True, null=True, verbose_name="Alasan Penolakan")
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    surat_keterangan_lahir = models.FileField(upload_to='syarat/kelahiran/surat_keterangan/', verbose_name="Surat Keterangan Lahir dari RS/Bidan")
    fotokopi_ktp_kk = models.FileField(upload_to='syarat/kelahiran/ktp_kk/', verbose_name="Fotokopi KTP dan KK Orang Tua")
    fotokopi_buku_nikah = models.FileField(upload_to='syarat/kelahiran/buku_nikah/', verbose_name="Fotokopi Buku Nikah Orang Tua")
    surat_pengantar_rt_rw = models.FileField(upload_to='syarat/kelahiran/pengantar_rt_rw/', verbose_name="Surat Pengantar RT/RW")
    hasil_surat = models.FileField(upload_to='hasil_surat/akta_kelahiran/', blank=True, null=True)

    def __str__(self):
        return f'Akta Kelahiran {self.nama_lengkap}'

class DomisiliUsaha(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_pemilik = models.CharField(max_length=100)
    nik_pemilik = models.CharField(max_length=16)
    nama_usaha = models.CharField(max_length=100)
    jenis_usaha = models.CharField(max_length=100)
    alamat_usaha = models.CharField(max_length=100)
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")
    alasan_penolakan = models.TextField(blank=True, null=True, verbose_name="Alasan Penolakan")
    nib = models.FileField(upload_to='domisili_usaha/nib/', verbose_name="NIB")
    fotokopi_ktp = models.FileField(upload_to='domisili_usaha/KTP/', verbose_name="Fotokopi KTP")
    surat_pengantar_rt_rw = models.FileField(upload_to='domisili_usaha/pengantar_rt_rw/', verbose_name="Surat Pengantar RT/RW")
    fotokopi_kk = models.FileField(upload_to='domisili_usaha/KK/', verbose_name="Fotokopi KK")
    foto_lokasi_usaha = models.FileField(upload_to='domisili_usaha/foto_lokasi/', verbose_name="Foto Lokasi Usaha")
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    hasil_surat = models.FileField(upload_to='hasil_surat/domisili_usaha/', blank=True, null=True)

    def __str__(self):
        return f"Domisili Usaha - {self.nama_usaha} ({self.nama_pemilik})"

class PindahDatang(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama = models.CharField(max_length=100)
    nik = models.CharField(max_length=16)
    asal_daerah = models.CharField(max_length=100)
    tujuan_daerah = models.CharField(max_length=100)
    tanggal_pindah = models.DateField()
    alasan_pindah = models.CharField(max_length=200)
    kk_lama = models.FileField(upload_to='pindah_datang/kk_lama/')
    ktp = models.FileField(upload_to='pindah_datang/ktp/')
    surat_pengantar = models.FileField(upload_to='pindah_datang/surat_pengantar/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    hasil_surat = models.FileField(upload_to='hasil_surat/pindah_datang/', blank=True, null=True)
    alasan_penolakan = models.TextField(blank=True, null=True, verbose_name="Alasan Penolakan")

    def __str__(self):
        return f"Pindah Datang - {self.nama} ({self.nik})"

class SKTMPengajuan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_lengkap = models.CharField(max_length=100)
    alamat_lengkap = models.CharField(max_length=200)
    nik = models.CharField(max_length=16)
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")
    surat_pengantar = models.FileField(upload_to='sktm/surat_pengantar/', verbose_name="Surat Pengantar RT/RW")
    foto_ktp = models.ImageField(upload_to='sktm/foto_ktp/', verbose_name="Fotokopi KTP")
    foto_kk = models.ImageField(upload_to='sktm/foto_kk/', verbose_name="Fotokopi Kartu Keluarga")
    surat_pernyataan = models.FileField(upload_to='sktm/surat_pernyataan/', verbose_name="Surat Pernyataan Tidak Mampu")
    surat_keterangan_sekolah = models.FileField(upload_to='sktm/keterangan_sekolah/', blank=True, null=True, verbose_name="Surat Keterangan Sekolah")
    surat_keterangan_usaha = models.FileField(upload_to='sktm/keterangan_usaha/', blank=True, null=True, verbose_name="Surat Keterangan Usaha / NIB")
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    hasil_surat = models.FileField(upload_to='sktm/hasil_surat/', blank=True, null=True)
    alasan_penolakan = models.TextField(blank=True, null=True, verbose_name="Alasan Penolakan")

    def __str__(self):
        return f"SKTM - {self.nama_lengkap} ({self.nik})"

class DomisiliPengajuan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_lengkap = models.CharField(max_length=100)
    alamat_lengkap = models.CharField(max_length=200)
    nik = models.CharField(max_length=16)
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")
    surat_pengantar = models.FileField(upload_to='domisili/surat_pengantar/')
    foto_ktp = models.ImageField(upload_to='domisili/foto_ktp/')
    foto_kk = models.ImageField(upload_to='domisili/foto_kk/')
    surat_permohonan = models.FileField(upload_to='domisili/surat_permohonan/')
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    hasil_surat = models.FileField(upload_to='domisili/hasil_surat/', blank=True, null=True)
    alasan_penolakan = models.TextField(blank=True, null=True, verbose_name="Alasan Penolakan")

    def __str__(self):
        return f"{self.nama_lengkap} - {self.nik}"

class SKUPengajuan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_lengkap = models.CharField(max_length=100)
    alamat_lengkap = models.CharField(max_length=200)
    nik = models.CharField(max_length=16)
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")
    npwp = models.CharField(max_length=50, blank=True, null=True)
    surat_pengantar = models.FileField(upload_to='SKU/surat_pengantar/')
    surat_permohonan = models.FileField(upload_to='SKU/surat_permohonan/')
    foto_ktp = models.ImageField(upload_to='SKU/foto_ktp/')
    foto_kk = models.ImageField(upload_to='SKU/foto_kk/')
    surat_kuasa = models.ImageField(upload_to='SKU/surat_kuasa/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    hasil_surat = models.FileField(upload_to='SKU/hasil_surat/', blank=True, null=True)
    alasan_penolakan = models.TextField(blank=True, null=True, verbose_name="Alasan Penolakan")
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.npwp:
            self.npwp = self.nik
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nama_lengkap} - {self.nik}"

class SuratKTPBaruPengantar(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_lengkap = models.CharField(max_length=100)
    alamat_lengkap = models.CharField(max_length=200)
    foto_kk = models.ImageField(upload_to='ktp_baru/foto_kk/', verbose_name="Foto Kartu Keluarga")
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    hasil_surat = models.FileField(upload_to='hasil_surat/ktp_baru/', blank=True, null=True)
    alasan_penolakan = models.TextField(blank=True, null=True, verbose_name="Alasan Penolakan")

    def __str__(self):
        return f"KTP Baru - {self.nama_lengkap}"

class SuratKKPengantar(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_lengkap = models.CharField(max_length=100)
    nik = models.CharField(max_length=16)
    alamat = models.CharField(max_length=200)
    foto_kk = models.ImageField(upload_to='kk_pengantar/foto_kk/', verbose_name="Foto Kartu Keluarga")
    ijazah = models.FileField(upload_to='kk_pengantar/ijazah/', blank=True, null=True, verbose_name="Ijazah (Jika ubah status pendidikan)")
    surat_kelahiran = models.FileField(upload_to='kk_pengantar/surat_kelahiran/', blank=True, null=True, verbose_name="Surat Kelahiran (Jika tambah anggota keluarga)")
    surat_kematian = models.FileField(upload_to='kk_pengantar/surat_kematian/', blank=True, null=True, verbose_name="Surat Kematian (Jika kurangi anggota keluarga)")
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    hasil_surat = models.FileField(upload_to='hasil_surat/kk_pengantar/', blank=True, null=True)
    alasan_penolakan = models.TextField(blank=True, null=True, verbose_name="Alasan Penolakan")

    def __str__(self):
        return f"Pengantar KK - {self.nama_lengkap} ({self.nik})"

class SuratLainnya(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nik = models.CharField(max_length=20)
    nama_lengkap = models.CharField(max_length=100)
    alamat_lengkap = models.CharField(max_length=200)
    foto_ktp = models.ImageField(upload_to='surat_lainnya/')
    foto_kk = models.ImageField(upload_to='surat_lainnya/')
    jenis_pengajuan = models.CharField(max_length=100, default="Surat Lainnya")
    keterangan = models.CharField(max_length=500)
    no_whatsapp = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    alasan_penolakan = models.TextField(blank=True, null=True, verbose_name="Alasan Penolakan")
    hasil_surat = models.FileField(upload_to='surat_lainnya/hasil/', blank=True, null=True)

    def __str__(self):
        return f"{self.nama_lengkap} - {self.nik}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nama = models.CharField(max_length=100)
    alamat = models.CharField(max_length=100)
    no_whatsapp = models.CharField(max_length=15, blank=True, default='', verbose_name="No. WhatsApp")

    def __str__(self):
        return self.nama

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.CharField(max_length=300)
    published_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_at']
        verbose_name = "Pengumuman"
        verbose_name_plural = "Pengumuman"

class AnnouncementImage(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='announcement_images/')

    def __str__(self):
        return f"Gambar untuk {self.announcement.title}"