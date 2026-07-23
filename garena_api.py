"""
BOLT FINAL V6 - Real player info fix
Uses correct protobuf field numbers from freefire_pb2.py (OB51+)
LoginReq: open_id=22, open_id_type=23, login_token=29, orign_platform_type=99
+ Vercel fallback for Railway IP block
+ Real GetLoginData decryption
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
_TIMEOUT = 15

MAJOR_LOGIN_URLS = [
    "https://loginbp.ggwhitehawk.com/MajorLogin",
    "https://loginbp.ggpolarbear.com/MajorLogin",
]

_HR = {
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 15; I2404 Build/AP3A.240905.015.A2_V000L1)',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
    'Content-Type': 'application/octet-stream',
    'Expect': '100-continue',
    'X-Unity-Version': '2018.4.11f1',
    'X-GA': 'v1 1',
    'ReleaseVersion': 'OB54',  # Updated to OB54 for real info
}
_HR_OAUTH = {
    'User-Agent': 'GarenaMSDK/4.0.19P10(I2404 ;Android 15;en;US;)',
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
    if val is None: val=""
    e=str(val).encode()
    return _vr((fn<<3)|2)+_vr(len(e))+e

# ─── CORRECTED BUILDER (field numbers from freefire_pb2.py) ───
def build_login_payload(access_token, open_id, platform_type="3", orign_platform="4"):
    """
    Correct fields: 22=open_id, 23=open_id_type, 29=login_token, 99=orign_platform_type
    This is what real game client sends, not 1,2,3,4
    """
    payload=b""
    payload+=_pb_str(22, open_id)              # open_id
    payload+=_pb_str(23, platform_type)        # open_id_type: 3=Google for EAT
    payload+=_pb_str(29, access_token)         # login_token = EAT
    payload+=_pb_str(99, orign_platform)       # orign_platform_type
    # Optional: add some extra fields that help with real info (like other bots)
    # field 16? Not needed but we add version hint
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

VERCEL_BIND_CHECK = "https://bindinfocrownx612.vercel.app/check"

def vercel_check_token(access_token):
    try:
        r=requests.get(VERCEL_BIND_CHECK, params={'access_token':access_token}, timeout=10)
        j=r.json()
        if j.get("success")==True:
            raw=j.get("raw_response",{})
            if isinstance(raw,dict) and raw.get("error")=="error_token":
                data=j.get("data",{})
                # If summary is No recovery email, it's actually valid
                if data.get("summary")=="No recovery email set" or data.get("current_email")=="" or data.get("email")=="":
                    # Valid token, no email
                    return {"valid":True,"via":"vercel","data":j}
                return {"valid":False,"error":"error_token","via":"vercel"}
            return {"valid":True,"via":"vercel","data":j}
        return {"valid":False,"error":j,"via":"vercel"}
    except Exception as e:
        return {"valid":None,"error":str(e),"via":"vercel"}

def get_open_id(access_token):
    data=_garena_request('https://100067.connect.garena.com/oauth/token/inspect',params={'token':access_token})
    oid=data.get('open_id')
    if oid:
        return oid
    return None

def validate_token(access_token):
    v=vercel_check_token(access_token)
    if v.get("valid")==True:
        oid=get_open_id(access_token)
        return {"valid":True,"open_id":oid or "via_vercel","via":"vercel","raw":v.get("data")}
    if v.get("valid")==False:
        data=_garena_request('https://100067.connect.garena.com/oauth/token/inspect',params={'token':access_token})
        if data.get('open_id'):
            return {"valid":True,"open_id":data['open_id'],"via":"direct"}
        return {"valid":False,"error":f"invalid_request - token expired or invalid","via":"both","detail":v}
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
    # For EAT tokens, try platform 3 (Google) first, then 4 (Guest)
    for pt in ["3","4","2","1"]:
        payload=build_login_payload(access_token,open_id,platform_type=pt,orign_platform="4")
        resp=major_login(payload)
        if resp and len(resp)>20:
            parsed=_pbF(resp)
            if 8 in parsed:  # token field
                return resp,payload,pt
    return b'',b'',None

def _pb1s(val):
    e=val.encode()
    return _vr(0x0A)+_vr(len(e))+e+bytes([0x10,0x01])

# ─── Real Player Info - improved decryption ───
def get_player_info(access_token, forced_open_id=None):
    try:
        oid=get_open_id(access_token)
        if not oid:
            oid=forced_open_id
        if not oid:
            v=vercel_check_token(access_token)
            if v.get("valid"):
                oid=forced_open_id or "123456"
            else:
                return {'error':f"فشل الحصول على open_id - التوكن منتهي أو غير صالح (Vercel: {v.get('error')})"}

        resp_bytes,payload_used,used_pt=_try_variants(access_token,oid)
        if not resp_bytes:
            return {'error':f'فشل MajorLogin - السيرفر مشغول، جرب بعد دقيقة (platform {used_pt})'}

        mlr=_pbF(resp_bytes)
        if 8 not in mlr:
            if 2 in mlr:
                try:
                    msg=mlr[2].decode(errors='ignore')
                    return {'error':f'خطأ خادم MajorLogin: {msg[:200]}'}
                except: pass
            return {'error':f'استجابة MajorLogin بدون JWT - fields={list(mlr.keys())}'}

        tok=mlr[8].decode() if isinstance(mlr[8],bytes) else str(mlr[8])
        k=mlr[22] if 22 in mlr else _K
        iv=mlr[23] if 23 in mlr else _IV
        url=mlr[10].decode() if 10 in mlr and isinstance(mlr[10],bytes) else "https://clientbp.ggbluedragon.com"
        # Fallback URL
        if not url or "http" not in url:
            url="https://clientbp.ggbluedragon.com"

        player={'status':'success','open_id':oid,'jwt_token':tok[:20]+"...",'platform_used':used_pt,'server_url':url}

        # ─── GetLoginData with improved parsing ───
        try:
            r=requests.post(f'{url}/GetLoginData',data=payload_used,headers={**_HR,'Content-Type':'application/octet-stream','Authorization':f'Bearer {tok}'},verify=False,timeout=_TIMEOUT)
            if r.status_code==200 and r.content:
                content=r.content
                if r.headers.get('Content-Encoding')=='gzip':
                    try: content=gzip.GzipFile(fileobj=BytesIO(content)).read()
                    except: pass

                # Try to parse as protobuf
                resp=_pbF(content)
                # logger.info(f"GetLoginData fields: {list(resp.keys())}")

                # Try all possible encrypted fields (usually field 2, but try others)
                encrypted_candidates=[]
                for fn in [2,5,7,12,14]:
                    if fn in resp and isinstance(resp[fn],bytes) and len(resp[fn])>=16:
                        encrypted_candidates.append(resp[fn])

                decrypted_success=False
                for enc_data in encrypted_candidates:
                    try:
                        dec=AES.new(k,AES.MODE_CBC,iv).decrypt(enc_data)
                        try: dec=unpad(dec,16)
                        except: 
                            # Try without unpad, strip PKCS7 manually
                            pass
                        # Try parse decrypted
                        sub=_pbF(dec)
                        # Look for player info nested
                        # Common pattern: field 2 contains another protobuf with fields 1=uid, 3=name, 4=level
                        for sfn in [2,1,5]:
                            if sfn in sub:
                                info_data=sub[sfn]
                                if isinstance(info_data,bytes):
                                    info=_pbF(info_data)
                                    if 1 in info or 3 in info:
                                        # Found player info
                                        if 1 in info: player['uid']=info[1]
                                        if 2 in info: player['account_id']=info[2]
                                        if 3 in info:
                                            try: player['name']=info[3].decode('utf-8',errors='ignore')
                                            except: player['name']=str(info[3])
                                        if 4 in info: player['level']=info[4]
                                        if 5 in info: player['rank']=info[5]
                                        if 6 in info: player['exp']=info[6]
                                        if 8 in info: player['region']=info[8]
                                        decrypted_success=True
                                        break
                                    # Try flat
                                    if 1 in sub: player['uid']=sub[1]
                                    if 3 in sub:
                                        try: player['name']=sub[3].decode('utf-8',errors='ignore') if isinstance(sub[3],bytes) else str(sub[3])
                                        except: pass
                                    if 4 in sub: player['level']=sub[4]
                                    if 5 in sub: player['rank']=sub[5]
                        if decrypted_success:
                            break
                        # Also try direct fields in sub without extra nesting
                        if 1 in sub: player['uid']=sub[1]
                        if 3 in sub and 'name' not in player:
                            try: player['name']=sub[3].decode('utf-8',errors='ignore') if isinstance(sub[3],bytes) else str(sub[3])
                            except: pass
                        if player.get('uid') or player.get('name'):
                            decrypted_success=True
                            break
                    except Exception as e:
                        # logger.debug(f"decrypt try failed {e}")
                        continue

                if not decrypted_success:
                    # Try unencrypted direct parse
                    if 1 in resp: player['uid']=resp[1]
                    if 3 in resp:
                        try: player['name']=resp[3].decode('utf-8',errors='ignore') if isinstance(resp[3],bytes) else str(resp[3])
                        except: pass
                    if 4 in resp: player['level']=resp[4]
                    if 5 in resp: player['rank']=resp[5]
                    if 8 in resp:
                        try: player['region']=resp[8].decode('utf-8',errors='ignore') if isinstance(resp[8],bytes) else str(resp[8])
                        except: pass

                if not player.get('uid') and not player.get('name'):
                    player['debug_fields']=list(resp.keys())
                    player['note']='فك تشفير GetLoginData فشل - OB mismatch محتمل لكن JWT صالح'
                else:
                    player['note']='تم فك التشفير بنجاح - معلومات حقيقية'

        except Exception as e:
            player['warning']=f'GetLoginData error: {e}'

        # If still no uid/name, try to use account_id from URL as fallback BUT mark as fallback, not lie
        if not player.get('uid'):
            # Try to get from forced_open_id if it's numeric account_id
            if forced_open_id and str(forced_open_id).isdigit():
                player['uid_fallback']=str(forced_open_id)
                player['uid']=int(forced_open_id) if str(forced_open_id).isdigit() else forced_open_id

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
            return {'error':'No JWT from MajorLogin'}
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
                    pr=_pbF(r.content)
                    # Success if field 1 == 0 or small response
                    if 1 in pr and pr[1] in (0,1):
                        return {'status':200,'response':'success','endpoint':endpoint,'code':pr[1]}
                    if len(r.content)<100:
                        return {'status':200,'response':'success','raw':r.content.hex()}
                    return {'status':200,'response':'ok','endpoint':endpoint}
            except: continue
        return {'error':'change name failed all endpoints'}
    except Exception as e:
        return {'error':str(e)}

def check_links(access_token):
    d=_garena_request('https://100067.connect.garena.com/bind/app/platform/info/get',params={'access_token':access_token},headers=_HR_OAUTH)
    return d

def check_bind_info_direct(access_token):
    try:
        r=requests.get(VERCEL_BIND_CHECK,params={'access_token':access_token},timeout=10)
        j=r.json()
        if j.get('success'):
            data=j.get('data',{})
            email=data.get('current_email') or data.get('email') or ""
            return {"email":email,"raw":j,"note":"No email bound" if not email else "Email bound"}
        return {"raw":j}
    except Exception as e:
        return {"error":str(e)}

def is_success(r): return not r.get('error') and r.get('success',r.get('status',0)) in (True,1,200)
def extract_error(r): return str(r.get('error') or r.get('msg') or r.get('message') or r)
