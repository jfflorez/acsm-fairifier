"""Masking of run-dependent parts of EBAS .nas outputs, shared by the tests.

The converter names files <station>.<start>.<CREATED>.<...>.nas. CREATED
(YYYYMMDDHHMMSS) changes on every run and is also written inside the file,
together with its date as 'YYYY MM DD'.
"""
from datetime import datetime


def creation_stamp(name: str) -> str:
    """The 3rd dot-separated field of the file name; fails loudly if it isn't a stamp."""
    stamp = name.split(".")[2]
    datetime.strptime(stamp, "%Y%m%d%H%M%S")
    return stamp


def mask_name(name: str) -> str:
    parts = name.split(".")
    creation_stamp(name)
    parts[2] = "CREATED"          # no < > : not allowed in Windows file names
    return ".".join(parts)


def mask_content(name: str, data: bytes) -> bytes:
    """File content with this file's own creation stamp and date masked."""
    stamp = creation_stamp(name)
    created = datetime.strptime(stamp, "%Y%m%d%H%M%S")
    data = data.replace(stamp.encode(), b"<CREATED>")
    return data.replace(created.strftime("%Y %m %d").encode(), b"<DATE>")    # e.g. 2026 10 27
