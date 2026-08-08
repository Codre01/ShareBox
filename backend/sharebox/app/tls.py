"""Self-signed certificate management for LAN HTTPS.

ShareBox has no domain name and no way to reach a public CA, so the host mints
its own certificate covering its LAN addresses. Browsers will still warn the
first time - there is no way around that without a real CA - so the Control
Center shows the certificate fingerprint for the user to compare against the
one the browser reports.
"""

from __future__ import annotations

import datetime as dt
import ipaddress
import logging
from dataclasses import dataclass
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

logger = logging.getLogger("sharebox.tls")

# Browsers reject leaf certificates valid for much longer than this.
VALIDITY_DAYS = 397
# Regenerate before expiry rather than on it.
RENEW_WITHIN_DAYS = 30
KEY_SIZE = 2048


@dataclass(frozen=True)
class CertificatePaths:
    certificate: Path
    key: Path


def _san_entries(ip_addresses: list[str]) -> list[x509.GeneralName]:
    names: list[x509.GeneralName] = [
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
    ]
    for raw in ip_addresses:
        try:
            address = ipaddress.ip_address(raw)
        except ValueError:
            continue
        if address.is_loopback:
            continue
        names.append(x509.IPAddress(address))
    return names


def _covered_addresses(certificate: x509.Certificate) -> set[str]:
    try:
        san = certificate.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        ).value
    except x509.ExtensionNotFound:
        return set()
    return {str(ip) for ip in san.get_values_for_type(x509.IPAddress)}


def fingerprint(certificate: x509.Certificate) -> str:
    """SHA-256 fingerprint, formatted the way browsers display it."""
    digest = certificate.fingerprint(hashes.SHA256())
    return ":".join(f"{byte:02X}" for byte in digest)


class CertificateStore:
    def __init__(self, app_data_dir: Path) -> None:
        self.directory = app_data_dir / "tls"
        self.paths = CertificatePaths(
            certificate=self.directory / "sharebox-cert.pem",
            key=self.directory / "sharebox-key.pem",
        )

    def load(self) -> x509.Certificate | None:
        try:
            return x509.load_pem_x509_certificate(self.paths.certificate.read_bytes())
        except (OSError, ValueError):
            return None

    def fingerprint(self) -> str | None:
        certificate = self.load()
        return fingerprint(certificate) if certificate else None

    def needs_regeneration(self, ip_addresses: list[str]) -> bool:
        certificate = self.load()
        if certificate is None or not self.paths.key.exists():
            return True

        now = dt.datetime.now(dt.timezone.utc)
        if certificate.not_valid_after_utc <= now + dt.timedelta(days=RENEW_WITHIN_DAYS):
            logger.info("Certificate is expiring — regenerating")
            return True

        # A new Wi-Fi network means a new LAN IP the certificate does not cover.
        wanted = {a for a in ip_addresses if not ipaddress.ip_address(a).is_loopback}
        if not wanted.issubset(_covered_addresses(certificate)):
            logger.info("Certificate does not cover current LAN addresses — regenerating")
            return True
        return False

    def ensure(self, ip_addresses: list[str], host_name: str = "ShareBox") -> CertificatePaths:
        """Return usable cert/key paths, generating them when needed."""
        if self.needs_regeneration(ip_addresses):
            self.generate(ip_addresses, host_name)
        return self.paths

    def generate(self, ip_addresses: list[str], host_name: str = "ShareBox") -> CertificatePaths:
        self.directory.mkdir(parents=True, exist_ok=True)

        key = rsa.generate_private_key(public_exponent=65537, key_size=KEY_SIZE)
        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, host_name[:64] or "ShareBox"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ShareBox"),
            ]
        )
        now = dt.datetime.now(dt.timezone.utc)
        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - dt.timedelta(minutes=5))  # tolerate clock skew
            .not_valid_after(now + dt.timedelta(days=VALIDITY_DAYS))
            .add_extension(
                x509.SubjectAlternativeName(_san_entries(ip_addresses)), critical=False
            )
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .sign(key, hashes.SHA256())
        )

        self.paths.key.write_bytes(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        # The private key is per-install and never leaves the machine, but it
        # still has no business being world-readable.
        try:
            self.paths.key.chmod(0o600)
        except OSError:
            logger.debug("Could not restrict key permissions", exc_info=True)

        self.paths.certificate.write_bytes(
            certificate.public_bytes(serialization.Encoding.PEM)
        )
        logger.info(
            "Generated self-signed certificate for %s (SHA-256 %s)",
            ip_addresses or ["127.0.0.1"],
            fingerprint(certificate),
        )
        return self.paths
