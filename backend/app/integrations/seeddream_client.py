import os
from dotenv import load_dotenv
from byteplussdkarkruntime import Ark
import httpx

load_dotenv()

ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.ap-southeast.bytepluses.com/api/v3")
ARK_API_KEY = os.getenv("ARK_API_KEY")
SEEDDREAM_MODEL = os.getenv("SEEDDREAM_MODEL", "seedream-4-5-251128")

if not ARK_API_KEY:
    raise RuntimeError("ARK_API_KEY is not set")

# Timeout total 90 detik (ubah kalau mau)
_httpx_timeout = httpx.Timeout(90.0, connect=30.0, read=90.0, write=30.0)

_client = Ark(
    base_url=ARK_BASE_URL,
    api_key=ARK_API_KEY,
    timeout=_httpx_timeout,   # <= ini kunci
)

def generate_i2i_url(*, prompt: str, image_data_url: str, size: str = "4k", watermark: bool = False) -> str:
    print("[SEEDDREAM REQUEST] model=", SEEDDREAM_MODEL, "watermark=", watermark)

    resp = _client.images.generate(
        model=SEEDDREAM_MODEL,
        prompt=prompt,
        image=image_data_url,
        size=size,
        response_format="url",
        watermark=watermark,
    )
    return resp.data[0].url

