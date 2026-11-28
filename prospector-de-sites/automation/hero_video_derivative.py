"""Fixed, reproducible offline web encode; no arbitrary filters or commands."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import tempfile
import json

RECIPE="h264-web-crf25-v1"

def digest(path):
    with Path(path).open("rb") as f:
        h=hashlib.sha256()
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
        return h.hexdigest()

def _tools():
    exe=shutil.which("ffmpeg")
    probe=shutil.which("ffprobe")
    if not exe or not probe:
        raise ValueError("FFmpeg and ffprobe required for derivative verification")
    return Path(exe).resolve(),Path(probe).resolve()

def _run(args,timeout=180):
    try:
        return subprocess.run([str(x) for x in args],check=True,capture_output=True,timeout=timeout).stdout
    except (OSError,subprocess.SubprocessError) as exc:
        raise ValueError("Offline video derivative verification failed") from exc

def _metadata(probe,path):
    data=json.loads(_run([probe,"-v","error","-count_frames","-show_entries",
         "stream=codec_type,codec_name,width,height,nb_read_frames,duration,r_frame_rate,pix_fmt",
         "-of","json",path],timeout=90))
    streams=data.get("streams",[])
    videos=[s for s in streams if s.get("codec_type")=="video"]
    if len(videos)!=1:
        raise ValueError("One video stream required")
    v=videos[0]
    try:
        result={"width":int(v["width"]),"height":int(v["height"]),
                "frames":int(v["nb_read_frames"]),"duration":float(v["duration"]),
                "rate":v["r_frame_rate"]}
    except (KeyError,TypeError,ValueError) as exc:
        raise ValueError("Missing video frame/timing metadata") from exc
    if result["frames"]<1 or result["duration"]<=0:
        raise ValueError("Empty or invalid video")
    return result,streams

def _encode(exe,source,target):
    _run([exe,"-v","error","-nostdin","-y","-threads","1","-i",source,
          "-map","0:v:0","-an","-sn","-dn","-map_metadata","-1","-map_chapters","-1",
          "-c:v","libx264","-preset","medium","-crf","25","-pix_fmt","yuv420p",
          "-threads","1","-fflags","+bitexact","-flags:v","+bitexact",
          "-fps_mode","passthrough","-movflags","+faststart",target])

def _check_metadata(probe,source,target):
    src,_=_metadata(probe,source)
    dst,streams=_metadata(probe,target)
    if (any(src[k]!=dst[k] for k in ("width","height","frames","rate")) or
        abs(src["duration"]-dst["duration"])>0.001 or len(streams)!=1 or
        streams[0].get("codec_name")!="h264" or streams[0].get("pix_fmt")!="yuv420p"):
        raise ValueError("Derivative changed geometry, frame count, duration, or stream contract")
    return dst

def _ref(path):
    p=Path(path).resolve(strict=True)
    if not p.is_file() or p.stat().st_size==0:
        raise ValueError("Missing video artifact")
    return {"path":str(p),"sha256":digest(p)}

def create_web_derivative(original,target):
    source=Path(original).resolve(strict=True)
    target=Path(target).resolve()
    if target.suffix.lower()!=".mp4" or target.exists() or target==source:
        raise ValueError("Derivative requires a new MP4 path")
    exe,probe=_tools()
    source_ref=_ref(source)
    with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
        encoded=Path(tmp)/"encoded.mp4"
        _encode(exe,source,encoded)
        _check_metadata(probe,source,encoded)
        if _ref(source)!=source_ref:
            raise ValueError("Original changed during encoding")
        # Copy into an exclusive destination, never overwrite existing review assets.
        with encoded.open("rb") as f,target.open("xb") as out:
            shutil.copyfileobj(f,out)
    return {"recipe":RECIPE,"ffmpegSha256":digest(exe),"original":source_ref,
            "output":_ref(target)}

def verify_web_derivative(record,ledger_original,final_video):
    if not isinstance(record,dict) or set(record)!={"recipe","ffmpegSha256","original","output"} or record["recipe"]!=RECIPE:
        raise ValueError("Unsupported derivative recipe")
    exe,probe=_tools()
    if digest(exe)!=record["ffmpegSha256"]:
        raise ValueError("Derivative FFmpeg build differs; use original reviewed build")
    for ref,expected in ((record["original"],ledger_original),(record["output"],final_video)):
        if not isinstance(ref,dict) or set(ref)!={"path","sha256"} or _ref(ref["path"])!=ref or ref["sha256"]!=expected["sha256"]:
            raise ValueError("Derivative artifact does not bind original ledger and final video")
    if record["original"]["sha256"]==record["output"]["sha256"]:
        raise ValueError("Derivative must be distinct from original")
    source=record["original"]["path"]
    target=record["output"]["path"]
    _check_metadata(probe,source,target)
    with tempfile.TemporaryDirectory() as tmp:
        expected=Path(tmp)/"expected.mp4"
        _encode(exe,source,expected)
        if digest(expected)!=record["output"]["sha256"]:
            raise ValueError("Derivative bytes do not reproduce from exact original")
    return True
