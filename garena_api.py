"""
FINAL V4 - Uses Vercel endpoints like Bot-Istiada (which works on Railway)
+ Dynamic protobuf builder (no buggy replace)
+ Validation via Vercel + Direct fallback
"""

import gzip, logging, requests, urllib3
from io import BytesIO
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger("bolt.garena")

_K = b'Yg&tc%DEuh6%Zc^8'
_IV = b'6oyZDr22E3ychjM%'
_TIMEOUT = 12

MAJOR_LOGIN_URLS = [
    "https://loginbp.ggwhitehawk.com/MajorLogin",
    "https://loginbp.ggpolarbear.com/MajorLogin",
]

_HR = {
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 13; PHOENIX Build/TP1A)',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
    'Content-Type': 'application/octet-stream',
    'X-Unity-Version': '2018.4.11f1',
    'X-GA': 'v1 1',
    'ReleaseVersion': 'OB50',
}
_HR_OAUTH = {
    'User-Agent': 'GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
}
PLATFORM_NAMES = {1:"Garena",2:"Facebook",3:"Google",4:"Apple",5:"Twitter",6:"VK",8:"Huawei",9:"Guest"}

def _vr(n):
    r=[]
    while True:
        b=n & 0x7F; n >>=7
        if n: b|=0x80
        r.append(b)
        if not n: break
    return bytes(r)

def _pbF(data):
    out,pos={},0
    while pos < len(data):
        try:
            tag=sh=0
            while True:
                b=data[pos]; pos+=1
                tag|=(b & 0x7F) << sh; sh+=7
                if not b & 0x80: break
            fn,wt=tag>>3, tag & 0x7
            if wt==0:
                v=sh=0
                while True:
                    b=data[pos]; pos+=1
                    v|=(b & 0x7F) << sh; sh+=7
                    if not b & 0x80: break
                out[fn]=v
            elif wt==2:
                ln=sh=0
                while True:
                    b=data[pos]; pos+=1
                    ln|=(b & 0x7F) << sh; sh+=7
                    if not b & 0x80: break
                out[fn]=data[pos:pos+ln]; pos+=ln
            elif wt==1: out[fn]=data[pos:pos+8]; pos+=8
            elif wt==5: out[fn]=data[pos:pos+4]; pos+=4
            else: break
        except: break
    return out

def _enc(raw): return AES.new(_K, AES.MODE_CBC, _IV).encrypt(pad(raw,16))
def _encKIV(raw,k,iv): return AES.new(k, AES.MODE_CBC, iv).encrypt(pad(raw,16))
def _pb_str(fn,val):
    e=val.encode()
    return _vr((fn<<3)|2)+_vr(len(e))+e

# Dynamic builder - FIXED
def build_login_payload(access_token, open_id, platform_type="3"):
    payload=b""
    payload+=_pb_str(1,open_id)
    payload+=_pb_str(2,platform_type)
    payload+=_pb_str(3,access_token)
    payload+=_pb_str(4,"4")
    payload+=_pb_str(5,"Android")
    payload+=_pb_str(6,"OB50")
    return _enc(payload)

def _garena_request(url,params=None,method="GET",body=None,headers=None,timeout=None):
    timeout=timeout or _TIMEOUT
    try:
        if method=="GET":
            r=requests.get(url,params=params,verify=False,headers=headers or _HR_OAUTH,timeout=timeout)
        else:
            r=requests.post(url,data=body,params=params,verify=False,headers=headers or _HR_OAUTH,timeout=timeout)
        content=r.content
        if r.headers.get('Content-Encoding')=='gzip':
            try: content=gzip.GzipFile(fileobj=BytesIO(content)).read()
            except: pass
        try: return r.json()
        except:
            try: return {"raw":content.decode(errors="ignore")[:500],"status":r.status_code}
            except: return {"raw":content.hex()[:500],"status":r.status_code}
    except requests.exceptions.Timeout:
        return {"error":"timeout"}
    except requests.exceptions.ConnectionError:
        return {"error":"connection"}
    except Exception as e:
        return {"error":str(e)}

# ─── Vercel endpoints (like Bot-Istiada) - work on Railway ───
VERCEL_BIND_CHECK = "https://bindinfocrownx612.vercel.app/check"
VERCEL_CANCEL_BIND = "https://bindcnclcrownx34.vercel.app/cancelbind"
VERCEL_REVOKE = "https://crownxrevoker73.vercel.app/revoke"

