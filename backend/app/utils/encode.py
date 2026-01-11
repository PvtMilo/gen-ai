from pathlib import Path
import base64

def file_to_data_url(file_path: Path) -> str:
    """
    Return format:
    data:image/jpeg;base64,AAAA...
    """
    suffix = file_path.suffix.lower()
    mime = "image/jpeg"
    if suffix == ".png":
        mime = "image/png"
    elif suffix == ".webp":
        mime = "image/webp"

    data = file_path.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{b64}"
