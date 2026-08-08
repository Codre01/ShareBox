from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pytest
from cryptography import x509

from sharebox.app.tls import CertificateStore


@pytest.fixture()
def store(tmp_path: Path) -> CertificateStore:
    return CertificateStore(tmp_path)


def _san_ips(certificate: x509.Certificate) -> set[str]:
    san = certificate.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    return {str(ip) for ip in san.get_values_for_type(x509.IPAddress)}


def _san_dns(certificate: x509.Certificate) -> set[str]:
    san = certificate.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    return set(san.get_values_for_type(x509.DNSName))


def test_generate_writes_cert_and_key(store: CertificateStore):
    paths = store.generate(["192.168.1.50"])
    assert paths.certificate.is_file()
    assert paths.key.is_file()


def test_certificate_covers_lan_and_loopback(store: CertificateStore):
    store.generate(["192.168.1.50", "10.0.0.7"])
    certificate = store.load()
    assert certificate is not None

    assert _san_ips(certificate) == {"192.168.1.50", "10.0.0.7", "127.0.0.1"}
    assert "localhost" in _san_dns(certificate)


def test_invalid_addresses_are_skipped(store: CertificateStore):
    store.generate(["not-an-ip", "192.168.1.50"])
    assert _san_ips(store.load()) == {"192.168.1.50", "127.0.0.1"}


def test_validity_window_is_browser_acceptable(store: CertificateStore):
    store.generate(["192.168.1.50"])
    certificate = store.load()

    span = certificate.not_valid_after_utc - certificate.not_valid_before_utc
    assert span <= dt.timedelta(days=398), "browsers reject long-lived leaf certs"
    # Backdated slightly so a skewed client clock does not see it as future-dated.
    assert certificate.not_valid_before_utc < dt.datetime.now(dt.timezone.utc)


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="POSIX mode bits; Windows chmod only toggles read-only, so 0600 is a no-op",
)
def test_key_is_not_world_readable(store: CertificateStore):
    paths = store.generate(["192.168.1.50"])
    assert paths.key.stat().st_mode & 0o077 == 0


def test_fingerprint_is_stable_and_formatted(store: CertificateStore):
    store.generate(["192.168.1.50"])
    value = store.fingerprint()

    assert value == store.fingerprint()
    assert len(value.split(":")) == 32, "SHA-256 is 32 bytes"
    assert value == value.upper()


def test_fingerprint_changes_when_regenerated(store: CertificateStore):
    store.generate(["192.168.1.50"])
    first = store.fingerprint()
    store.generate(["192.168.1.50"])
    assert store.fingerprint() != first


def test_missing_certificate_needs_regeneration(store: CertificateStore):
    assert store.needs_regeneration(["192.168.1.50"]) is True
    assert store.load() is None
    assert store.fingerprint() is None


def test_existing_certificate_is_reused(store: CertificateStore):
    store.generate(["192.168.1.50"])
    assert store.needs_regeneration(["192.168.1.50"]) is False


def test_new_lan_address_forces_regeneration(store: CertificateStore):
    store.generate(["192.168.1.50"])
    # Joining a different Wi-Fi network hands out an address the cert omits.
    assert store.needs_regeneration(["10.0.0.7"]) is True


def test_losing_an_address_does_not_force_regeneration(store: CertificateStore):
    store.generate(["192.168.1.50", "10.0.0.7"])
    assert store.needs_regeneration(["192.168.1.50"]) is False


def test_ensure_is_idempotent(store: CertificateStore):
    store.ensure(["192.168.1.50"])
    first = store.fingerprint()
    store.ensure(["192.168.1.50"])
    assert store.fingerprint() == first


def test_corrupt_certificate_is_replaced(store: CertificateStore):
    store.generate(["192.168.1.50"])
    store.paths.certificate.write_text("not a certificate", encoding="utf-8")

    assert store.load() is None
    assert store.needs_regeneration(["192.168.1.50"]) is True
    store.ensure(["192.168.1.50"])
    assert store.load() is not None


def test_certificate_is_not_a_ca(store: CertificateStore):
    store.generate(["192.168.1.50"])
    constraints = store.load().extensions.get_extension_for_class(x509.BasicConstraints)
    assert constraints.value.ca is False
    assert constraints.critical is True


def test_host_name_becomes_common_name(store: CertificateStore):
    store.generate(["192.168.1.50"], host_name="Kitchen PC")
    common = store.load().subject.get_attributes_for_oid(
        x509.oid.NameOID.COMMON_NAME
    )[0].value
    assert common == "Kitchen PC"


def test_overlong_host_name_is_truncated(store: CertificateStore):
    store.generate(["192.168.1.50"], host_name="X" * 200)
    common = store.load().subject.get_attributes_for_oid(
        x509.oid.NameOID.COMMON_NAME
    )[0].value
    assert len(common) <= 64
