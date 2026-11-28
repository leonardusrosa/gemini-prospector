"""Offline extraction and verification of standalone video endpoint posters."""
from pathlib import Path
import subprocess
import tempfile
import hashlib

def _extract(video, destination, last):
    # Decode actual first/last frame with deterministic PNG encoding.
    cmd=["ffmpeg","-v","error","-nostdin","-y","-i",str(video),"-an"]
    if last:
        # Update one output image for every decoded frame, leaving the final frame.
        cmd += ["-update","1"]
    else:
        cmd += ["-frames:v","1"]
    cmd += ["-c:v","png","-threads","1",str(destination)]
    try:
        subprocess.run(cmd,check=True,timeout=90,capture_output=True)
    except (OSError,subprocess.SubprocessError) as exc:
        raise ValueError("Could not decode video endpoint") from exc
    if not Path(destination).is_file():
        raise ValueError("Missing decoded endpoint")

def extract_video_frames(video, folder, variant):
    if variant not in ("desktop","mobile"):
        raise ValueError("Unknown viewport")
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    result={}
    for suffix in ("start","end"):
        target=folder/(variant+"_"+suffix+".png")
        if target.exists():
            raise ValueError("Do not overwrite reviewed posters")
        _extract(video,target,suffix=="end")
        result[variant+"_"+suffix]={"path":str(target.resolve()),"sha256":hashlib.sha256(target.read_bytes()).hexdigest()}
    return result

def verify_video_frames(video,start,end):
    with tempfile.TemporaryDirectory() as tmp:
        for ref,last in ((start,False),(end,True)):
            target=Path(tmp)/("end.png" if last else "start.png")
            _extract(video["path"],target,last)
            if hashlib.sha256(target.read_bytes()).hexdigest()!=ref["sha256"]:
                raise ValueError("Poster must be decoded from the exact delivered video")
