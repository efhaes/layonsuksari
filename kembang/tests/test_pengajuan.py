from io import BytesIO
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from kembang.models import (
    DomisiliPengajuan,
    DomisiliUsaha,
    PindahDatang,
    SKTMPengajuan,
    SKUPengajuan,
    SuratKelahiran,
    SuratKematian,
    SuratKKPengantar,
    SuratKTPBaruPengantar,
    SuratLainnya,
)


def image_upload(name="dokumen.png"):
    image = Image.new("RGB", (2, 2), color="white")
    content = BytesIO()
    image.save(content, format="PNG")
    return SimpleUploadedFile(name, content.getvalue(), content_type="image/png")


def file_upload(name="dokumen.pdf", content=b"%PDF-1.4 test"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="sukasari-test-media-"))
class PengajuanTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.warga = User.objects.create_user(
            username="3201010101010101",
            password="WargaPass123!",
        )
        cls.warga_lain = User.objects.create_user(
            username="3201010101010102",
            password="WargaPass123!",
        )
        cls.staff = User.objects.create_user(
            username="staff-pengajuan",
            password="StaffPass123!",
            is_staff=True,
        )

    def setUp(self):
        self.client.force_login(self.warga)

    def cases(self):
        return {
            "kematian": {
                "route": "pengajuan_akta_kematian",
                "model": SuratKematian,
                "detail": "detail_pengajuan_akta_kematian",
                "delete": "hapus_kematian",
                "data": {
                    "nama_jenazah": "Almarhum Satu",
                    "nik_jenazah": "3201010101010001",
                    "tanggal_kematian": "2024-01-01",
                    "tempat_kematian": "Bogor",
                    "penyebab_kematian": "Sakit",
                    "nama_pelapor": "Pelapor Satu",
                    "nik_pelapor": "3201010101010002",
                    "hubungan_pelapor": "Anak",
                    "no_whatsapp": "081234567890",
                    "fotokopi_ktp_jenazah": file_upload("ktp.pdf"),
                    "fotokopi_kk": file_upload("kk.pdf"),
                    "surat_keterangan_kematian": file_upload("keterangan.pdf"),
                    "surat_pengantar_rt_rw": file_upload("pengantar.pdf"),
                    "fotokopi_ktp_pelapor": file_upload("pelapor.pdf"),
                },
            },
            "kelahiran": {
                "route": "pengajuan_akta_kelahiran",
                "model": SuratKelahiran,
                "detail": "detail_pengajuan_kelahiran",
                "delete": "hapus_kelahiran",
                "data": {
                    "nama_lengkap": "Bayi Satu",
                    "tempat_lahir": "Bogor",
                    "tanggal_lahir": "2024-01-01",
                    "jenis_kelamin": "L",
                    "nama_ayah": "Ayah Satu",
                    "nama_ibu": "Ibu Satu",
                    "alamat": "Alamat Satu",
                    "no_whatsapp": "081234567890",
                    "surat_keterangan_lahir": file_upload("lahir.pdf"),
                    "fotokopi_ktp_kk": file_upload("ktpkk.pdf"),
                    "fotokopi_buku_nikah": file_upload("nikah.pdf"),
                    "surat_pengantar_rt_rw": file_upload("pengantar.pdf"),
                },
            },
            "pindah": {
                "route": "pengajuan_pindah_datang",
                "model": PindahDatang,
                "detail": "detail_pengajuan_pindah_datang",
                "delete": "hapus_pindah_datang",
                "data": {
                    "nama": "Warga Pindah",
                    "nik": "3201010101010003",
                    "asal_daerah": "Bogor",
                    "tujuan_daerah": "Depok",
                    "tanggal_pindah": "2024-01-01",
                    "alasan_pindah": "Pekerjaan",
                    "no_whatsapp": "081234567890",
                    "kk_lama": file_upload("kk-lama.pdf"),
                    "ktp": file_upload("ktp.pdf"),
                    "surat_pengantar": file_upload("pengantar.pdf"),
                },
            },
            "skdu": {
                "route": "pengajuan_skdu",
                "model": DomisiliUsaha,
                "detail": "detail_skdu",
                "delete": "hapus_domisili_usaha",
                "data": {
                    "nama_pemilik": "Pemilik Usaha",
                    "nik_pemilik": "3201010101010004",
                    "nama_usaha": "Usaha Satu",
                    "jenis_usaha": "Perdagangan",
                    "alamat_usaha": "Alamat Usaha",
                    "no_whatsapp": "081234567890",
                    "nib": file_upload("nib.pdf"),
                    "fotokopi_ktp": file_upload("ktp.pdf"),
                    "surat_pengantar_rt_rw": file_upload("pengantar.pdf"),
                    "fotokopi_kk": file_upload("kk.pdf"),
                    "foto_lokasi_usaha": image_upload("lokasi.png"),
                },
            },
            "sktm": {
                "route": "pengajuan_sktm",
                "model": SKTMPengajuan,
                "detail": "detail_pengajuan_sktm",
                "delete": "hapus_sktm",
                "data": {
                    "nama_lengkap": "Warga SKTM",
                    "alamat_lengkap": "Alamat SKTM",
                    "nik": "3201010101010005",
                    "no_whatsapp": "081234567890",
                    "surat_pengantar": file_upload("pengantar.pdf"),
                    "foto_ktp": image_upload("ktp.png"),
                    "foto_kk": image_upload("kk.png"),
                    "surat_pernyataan": file_upload("pernyataan.pdf"),
                },
            },
            "domisili": {
                "route": "pengajuan_domisili",
                "model": DomisiliPengajuan,
                "detail": "detail_pengajuan_domisili",
                "delete": "hapus_domisili",
                "data": {
                    "nama_lengkap": "Warga Domisili",
                    "alamat_lengkap": "Alamat Domisili",
                    "nik": "3201010101010006",
                    "no_whatsapp": "081234567890",
                    "surat_pengantar": file_upload("pengantar.pdf"),
                    "foto_ktp": image_upload("ktp.png"),
                    "foto_kk": image_upload("kk.png"),
                    "surat_permohonan": file_upload("permohonan.pdf"),
                },
            },
            "sku": {
                "route": "pengajuan_sku",
                "model": SKUPengajuan,
                "detail": "detail_pengajuan_sku",
                "delete": "hapus_sku",
                "data": {
                    "nama_lengkap": "Warga SKU",
                    "alamat_lengkap": "Alamat SKU",
                    "nik": "3201010101010007",
                    "no_whatsapp": "081234567890",
                    "npwp": "",
                    "surat_pengantar": file_upload("pengantar.pdf"),
                    "surat_permohonan": file_upload("permohonan.pdf"),
                    "foto_ktp": image_upload("ktp.png"),
                    "foto_kk": image_upload("kk.png"),
                },
            },
            "ktp": {
                "route": "pengajuan_ktp",
                "model": SuratKTPBaruPengantar,
                "detail": "detail_pengajuan_ktp",
                "delete": "hapus_ktp",
                "data": {
                    "nama_lengkap": "Warga KTP",
                    "alamat_lengkap": "Alamat KTP",
                    "no_whatsapp": "081234567890",
                    "foto_kk": image_upload("kk.png"),
                },
            },
            "kk": {
                "route": "pengajuan_kk",
                "model": SuratKKPengantar,
                "detail": "detail_pengajuan_kk",
                "delete": "hapus_kk",
                "data": {
                    "nama_lengkap": "Warga KK",
                    "nik": "3201010101010008",
                    "alamat": "Alamat KK",
                    "no_whatsapp": "081234567890",
                    "foto_kk": image_upload("kk.png"),
                },
            },
            "lainnya": {
                "route": "pengajuan_surat_lainnya",
                "model": SuratLainnya,
                "detail": "detail_surat_lainnya",
                "delete": "hapus_surat_lainnya",
                "data": {
                    "nik": "3201010101010009",
                    "nama_lengkap": "Warga Lainnya",
                    "alamat_lengkap": "Alamat Lainnya",
                    "foto_ktp": image_upload("ktp.png"),
                    "foto_kk": image_upload("kk.png"),
                    "no_whatsapp": "081234567890",
                    "jenis_pengajuan": "Surat Belum Menikah",
                    "keterangan": "Keperluan administrasi",
                },
            },
        }

    def fresh_data(self, data):
        result = {}
        for key, value in data.items():
            if isinstance(value, SimpleUploadedFile):
                result[key] = SimpleUploadedFile(
                    value.name,
                    value.read(),
                    content_type=value.content_type,
                )
            else:
                result[key] = value
        return result

    def test_all_ten_submission_types_create_with_initial_status(self):
        for name, case in self.cases().items():
            with self.subTest(name=name):
                response = self.client.post(
                    reverse(case["route"]),
                    self.fresh_data(case["data"]),
                )
                self.assertEqual(response.status_code, 302)
                obj = case["model"].objects.get(user=self.warga)
                self.assertEqual(obj.status, "diajukan")

    def test_all_ten_submission_types_reject_missing_required_field(self):
        for name, case in self.cases().items():
            with self.subTest(name=name):
                data = self.fresh_data(case["data"])
                required_field = next(
                    field for field, value in data.items() if value not in ("", None)
                )
                data.pop(required_field)
                response = self.client.post(reverse(case["route"]), data)
                self.assertEqual(response.status_code, 200)
                self.assertFalse(case["model"].objects.filter(user=self.warga).exists())

    def test_active_duplicate_submission_is_rejected_for_all_types(self):
        for name, case in self.cases().items():
            with self.subTest(name=name):
                first = self.client.post(
                    reverse(case["route"]),
                    self.fresh_data(case["data"]),
                )
                self.assertEqual(first.status_code, 302)
                second = self.client.post(
                    reverse(case["route"]),
                    self.fresh_data(case["data"]),
                )
                self.assertEqual(second.status_code, 302)
                self.assertEqual(case["model"].objects.filter(user=self.warga).count(), 1)

    def test_staff_can_read_update_and_delete_each_submission_type(self):
        self.client.force_login(self.staff)
        for name, case in self.cases().items():
            with self.subTest(name=name):
                obj = case["model"].objects.create(user=self.warga, **self.fresh_data(case["data"]))
                detail = reverse(case["detail"], args=[obj.pk])
                response = self.client.get(detail)
                self.assertEqual(response.status_code, 200)
                response = self.client.post(
                    detail,
                    {"status": "selesai", "hasil_surat": file_upload("hasil.pdf")},
                )
                self.assertEqual(response.status_code, 302)
                obj.refresh_from_db()
                self.assertEqual(obj.status, "selesai")
                self.assertTrue(obj.hasil_surat)
                response = self.client.post(reverse(case["delete"], args=[obj.pk]))
                self.assertEqual(response.status_code, 302)
                self.assertFalse(case["model"].objects.filter(pk=obj.pk).exists())

    def test_warga_cannot_read_or_delete_submission_detail(self):
        for name, case in self.cases().items():
            with self.subTest(name=name):
                obj = case["model"].objects.create(
                    user=self.warga_lain,
                    **self.fresh_data(case["data"]),
                )
                response = self.client.get(reverse(case["detail"], args=[obj.pk]))
                self.assertEqual(response.status_code, 302)
                response = self.client.post(reverse(case["delete"], args=[obj.pk]))
                self.assertEqual(response.status_code, 302)
                self.assertTrue(case["model"].objects.filter(pk=obj.pk).exists())

    def test_each_detail_endpoint_returns_404_for_invalid_id(self):
        self.client.force_login(self.staff)
        for name, case in self.cases().items():
            with self.subTest(name=name):
                response = self.client.get(reverse(case["detail"], args=[999999]))
                self.assertEqual(response.status_code, 404)
