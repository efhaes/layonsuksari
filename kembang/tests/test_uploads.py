import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from kembang.models import SKTMPengajuan, SuratKelahiran


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="sukasari-upload-test-"))
class UploadSecurityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.warga = User.objects.create_user(
            username="upload-warga",
            password="WargaPass123!",
        )
        cls.staff = User.objects.create_user(
            username="upload-staff",
            password="StaffPass123!",
            is_staff=True,
        )

    def valid_data(self):
        return {
            "nama_lengkap": "Bayi Upload",
            "tempat_lahir": "Bogor",
            "tanggal_lahir": "2024-01-01",
            "jenis_kelamin": "L",
            "nama_ayah": "Ayah",
            "nama_ibu": "Ibu",
            "alamat": "Alamat",
            "no_whatsapp": "081234567890",
            "surat_keterangan_lahir": SimpleUploadedFile(
                "lahir.pdf", b"%PDF-1.4", content_type="application/pdf"
            ),
            "fotokopi_ktp_kk": SimpleUploadedFile(
                "ktpkk.pdf", b"%PDF-1.4", content_type="application/pdf"
            ),
            "fotokopi_buku_nikah": SimpleUploadedFile(
                "nikah.pdf", b"%PDF-1.4", content_type="application/pdf"
            ),
            "surat_pengantar_rt_rw": SimpleUploadedFile(
                "pengantar.pdf", b"%PDF-1.4", content_type="application/pdf"
            ),
        }

    def test_invalid_image_upload_is_rejected(self):
        self.client.force_login(self.warga)
        data = {
            "nama_lengkap": "Warga SKTM",
            "alamat_lengkap": "Alamat",
            "nik": "3201010101010001",
            "no_whatsapp": "081234567890",
            "surat_pengantar": SimpleUploadedFile("pengantar.pdf", b"pdf"),
            "foto_ktp": SimpleUploadedFile(
                "not-an-image.png", b"not an image", content_type="image/png"
            ),
            "foto_kk": SimpleUploadedFile("kk.png", b"not an image", content_type="image/png"),
            "surat_pernyataan": SimpleUploadedFile("pernyataan.pdf", b"pdf"),
        }

        response = self.client.post(reverse("pengajuan_sktm"), data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SKTMPengajuan.objects.count(), 0)

    def test_submit_without_csrf_is_rejected_when_csrf_checks_enabled(self):
        client = self.client_class(enforce_csrf_checks=True)
        client.force_login(self.warga)

        response = client.post(reverse("pengajuan_akta_kelahiran"), self.valid_data())

        self.assertEqual(response.status_code, 403)

    def result_target(self):
        self.client.force_login(self.staff)
        return SuratKelahiran.objects.create(
            user=self.warga,
            nama_lengkap="Bayi",
            tempat_lahir="Bogor",
            tanggal_lahir="2024-01-01",
            jenis_kelamin="L",
            nama_ayah="Ayah",
            nama_ibu="Ibu",
            alamat="Alamat",
            no_whatsapp="081234567890",
            surat_keterangan_lahir="lahir.pdf",
            fotokopi_ktp_kk="ktpkk.pdf",
            fotokopi_buku_nikah="nikah.pdf",
            surat_pengantar_rt_rw="pengantar.pdf",
        )

    def update_result(self, obj, uploaded_file):
        return self.client.post(
            reverse("detail_pengajuan_kelahiran", args=[obj.pk]),
            {"status": "selesai", "hasil_surat": uploaded_file},
        )

    def test_valid_pdf_result_upload_is_accepted(self):
        obj = self.result_target()

        response = self.update_result(
            obj,
            SimpleUploadedFile(
                "result.pdf", b"%PDF-1.4 valid", content_type="application/pdf"
            ),
        )

        self.assertEqual(response.status_code, 302)
        obj.refresh_from_db()
        self.assertEqual(obj.status, "selesai")
        self.assertTrue(obj.hasil_surat.name.endswith("result.pdf"))

    def test_non_pdf_result_upload_is_rejected(self):
        obj = self.result_target()

        response = self.update_result(
            obj,
            SimpleUploadedFile(
                "result.exe", b"not a pdf", content_type="application/octet-stream"
            ),
        )

        self.assertEqual(response.status_code, 302)
        obj.refresh_from_db()
        self.assertEqual(obj.status, "diajukan")
        self.assertFalse(obj.hasil_surat)

    def test_pdf_extension_with_invalid_content_is_rejected(self):
        obj = self.result_target()

        response = self.update_result(
            obj,
            SimpleUploadedFile(
                "result.pdf", b"not a pdf", content_type="application/pdf"
            ),
        )

        self.assertEqual(response.status_code, 302)
        obj.refresh_from_db()
        self.assertEqual(obj.status, "diajukan")
        self.assertFalse(obj.hasil_surat)

    def test_empty_pdf_result_upload_is_rejected(self):
        obj = self.result_target()

        response = self.update_result(
            obj,
            SimpleUploadedFile("result.pdf", b"", content_type="application/pdf"),
        )

        self.assertEqual(response.status_code, 302)
        obj.refresh_from_db()
        self.assertEqual(obj.status, "diajukan")
        self.assertFalse(obj.hasil_surat)

    def test_oversized_pdf_result_upload_is_rejected(self):
        obj = self.result_target()

        response = self.update_result(
            obj,
            SimpleUploadedFile(
                "result.pdf",
                b"%PDF-1.4" + b"x" * (10 * 1024 * 1024),
                content_type="application/pdf",
            ),
        )

        self.assertEqual(response.status_code, 302)
        obj.refresh_from_db()
        self.assertEqual(obj.status, "diajukan")
        self.assertFalse(obj.hasil_surat)

