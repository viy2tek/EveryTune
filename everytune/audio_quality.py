"""Optional local metadata inspection. Never open network inputs or playlists."""
import asyncio
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

FORMATS={'mp3':'mp3','flac':'flac','wav':'wav','wave':'wav','ogg':'ogg','oga':'ogg','opus':'ogg',
         'm4a':'mov','alac':'mov','aac':'aac','aiff':'aiff','aif':'aiff','ape':'ape','wv':'wv','wma':'asf','dsf':'dsf','dff':'iff'}
MAX_HEADER=512*1024


def declared_quality(data):
    if not isinstance(data,dict):return None
    result={}
    for key,maximum in [('bit_rate',4294967295),('sample_rate',4294967295),('bits_per_sample',64),('channels',64)]:
        value=data.get(key)
        if isinstance(value,str) and value.isdecimal() and len(value)<=10:value=int(value)
        if type(value) is int and 0<value<=maximum:result[key]=value
    codec=data.get('codec')
    if isinstance(codec,str) and re.fullmatch(r'[a-zA-Z0-9_]{1,40}',codec):result['codec']=codec
    return result or None


def probe_quality(data):
    if not isinstance(data,dict):return None
    streams=data.get('streams') or []
    if not isinstance(streams,list):return None
    stream=next((s for s in streams if isinstance(s,dict) and s.get('codec_type')=='audio'),None)
    if not stream:return None
    depth=stream.get('bits_per_raw_sample')
    if depth in (None,'0',0):depth=stream.get('bits_per_sample')
    return declared_quality({'codec':stream.get('codec_name'),'bit_rate':stream.get('bit_rate'),
        'sample_rate':stream.get('sample_rate'),'bits_per_sample':depth,'channels':stream.get('channels')})


async def inspect_audio(path,filename):
    executable=shutil.which('ffprobe')
    format=FORMATS.get(Path(filename).suffix.lower().lstrip('.'))
    if not executable or not format:return None
    process=None
    try:
        # A forced demuxer prevents playlist discovery; only the local input protocol is enabled.
        process=await asyncio.create_subprocess_exec(executable,'-v','error','-protocol_whitelist','file',
            '-max_alloc','67108864','-threads','1','-f',format,
            *(['-enable_drefs','0','-use_absolute_path','0'] if format=='mov' else []),
            '-probesize',str(MAX_HEADER),'-analyzeduration','1000000','-select_streams','a:0',
            '-show_entries','stream=codec_type,codec_name,bit_rate,sample_rate,bits_per_raw_sample,bits_per_sample,channels',
            '-of','json','-i',str(path),stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,
            **({'creationflags':subprocess.CREATE_NO_WINDOW} if sys.platform=='win32' else {}))
        output,_=await asyncio.wait_for(process.communicate(),timeout=5)
        if process.returncode or len(output)>32768:return None
        return probe_quality(json.loads(output))
    except (OSError,TimeoutError,ValueError,TypeError,AttributeError):
        return None
    finally:
        if process and process.returncode is None:
            try:process.kill()
            except ProcessLookupError:pass
            await process.wait()