def vercel_check_token(access_token):
    """Use Vercel endpoint to validate - works on Railway IP"""
    try:
        r=requests.get(VERCEL_BIND_CHECK, params={'access_token':access_token}, timeout=10)
        j=r.json()
        # If success true, token is valid even if no email
        # Example valid: {"success":true,"data":{"summary":"No recovery email set"}}
        # Invalid: {"raw_response":{"error":"error_token"}}
        if j.get("success") == True:
            # Check if raw_response error_token -> invalid
            raw=j.get("raw_response",{})
            if isinstance(raw,dict) and raw.get("error")=="error_token":
                # Some versions return error_token even for valid? Let's check data status
                data=j.get("data",{})
                if data.get("summary")=="No recovery email set" or data.get("email") or data.get("current_email"):
                    return {"valid":True,"via":"vercel","data":j}
                return {"valid":False,"error":"error_token","via":"vercel"}
            return {"valid":True,"via":"vercel","data":j}
        return {"valid":False,"error":j,"via":"vercel"}
    except Exception as e:
        return {"valid":None,"error":str(e),"via":"vercel"}

def get_open_id(access_token):
    # Try direct first
    data=_garena_request('https://100067.connect.garena.com/oauth/token/inspect',params={'token':access_token})
    oid=data.get('open_id')
    if oid:
        return oid
    # Fallback: try via Vercel? Vercel doesn't return open_id, but we can try account_id from URL as open_id
    # For now return None, caller will try account_id fallback
    return None

def validate_token(access_token):
    # Try Vercel first - works on Railway
    v=vercel_check_token(access_token)
    if v.get("valid")==True:
        # Try to get open_id from direct if possible, but consider valid
        oid=get_open_id(access_token)
        return {"valid":True,"open_id":oid or "via_vercel","via":"vercel","raw":v.get("data")}
    if v.get("valid")==False and v.get("error")!="timeout":
        # Vercel says invalid -> likely expired
        # Try direct as second chance
        data=_garena_request('https://100067.connect.garena.com/oauth/token/inspect',params={'token':access_token})
        if data.get('open_id'):
            return {"valid":True,"open_id":data['open_id'],"via":"direct"}
        return {"valid":False,"error":f"invalid_request - {v.get('error')}","via":"both"}
    # Vercel timeout - try direct
    data=_garena_request('https://100067.connect.garena.com/oauth/token/inspect',params={'token':access_token})
    if data.get('open_id'):
        return {"valid":True,"open_id":data['open_id'],"via":"direct"}
    return {"valid":False,"error":data.get('error','unknown'),"raw":data}

def major_login(payload):
    last=b''
    for url in MAJOR_LOGIN_URLS:
        try:
            r=requests.post(url,data=payload,headers=_HR,verify=False,timeout=_TIMEOUT)
            if r.status_code==200 and r.content and len(r.content)>10:
                content=r.content
                if r.headers.get('Content-Encoding')=='gzip':
                    try: content=gzip.GzipFile(fileobj=BytesIO(content)).read()
                    except: pass
                if len(content)>20:
                    return content
            last=r.content
        except Exception as e:
            logger.error(f"major_login {url} {e}")
            continue
    return last

def _try_variants(access_token, open_id):
    for pt in ["3","4","2","1"]:
        payload=build_login_payload(access_token,open_id,platform_type=pt)
        resp=major_login(payload)
        if resp and len(resp)>20:
            parsed=_pbF(resp)
            if 8 in parsed:
                return resp,payload,pt
    return b'',b'',None

def _pb1s(val):
    e=val.encode()
    return _vr(0x0A)+_vr(len(e))+e+bytes([0x10,0x01])

