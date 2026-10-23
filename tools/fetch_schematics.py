"""Download the community OSC schematics referenced in the video descriptions.

    python3 fetch_schematics.py <out_dir>

Files are the authors' own uploads (MediaFire / Google Drive); they are fetched for local
testing and are not redistributed in this repository.
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"

SOURCES = {
    "cubicmetre/osc6.1": ["https://www.mediafire.com/file/vzgb1yd0b4wu6h6/The_Orbital_Strike_Cannon_Mk.6.1.litematic/file",
                          "https://www.mediafire.com/file/0ft1rhdaix545ay/OSC_6_Nether.litematic/file",
                          "https://www.mediafire.com/file/aaxm0toied87r6l/OSC_6_Control_Panel.litematic/file",
                          "https://www.mediafire.com/file/xn8n9v18t7df49b/OSC_6.0_Fire_Control.xlsx/file"],
    "cubicmetre/osc1": ["https://www.mediafire.com/folder/88qrgise22lax/Orbital_Strike_Cannon"],
    "cubicmetre/minimal_signature": ["https://www.mediafire.com/folder/ykwaocnz7cslg/Orbital_Strike_Minimal_Signature"],
    "cubicmetre/skybender": ["https://www.mediafire.com/folder/8k2xnz31xw56q/Orbital_Skybender"],
    "cubicmetre/chaos_cube": ["https://www.mediafire.com/file/9szvlhbps89ap0w/Sulfur_Cube_Cannon.zip/file"],
    "cubicmetre/railcannon": ["https://www.mediafire.com/file/1zh80q14wed2kre/The_Orbital_Railcannon.litematic/file"],
    "cubicmetre/anvil_cluster": ["https://www.mediafire.com/folder/kjm0zmlyonmvp/Anvil_and_Cluster_Artillery"],
    "cubicmetre/smart_artillery": ["https://www.mediafire.com/folder/yci3ip29bpu36/Smart_Artillery"],
    "cubicmetre/tnt_railgun": ["https://www.mediafire.com/file/0uvhi7160jgdord/TnT_Railgun.litematic/file"],
    "cubicmetre/anti_air": ["https://www.mediafire.com/file/3lmdwkokjxf5j95/Anti-Air_Auto-Cannon.litematic/file"],
    "dumbrock/wosc2": ["https://www.mediafire.com/file/2w6y7q2bl4eg7ik/WOSC_2.0.litematic/file"],
    "dumbrock/hollower": ["https://www.mediafire.com/file/mnt0nh6ftnwuthq/WOSC_Thee_Hollower.litematic/file"],
    "dumbrock/tosc": ["https://www.mediafire.com/file/y1tgghhjkhst36k/TOSC.litematic/file"],
    "dumbrock/mosc": ["https://www.mediafire.com/file/lderslmuf0ih727/MOSC.litematic/file",
                      "https://www.mediafire.com/folder/zi42yqnob9ku0/MOSC_evolution"],
    "hogan/paper": ["https://www.mediafire.com/file/z21y4eyolx0gb9e/Schematics.zip/file",
                    "https://drive.google.com/file/d/1iEjoTdiM7ADpWbZCq7RrsIOE17GbffS7/view?usp=sharing"],
    "table/mini": ["https://www.mediafire.com/file/jp5ktriienk0757/Orbital_Strike_cannons.zip/file"],
    "tkparmaa/ce": ["https://drive.google.com/drive/folders/1WdUUlT5t4d-O6i3UElhzuL9VTBE5TGMG",
                    "https://drive.google.com/drive/folders/1p92PpnBEW9vvnm_5_TX6dEEbUjw2IneZ"],
    "wmc/pearl_lazy": ["https://drive.google.com/drive/folders/1jTPoPleTWz_S8t9jjbV7mHVteSPWbUGp"],
    "wmc/wither": ["https://drive.google.com/drive/folders/189bKvMRewQbvr2p3G9DZXOvTTfGVfFAA"],
    "malorem/missile": ["https://drive.google.com/file/d/1qyG0LuhYqvf16FVoooANKL0knQyYJXsD/view"],
    "moxxie/mk6": ["https://drive.google.com/file/d/1Pu7KSIbQ6fs_yaRWO9lndmBGUS2gAKSE/view",
                   "https://drive.google.com/file/d/13U4z78ix38hDTVW1DyC_xDfCJ9MZHU38/view"],
}


def curl(url, out=None):
    cmd = ["curl", "-sSL", "-A", UA, url]
    if out:
        cmd += ["-o", out]
        return subprocess.run(cmd).returncode == 0
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def mediafire_file(url, out_dir):
    page = curl(url)
    m = re.search(r'href="(https://download\d*\.mediafire\.com/[^"]+)"', page)
    if not m:
        return f"no link: {url}"
    name = urllib.parse.unquote(url.rstrip("/").split("/")[-2]).replace("%", "")
    curl(m.group(1), os.path.join(out_dir, name))
    return f"ok {name}"


def mediafire_folder(url, out_dir):
    key = url.split("/folder/")[1].split("/")[0]
    res = []
    api = ("https://www.mediafire.com/api/1.5/folder/get_content.php?folder_key={}&content_type={}"
           "&response_format=json")
    for kind in ("files", "folders"):
        data = json.loads(curl(api.format(key, kind)) or "{}")
        content = data.get("response", {}).get("folder_content", {})
        for f in content.get("files", []) or []:
            res.append(mediafire_file(f["links"]["normal_download"], out_dir))
        for sub in content.get("folders", []) or []:
            d = os.path.join(out_dir, sub["name"])
            os.makedirs(d, exist_ok=True)
            res += mediafire_folder(f"https://www.mediafire.com/folder/{sub['folderkey']}", d)
    return res


def gdrive(url, out_dir):
    try:
        import gdown
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "gdown"])
        import gdown
    try:
        if "/folders/" in url:
            gdown.download_folder(url, output=out_dir, quiet=True, use_cookies=False)
        else:
            gdown.download(url, output=out_dir + "/", quiet=True, fuzzy=True)
        return f"ok {url}"
    except Exception as e:  # private / quota
        return f"fail {url}: {e}"


def main(out):
    for name, urls in SOURCES.items():
        d = os.path.join(out, name)
        os.makedirs(d, exist_ok=True)
        for u in urls:
            if "mediafire.com/folder" in u:
                r = mediafire_folder(u, d)
            elif "mediafire.com" in u:
                r = mediafire_file(u, d)
            else:
                r = gdrive(u, d)
            print(name, r)
        for z in [f for f in os.listdir(d) if f.endswith(".zip")]:
            subprocess.run(["unzip", "-q", "-o", os.path.join(d, z), "-d", os.path.join(d, z[:-4])])


if __name__ == "__main__":
    main(sys.argv[1])
