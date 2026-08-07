"""تحليل حركة خادم AI وإدارة التعديلات التجريبية.

اتصال ``CONNECT`` هو نفق TLS معتم؛ لذلك يستطيع المحلل قياس الحجم وEntropy
فقط، ولا يستطيع استنتاج قرار AI أو تعديل الرسالة الداخلية بأمان. أي تغيير في
TLS ciphertext يفشل تحقق AEAD ويقطع الاتصال. دالة ``modify_ai_payload``
مخصصة حصراً لبيانات مفكوكة/عينات اختبار، ولا تُستعمل على نفق TLS.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any

AI_HOSTS = ["pes22-game.cs.konami.net"]
SAMPLE_LIMIT = 1024

# (offset, value, required_length_exclusive) كما طُلب في النموذج التجريبي.
# لا توجد دلالة موثقة لهذه المواقع في بروتوكول KONAMI؛ لذلك لا يجوز تطبيقها
# على TLS أو حركة إنتاج مشفرة.
_PATCHES = {
    "slow_ai": (42, 0x32, 50),
    "no_press": (55, 0x0A, 60),
    "ai_miss": (68, 0xFF, 70),
    "stamina": (75, 0x00, 80),
}


def _clean_host(host: str) -> str:
    """Normalize a host (optionally including a port) for exact matching."""
    value = (host or "").strip().lower().rstrip(".")
    if value.startswith("[") and "]" in value:  # IPv6-style bracketed host
        return value[1 : value.index("]")]
    if value.count(":") == 1:
        name, maybe_port = value.rsplit(":", 1)
        if maybe_port.isdigit():
            value = name
    return value


def is_ai_file(host: str) -> bool:
    """Return True only for a configured AI host or one of its subdomains."""
    clean = _clean_host(host)
    return any(clean == item or clean.endswith("." + item) for item in AI_HOSTS)


def calculate_entropy(payload: bytes, limit: int = SAMPLE_LIMIT) -> float:
    """Calculate Shannon entropy for a bounded payload sample."""
    sample = bytes(payload[:limit])
    if not sample:
        return 0.0

    frequencies: dict[int, int] = {}
    for byte in sample:
        frequencies[byte] = frequencies.get(byte, 0) + 1

    length = len(sample)
    value = -sum(
        (count / length) * math.log2(count / length)
        for count in frequencies.values()
    )
    return round(value, 2)


def looks_like_tls_record(payload: bytes) -> bool:
    """Best-effort detection of a TLS record header at the start of a chunk."""
    if len(payload) < 5:
        return False
    content_type, major, minor = payload[0], payload[1], payload[2]
    record_length = int.from_bytes(payload[3:5], "big")
    return (
        content_type in {20, 21, 22, 23, 24}
        and major == 3
        and 0 <= minor <= 4
        and 0 < record_length <= (2**14 + 256)
    )


def _classify(size: int, entropy: float) -> tuple[str, int]:
    """Keep the requested size/entropy heuristic, explicitly as a guess."""
    if size > 5000 and entropy > 7.5:
        return "AI Match Data", 94
    if size > 1000:
        return "AI BehaviorTree", 88
    return "AI Config", 75


def analyze_ai_payload(
    payload: bytes,
    host: str,
    *,
    encrypted_transport: bool | None = None,
) -> dict[str, Any]:
    """Analyze a bounded payload sample without retaining its contents.

    ``type`` and ``confidence`` preserve the requested heuristic. They are not
    protocol-level proof: on TLS they describe traffic shape only.
    """
    data = bytes(payload)
    size = len(data)
    entropy = calculate_entropy(data)
    file_type, confidence = _classify(size, entropy)
    encrypted = (
        looks_like_tls_record(data)
        if encrypted_transport is None
        else bool(encrypted_transport)
    )
    ai_host = is_ai_file(host)

    return {
        "is_ai": ai_host,
        "file": _clean_host(host),
        "size": size,
        "sample_size": min(size, SAMPLE_LIMIT),
        "entropy": entropy,
        "type": file_type,
        "confidence": confidence,
        "heuristic": True,
        "encrypted_transport": encrypted,
        "can_modify": ai_host and not encrypted,
        "needs_modify": ai_host and not encrypted and entropy > 7.0 and size > 1000,
        "note": (
            "TLS metadata only; payload meaning and AI decisions are not visible"
            if encrypted
            else "Decoded/offline payload heuristic"
        ),
    }


def _enabled_keys(enabled: Iterable[str] | Mapping[str, object]) -> set[str]:
    if isinstance(enabled, Mapping):
        return {str(key) for key, value in enabled.items() if value is True}
    return {str(key) for key in enabled}


def modify_ai_payload(
    payload: bytes,
    enabled: Iterable[str] | Mapping[str, object],
) -> tuple[bytes, list[str]]:
    """Apply experimental offsets to *decoded/offline* bytes.

    Never call this for CONNECT/TLS ciphertext. The return list contains only
    patches that were actually applied; ``show_ai`` is a UI-only preference.
    """
    data = bytearray(payload)
    requested = _enabled_keys(enabled)
    applied: list[str] = []

    for key, (offset, value, required_length) in _PATCHES.items():
        if key in requested and len(data) > required_length:
            data[offset] = value
            applied.append(key)

    return bytes(data), applied


class AIConnectionAnalyzer:
    """Bounded, per-connection analyzer used by both proxy entry points."""

    def __init__(
        self,
        host: str,
        enabled: Iterable[str] | Mapping[str, object] = (),
        *,
        encrypted_tunnel: bool = True,
    ) -> None:
        self.host = _clean_host(host)
        self.enabled = _enabled_keys(enabled)
        self.encrypted_tunnel = encrypted_tunnel
        self.client_bytes = 0
        self.server_bytes = 0
        self._server_sample = bytearray()
        self._applied: set[str] = set()

    def process(self, chunk: bytes, direction: str) -> bytes:
        """Observe a chunk and return bytes safe to relay."""
        if direction == "client_to_server":
            self.client_bytes += len(chunk)
            return chunk

        self.server_bytes += len(chunk)
        if len(self._server_sample) < SAMPLE_LIMIT:
            remaining = SAMPLE_LIMIT - len(self._server_sample)
            self._server_sample.extend(chunk[:remaining])

        # CONNECT traffic remains byte-for-byte passthrough. This branch exists
        # only for future decoded/offline adapters that can provide plaintext.
        if not self.encrypted_tunnel and self.enabled:
            modified, applied = modify_ai_payload(chunk, self.enabled)
            self._applied.update(applied)
            return modified
        return chunk

    def result(self) -> dict[str, Any]:
        analysis = analyze_ai_payload(
            bytes(self._server_sample),
            self.host,
            encrypted_transport=self.encrypted_tunnel,
        )
        file_type, confidence = _classify(self.server_bytes, analysis["entropy"])
        analysis.update(
            {
                "size": self.server_bytes,
                "sample_size": len(self._server_sample),
                "client_bytes": self.client_bytes,
                "server_bytes": self.server_bytes,
                "type": file_type,
                "confidence": confidence,
                "requested_features": sorted(self.enabled),
                "applied_features": sorted(self._applied),
                "mode": "metadata_only" if self.encrypted_tunnel else "decoded_payload",
            }
        )
        return analysis
