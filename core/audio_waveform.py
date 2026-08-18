
import os 
import struct 
import wave 
from typing import List ,Optional 

_soundfile_checked =False 
_soundfile_module =None 
_miniaudio_checked =False 
_miniaudio_module =None 


def _get_soundfile ():

    global _soundfile_checked ,_soundfile_module 
    if not _soundfile_checked :
        try :
            import soundfile as sf 
            _soundfile_module =sf 
        except ImportError :
            _soundfile_module =None 
        _soundfile_checked =True 
    return _soundfile_module 


def _get_miniaudio ():

    global _miniaudio_checked ,_miniaudio_module 
    if not _miniaudio_checked :
        try :
            import miniaudio 
            _miniaudio_module =miniaudio 
        except ImportError :
            _miniaudio_module =None 
        _miniaudio_checked =True 
    return _miniaudio_module 


def soundfile_available ()->bool :
    return _get_soundfile ()is not None 


def miniaudio_available ()->bool :
    return _get_miniaudio ()is not None 


def _peaks_from_samples (samples ,max_val :float ,num_buckets :int )->List [float ]:
    bucket_size =max (1 ,len (samples )//max (1 ,num_buckets ))
    peaks :List [float ]=[]
    for i in range (0 ,len (samples ),bucket_size ):
        chunk =samples [i :i +bucket_size ]
        if not chunk :
            continue 
        peak =max (abs (s )for s in chunk )/max_val 
        peaks .append (min (1.0 ,peak ))
    return peaks [:num_buckets ]if peaks else []


def _extract_peaks_wave (path :str ,num_buckets :int )->Optional [List [float ]]:

    try :
        with wave .open (path ,"rb")as wf :
            n_frames =wf .getnframes ()
            sampwidth =wf .getsampwidth ()
            n_channels =max (1 ,wf .getnchannels ())
            if n_frames <=0 or sampwidth not in (1 ,2 ,4 ):
                return None 
            raw =wf .readframes (n_frames )
    except (wave .Error ,EOFError ,OSError ):
        return None 

    if sampwidth ==2 :
        count =len (raw )//2 
        if count ==0 :
            return []
        samples =struct .unpack (f"<{count }h",raw [:count *2 ])
        max_val =32768.0 
    elif sampwidth ==1 :
        if not raw :
            return []
        samples =[b -128 for b in raw ]
        max_val =128.0 
    else :
        count =len (raw )//4 
        if count ==0 :
            return []
        samples =struct .unpack (f"<{count }i",raw [:count *4 ])
        max_val =float (2 **31 )

    if n_channels >1 :

        samples =samples [::n_channels ]

    return _peaks_from_samples (samples ,max_val ,num_buckets )


def _extract_peaks_miniaudio (path :str ,num_buckets :int )->List [float ]:

    ma =_get_miniaudio ()
    if ma is None :
        return []
    try :
        decoded =ma .decode_file (path ,output_format =ma .SampleFormat .SIGNED16 ,nchannels =1 )
        samples =decoded .samples 
    except Exception :
        return []
    if not samples :
        return []
    return _peaks_from_samples (list (samples ),32768.0 ,num_buckets )


def _extract_peaks_soundfile (path :str ,num_buckets :int )->List [float ]:
    sf =_get_soundfile ()
    if sf is None :
        return []
    try :
        data ,_samplerate =sf .read (path ,dtype ="int16",always_2d =True )
    except Exception :
        return []
    if data .size ==0 :
        return []

    mono =data [:,0 ]
    return _peaks_from_samples (mono .tolist (),32768.0 ,num_buckets )


def extract_peaks (path :str ,num_buckets :int =600 ,timeout_sec :float =15.0 )->List [float ]:

    if not path or not os .path .isfile (path ):
        return []

    ext =os .path .splitext (path )[1 ].lower ()
    if ext ==".wav":
        result =_extract_peaks_wave (path ,num_buckets )
        if result :
            return result 



    result =_extract_peaks_miniaudio (path ,num_buckets )
    if result :
        return result 

    return _extract_peaks_soundfile (path ,num_buckets )
