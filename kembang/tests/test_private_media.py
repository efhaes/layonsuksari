import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from kembang.models import SuratKelahiran


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="sukasari-private-media-"))
class ProtectedMediaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="media-owner")
        cls.other_user = User.objects.create_user(username="media-other")
        cls.staff = User.objects.create_user(username="media-staff", is_staff=True)
        cls.application = SuratKelahiran.objects.create(
            user=cls.owner,
            nama_lengkap="Dokumen Pribadi",
            tempat_lahir="Bogor",
            tanggal_lahir="2024-01-01",
            jenis_kelamin="L",
            nama_ayah="Ayah",
            nama_ibu="Ibu",
            alamat="Alamat",
            no_whatsapp="081234567890",
            surat_keterangan_lahir=SimpleUploadedFile("lahir.pdf", b"private document"),
            fotokopi_ktp_kk=SimpleUploadedFile("ktpkk.pdf", b"private identity"),
            fotokopi_buku_nikah=SimpleUploadedFile("nikah.pdf", b"private marriage"),
            surat_pengantar_rt_rw=SimpleUploadedFile("pengantar.pdf", b"private letter"),
            hasil_surat=SimpleUploadedFile("hasil.pdf", b"private result"),
        )

    def file_url(self, field):
        return reverse(
            "protected_surat_file",
            args=["suratkelahiran", self.application.pk, field],
        )

    def test_anonymous_cannot_download_private_file(self):
        response = self.client.get(self.file_url("hasil_surat"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_other_warga_cannot_download_private_file(self):
        self.client.force_login(self.other_user)

        response = self.client.get(self.file_url("hasil_surat"))

        self.assertEqual(response.status_code, 403)

    def test_owner_can_download_own_private_file(self):
        self.client.force_login(self.owner)

        response = self.client.get(self.file_url("hasil_surat"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"private result")
        self.assertEqual(response.headers["Content-Disposition"], 'attachment; filename="hasil.pdf"')

    def test_staff_can_download_private_file(self):
        self.client.force_login(self.staff)

        response = self.client.get(self.file_url("fotokopi_ktp_kk"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"private identity")

    def test_unknown_file_field_is_not_a_valid_download(self):
        self.client.force_login(self.owner)

        response = self.client.get(self.file_url("settings.py"))

        self.assertEqual(response.status_code, 404)

    def test_private_media_path_is_not_served_by_public_media_route(self):
        response = self.client.get(
            f"/media/{self.application.hasil_surat.name}"
        )

        self.assertEqual(response.status_code, 404)
