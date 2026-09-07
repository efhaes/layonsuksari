from django import template

from kembang.contact import normalize_whatsapp
from kembang.models import UserProfile

register = template.Library()


@register.filter
def whatsapp_number(obj):
    user = getattr(obj, "user", obj)
    try:
        profile = user.userprofile
    except (AttributeError, UserProfile.DoesNotExist):
        profile = None
    return normalize_whatsapp(getattr(profile, "no_whatsapp", "")) or ""


@register.filter
def whatsapp_message(obj, jenis_surat):
    user = getattr(obj, "user", None)
    try:
        profile = user.userprofile
    except (AttributeError, UserProfile.DoesNotExist):
        profile = None
    nama = getattr(profile, "nama", "") or "Bapak/Ibu"
    status_label = obj.get_status_display()
    message = (
        f"Halo Bapak/Ibu {nama},\n\n"
        f"Kami dari Kantor Desa Sukasari ingin menghubungi Anda terkait pengajuan {jenis_surat}.\n\n"
        f"Status pengajuan saat ini: {status_label}.\n"
    )
    if obj.status == "ditolak":
        alasan = (getattr(obj, "alasan_penolakan", "") or "").strip()
        if alasan:
            message += (
                f"\nAlasan Penolakan:\n{alasan}\n\n"
                "Silakan perbaiki atau lengkapi dokumen yang diperlukan.\n"
            )
    return message + "\nTerima kasih."