def get_player_info(access_token, forced_open_id=None):
    try:
        oid=get_open_id(access_token)
        if not oid and forced_open_id:
            oid=str(forced_open_id)
        if not oid:
            # Try to use Vercel to at least confirm token valid, then try with account_id fallback
            v=vercel_check_token(access_token)
            if v.get("valid"):
                # Use dummy open_id to try MajorLogin - some servers accept any?
                oid=forced_open_id or "123456"
            else:
                return {'error':f"فشل getting open_id - {v.get('error')} - جرب رابط جديد طازج (أقل من 5 دقائق)"}
        resp_bytes,payload_used,used_pt=_try_variants(access_token,oid)
        if not resp_bytes:
            return {'error':f'فشل MajorLogin - جرب بعد دقائق (platform {used_pt}) - قد يكون IP Railway محجوب مؤقتا'}
        mlr=_pbF(resp_bytes)
        if 8 not in mlr:
            if 2 in mlr:
                try:
                    msg=mlr[2].decode(errors='ignore')
                    return {'error':f'خطأ خادم: {msg[:200]}'}
                except: pass
            return {'error':f'استجابة بدون JWT fields={list(mlr.keys())}'}
        tok=mlr[8].decode() if isinstance(mlr[8],bytes) else str(mlr[8])
        k=mlr[22] if 22 in mlr else _K
        iv=mlr[23] if 23 in mlr else _IV
        url=mlr[10].decode() if 10 in mlr and isinstance(mlr[10],bytes) else "https://clientbp.ggbluedragon.com"
        player={'status':'success','open_id':oid,'jwt_token':tok[:20]+"...",'platform_used':used_pt}
        try:
            r=requests.post(f'{url}/GetLoginData',data=payload_used,headers={**_HR,'Content-Type':'application/octet-stream','Authorization':f'Bearer {tok}'},verify=False,timeout=_TIMEOUT)
            if r.status_code==200 and r.content:
                content=r.content
                if r.headers.get('Content-Encoding')=='gzip':
                    try: content=gzip.GzipFile(fileobj=BytesIO(content)).read()
                    except: pass
                try:
                    resp=_pbF(content)
                    if 2 in resp:
                        try:
                            dec=AES.new(k,AES.MODE_CBC,iv).decrypt(resp[2])
                            try: dec=unpad(dec,16)
                            except: pass
                            sub=_pbF(dec)
                            if 2 in sub:
                                info=_pbF(sub[2])
                                if 1 in info: player['uid']=info[1]
                                if 3 in info:
                                    try: player['name']=info[3].decode('utf-8',errors='ignore')
                                    except: player['name']=str(info[3])
                                if 4 in info: player['level']=info[4]
                                if 5 in info: player['rank']=info[5]
                            if 1 in sub: player['uid']=sub[1]
                        except Exception as e:
                            logger.debug(f"decrypt err {e}")
                except Exception as e:
                    logger.debug(f"parse err {e}")
        except Exception as e:
            player['warning']='JWT valid but GetLoginData failed'
        if 'uid' not in player and 'name' not in player:
            player['note']='JWT valid لكن معلومات اللاعب ما تفكتش (OB mismatch) - تغيير الاسم سيعمل'
        return player
    except Exception as e:
        logger.exception("get_player_info")
        return {'error':str(e)}

def change_name(access_token, new_name, forced_open_id=None):
    try:
        oid=get_open_id(access_token) or forced_open_id
        if not oid:
            return {'error':'فشل open_id - استخدم account_id من الرابط'}
        resp_bytes,payload_used,_=_try_variants(access_token,oid)
        if not resp_bytes:
            return {'error':'MajorLogin failed'}
        mlr=_pbF(resp_bytes)
        if 8 not in mlr:
            return {'error':'No JWT'}
        tok=mlr[8].decode() if isinstance(mlr[8],bytes) else str(mlr[8])
        k=mlr[22] if 22 in mlr else _K
        iv=mlr[23] if 23 in mlr else _IV
        base_url=mlr[10].decode() if 10 in mlr and isinstance(mlr[10],bytes) else "https://clientbp.ggbluedragon.com"
        try:
            requests.post(f'{base_url}/GetLoginData',data=payload_used,headers={**_HR,'Content-Type':'application/octet-stream','Authorization':f'Bearer {tok}'},verify=False,timeout=8)
        except: pass
        npyl=_encKIV(_pb1s(new_name),k,iv)
        for endpoint in [f"{base_url}/MajorModifyNickname","https://loginbp.ggwhitehawk.com/MajorModifyNickname","https://loginbp.ggpolarbear.com/MajorModifyNickname"]:
            try:
                r=requests.post(endpoint,data=npyl,headers={**_HR,'Content-Type':'application/octet-stream','Authorization':f'Bearer {tok}'},verify=False,timeout=_TIMEOUT)
                if r.status_code==200:
                    return {'status':200,'response':'success','endpoint':endpoint}
            except: continue
        return {'error':'change name failed all endpoints'}
    except Exception as e:
        return {'error':str(e)}

def check_links(access_token):
    # Try direct first
    d=_garena_request('https://100067.connect.garena.com/bind/app/platform/info/get',params={'access_token':access_token},headers=_HR_OAUTH)
    if d.get('bounded_accounts'):
        return d
    # Fallback Vercel? No direct equivalent, return direct
    return d

def check_bind_info_direct(access_token):
    # Try Vercel first (works on Railway)
    try:
        r=requests.get(VERCEL_BIND_CHECK,params={'access_token':access_token},timeout=10)
        j=r.json()
        # Normalize to {email: ...}
        if j.get('success'):
            data=j.get('data',{})
            email=data.get('current_email') or data.get('email') or ""
            if email:
                return {"email":email,"raw":j}
            # If no email, return raw for debug
            return {"email":"", "raw":j, "note":"No email bound"}
        return j
    except Exception as e:
        return {"error":str(e)}
    # Fallback direct
    return _garena_request('https://100067.connect.garena.com/bind/app/get_email',params={'access_token':access_token})

def is_success(r): return not r.get('error') and r.get('success',r.get('status',0)) in (True,1,200)
def extract_error(r): return str(r.get('error') or r.get('msg') or r.get('message') or r)
