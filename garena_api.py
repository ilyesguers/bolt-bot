"""
BOLT V7 FINAL - Real info, no dummy 123456 lie
- Correct field numbers 22,23,29,99
- Real player info from URL + server
"""

import gzip, logging, requests, urllib3
from io import BytesIO
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
    'ReleaseVersion': 'OB54',
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

def build_login_payload(access_token, open_id, platform_type="3", orign_platform="4"):
    payload=b""
    payload+=_pb_str(22, open_id)
    payload+=_pb_str(23, platform_type)
    payload+=_pb_str(29, access_token)
    payload+=_pb_str(99, orign_platform)
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
    except Exception as e:
        return {"error":str(e)}

VERCEL_BIND_CHECK = "https://bindinfocrownx612.vercel.app/check"

def vercel_check_token(access_token):
    try:
        r=requests.get(VERCEL_BIND_CHECK, params={'access_token':access_token}, timeout=10)
        j=r.json()
        if j.get("success")==True:
            return {"valid":True,"via":"vercel","data":j}
        return {"valid":False,"error":j,"via":"vercel"}
    except Exception as e:
        return {"valid":None,"error":str(e),"via":"vercel"}

def get_open_id(access_token):
    data=_garena_request('https://100067.connect.garena.com/oauth/token/inspect',params={'token':access_token})
    return data.get('open_id')

def validate_token(access_token):
    v=vercel_check_token(access_token)
    if v.get("valid")==True:
        oid=get_open_id(access_token)
        return {"valid":True,"open_id":oid or "via_vercel","via":"vercel","raw":v.get("data")}
    data=_garena_request('https://100067.connect.garena.com/oauth/token/inspect',params={'token':access_token})
    if data.get('open_id'):
        return {"valid":True,"open_id":data['open_id'],"via":"direct"}
    return {"valid":False,"error":"invalid_request","via":"both"}

def major_login(payload):
    last=b''
    for url in MAJOR_LOGIN_URLS:
        try:
            r=requests.post(url,data=payload,headers=_HR,verify=False,timeout=_TIMEOUT)
            if r.status_code==200 and r.content and len(r.content)>20:
                content=r.content
                if r.headers.get('Content-Encoding')=='gzip':
                    try: content=gzip.GzipFile(fileobj=BytesIO(content)).read()
                    except: pass
                return content
            last=r.content
        except: continue
    return last

def _try_variants(access_token, open_id):
    for pt in ["3","4","2"]:
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

def get_player_info(access_token, forced_open_id=None, nickname_fallback=None, region_fallback=None):
    """Real info, no lie - uses forced_open_id=account_id and nickname from URL when server fails"""
    try:
        oid=get_open_id(access_token)
        if not oid:
            oid=forced_open_id
        if not oid:
            return {'error': 'لا يمكن الحصول على OpenID - التوكن منتهي، جيب رابط جديد طازج'}

        resp_bytes,payload_used,used_pt=_try_variants(access_token,oid)
        if not resp_bytes:
            # Even if MajorLogin fails, return real info from URL
            return {
                'status':'partial',
                'open_id':oid,
                'uid':oid if str(oid).isdigit() else None,
                'name':nickname_fallback,
                'region':region_fallback,
                'platform_used':used_pt,
                'note':'MajorLogin فشل (IP محجوب) لكن هذه معلوماتك من الرابط نفسه - حقيقية 100%',
                'source':'url'
            }

        mlr=_pbF(resp_bytes)
        if 8 not in mlr:
            return {'error': f'MajorLogin بدون JWT'}

        tok=mlr[8].decode() if isinstance(mlr[8],bytes) else str(mlr[8])
        k=mlr[22] if 22 in mlr else _K
        iv=mlr[23] if 23 in mlr else _IV
        url=mlr[10].decode() if 10 in mlr and isinstance(mlr[10],bytes) else "https://clientbp.ggbluedragon.com"
        if not url.startswith("http"): url="https://clientbp.ggbluedragon.com"

        player={
            'status':'success',
            'open_id':oid,
            'jwt_token':tok[:20]+"...",
            'platform_used':used_pt,
            'server_url':url,
            'uid':int(oid) if str(oid).isdigit() else None,
            'name':nickname_fallback,
            'region':region_fallback,
            'source':'jwt+url'
        }

        # Try GetLoginData decryption for level/rank
        try:
            r=requests.post(f'{url}/GetLoginData',data=payload_used,headers={**_HR,'Content-Type':'application/octet-stream','Authorization':f'Bearer {tok}'},verify=False,timeout=_TIMEOUT)
            if r.status_code==200 and r.content:
                content=r.content
                if r.headers.get('Content-Encoding')=='gzip':
                    try: content=gzip.GzipFile(fileobj=BytesIO(content)).read()
                    except: pass
                resp=_pbF(content)
                # Try decrypt all candidates
                for fn in [2,5,7,12]:
                    if fn in resp and isinstance(resp[fn],bytes) and len(resp[fn])>=16:
                        try:
                            dec=AES.new(k,AES.MODE_CBC,iv).decrypt(resp[fn])
                            try: dec=unpad(dec,16)
                            except: pass
                            sub=_pbF(dec)
                            # Nested
                            for sfn in [2,1]:
                                if sfn in sub and isinstance(sub[sfn],bytes):
                                    info=_pbF(sub[sfn])
                                    if 1 in info: player['uid']=info[1]
                                    if 3 in info:
                                        try: player['name']=info[3].decode('utf-8',errors='ignore')
                                        except: player['name']=str(info[3])
                                    if 4 in info: player['level']=info[4]
                                    if 5 in info: player['rank']=info[5]
                                    if 8 in info:
                                        try: player['region']=info[8].decode('utf-8',errors='ignore')
                                        except: pass
                            if 1 in sub: player['uid']=sub[1]
                            if 3 in sub and isinstance(sub[3],bytes):
                                try: player['name']=sub[3].decode('utf-8',errors='ignore')
                                except: pass
                            if 4 in sub: player['level']=sub[4]
                            if 5 in sub: player['rank']=sub[5]
                        except: continue
                # If still no level, keep what we have from URL
                if player.get('level'):
                    player['note']='معلومات كاملة حقيقية من Garena'
                else:
                    player['note']='معلومات أساسية من الرابط + JWT صالح - الليفل يحتاج OB تحديث'
        except Exception as e:
            player['warning']=str(e)

        return player
    except Exception as e:
        logger.exception("get_player_info")
        return {'error':str(e)}

def change_name(access_token, new_name, forced_open_id=None):
    try:
        oid=get_open_id(access_token) or forced_open_id
        if not oid:
            return {'error':'فشل open_id'}
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
        return {'error':'change name failed'}
    except Exception as e:
        return {'error':str(e)}

def check_links(access_token):
    return _garena_request('https://100067.connect.garena.com/bind/app/platform/info/get',params={'access_token':access_token},headers=_HR_OAUTH)

def check_bind_info_direct(access_token):
    try:
        r=requests.get(VERCEL_BIND_CHECK,params={'access_token':access_token},timeout=10)
        j=r.json()
        if j.get('success'):
            data=j.get('data',{})
            email=data.get('current_email') or data.get('email') or ""
            return {"email":email,"raw":j,"summary":data.get('summary','')}
        return {"raw":j}
    except Exception as e:
        return {"error":str(e)}
