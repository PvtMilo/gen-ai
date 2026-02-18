import json
import subprocess
import sys
from pydantic import BaseModel
from fastapi import APIRouter


router = APIRouter(prefix="/printer", tags=["printer"])


class PrinterDeviceOut(BaseModel):
    name: str
    is_default: bool = False


class PrinterDevicesOut(BaseModel):
    printers: list[PrinterDeviceOut]
    detected_on: str
    error_message: str | None = None


def _normalize_devices(raw: object) -> list[PrinterDeviceOut]:
    if raw is None:
        return []

    if isinstance(raw, dict):
        raw_items = [raw]
    elif isinstance(raw, list):
        raw_items = raw
    else:
        return []

    devices: list[PrinterDeviceOut] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("Name") or "").strip()
        if not name:
            continue
        is_default = bool(item.get("Default"))
        devices.append(PrinterDeviceOut(name=name, is_default=is_default))

    devices.sort(key=lambda x: (not x.is_default, x.name.lower()))
    return devices


def _detect_windows_printers() -> list[PrinterDeviceOut]:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "$ErrorActionPreference='Stop'; Get-Printer | Select-Object Name,Default | ConvertTo-Json -Compress",
    ]
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "Get-Printer failed")

    output = (proc.stdout or "").strip()
    if not output:
        return []

    parsed = json.loads(output)
    return _normalize_devices(parsed)


@router.get("", response_model=PrinterDevicesOut)
def printer_health():
    return PrinterDevicesOut(printers=[], detected_on=sys.platform)


@router.get("/devices", response_model=PrinterDevicesOut)
def list_printers():
    if not sys.platform.startswith("win"):
        return PrinterDevicesOut(
            printers=[],
            detected_on=sys.platform,
            error_message="Printer auto-detection is implemented for Windows only",
        )

    try:
        devices = _detect_windows_printers()
        return PrinterDevicesOut(printers=devices, detected_on=sys.platform)
    except Exception as exc:
        return PrinterDevicesOut(
            printers=[],
            detected_on=sys.platform,
            error_message=str(exc),
        )
