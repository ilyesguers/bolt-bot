"""
BOLT ⚡ — Garena API Module
━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️ ONLY direct Garena APIs — no third-party Vercel endpoints
✅ Clean, validated, timeout-protected
📡 Operations: login, name change, bind info, links check, token validation
"""

import ssl
import gzip
import logging
import http.client
import requests
import urllib3
from io import BytesIO
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger("bolt.garena")

# ─── Constants ────────────────────────────────────────────────────────────────

_K  = b'Yg&tc%DEuh6%Zc^8'
_IV = b'6oyZDr22E3ychjM%'

_TIMEOUT = 15

_HR = {
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 13; PHOENIX Build/TP1A)',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Unity-Version': '2018.4.11f1',
    'X-GA': 'v1 1',
    'ReleaseVersion': 'OB53',
}

PLATFORM_NAMES = {
    1: "Garena", 2: "Facebook", 3: "Google", 4: "Apple",
    5: "Twitter", 6: "VK", 8: "Huawei", 9: "Guest",
    12: "Line", 14: "Amazon", 15: "PlayGames", 16: "AppleGameCenter",
    18: "Riot", 100: "Steam",
}

# ─── Protobuf Helpers ─────────────────────────────────────────────────────────

def _vr(n):
    r = []
    while True:
        b = n & 0x7F; n >>= 7
        if n: b |= 0x80
        r.append(b)
        if not n: break
    return bytes(r)

def _pbF(data):
    out, pos = {}, 0
    while pos < len(data):
        try:
            tag, sh = 0, 0
            while True:
                b = data[pos]; pos += 1
                tag |= (b & 0x7F) << sh; sh += 7
                if not b & 0x80: break
            fn, wt = tag >> 3, tag & 0x7
            if wt == 0:
                v, sh = 0, 0
                while True:
                    b = data[pos]; pos += 1
                    v |= (b & 0x7F) << sh; sh += 7
                    if not b & 0x80: break
                out[fn] = v
            elif wt == 2:
                ln, sh = 0, 0
                while True:
                    b = data[pos]; pos += 1
                    ln |= (b & 0x7F) << sh; sh += 7
                    if not b & 0x80: break
                out[fn] = data[pos:pos+ln]; pos += ln
            elif wt == 1: out[fn] = data[pos:pos+8]; pos += 8
            elif wt == 5: out[fn] = data[pos:pos+4]; pos += 4
            else: break
        except: break
    return out

def _enc(raw):
    return AES.new(_K, AES.MODE_CBC, _IV).encrypt(pad(raw, 16))

def _encKIV(raw, k, iv):
    return AES.new(k, AES.MODE_CBC, iv).encrypt(pad(raw, 16))

def _pb1s(val):
    e = val.encode()
    return _vr(0x0A) + _vr(len(e)) + e + bytes([0x10, 0x01])

# ─── Device Template ──────────────────────────────────────────────────────────

_dT = bytes.fromhex(
    '1a13323032352d30372d33302031343a31313a3230220966726565206669726528013a07'
    '312e3132332e314234416e64726f6964204f53203133202f204150492d33332028545031'
    '412e3232303632342e3031342f3235303531355631393737294a0848616e6468656c6452'
    '094f72616e676520544e5a0457494649609c1368b80872033438307a1d41524d3634204650'
    '20415349444420414553207c2032303030207c20388001973c8a010c4d616c692d473532'
    '204d433292013e4f70656e474c20455320332e322076312e72333270312d3031656163302e'
    '32613839336330346361303032366332653638303264626537643761663563359a012b476f'
    '6f676c657c61326365613833342d353732362d346235622d383666322d373130356364386666'
    '353530a2010e3139362e3138372e3132382e3334aa0102656eb201203965373166616266343364'
    '383863303662373966353438313034633766636237ba010134c2010848616e6468656c64ca0115'
    '494e46494e495820496e66696e6978205836383336ea014063363231663264363231343330646163'
    '316137383261306461623634653663383061393734613662633732386366326536623132323464313836'
    '633962376166f00101ca02094f72616e676520544ed2020457494649ca03203161633462383065636630'
    '343738613434323033626638666163363132306635e003dc810ee803daa106f003ef068004e7a506'
    '8804dc810e9004e7a5069804dc810ec80403d2045b2f646174612f6170702f7e7e73444e524632'
    '526357313830465a4d66624d5a636b773d3d2f636f6d2e6474732e66726565666972656d61782d'
    '4a534d4f476d33464e59454271535376587767495a413d3d2f6c69622f61726d3634e00402ea047b'
    '61393862306265333734326162303061313966393737633637633031633266617c2f646174612f6170'
    '702f7e7e73444e524632526357313830465a4d66624d5a636b773d3d2f636f6d2e6474732e66726565'
    '666972656d61782d4a534d4f476d33464e59454271535376587767495a413d3d2f626173652e61706b'
    'f00402f804028a050236349a050a32303139313135363537a80503b205094f70656e474c455333b805'
    'ff7fc00504d20506526164c3a873da05023133e005b9f601ea050b616e64726f69645f6d6178f2055c'
    '4b71734854346230414a3777466c617231594d4b693653517a6732726b3665764f38334f306f59306763'
    '5a626457467a785633483564454f586a47704e3967476956774b7533547a312b716a36326546673074'
    '627537664350553d8206147b226375725f72617465223a5b36302c39305d7d8806019006019a060134a2060134b20600'
)

_AT_PH = b'61393862306265333734326162303061313966393737633637633031633266617c'
_OID_PH = b'4306245793de86da425a52caadf21eed'
_TS_PH = b'2025-07-30 14:11:20'


# ─── Core Garena Functions (DIRECT — no third-party) ──────────────────────────

def _garena_request(url: str, params: dict = None, method: str = "GET",
                     body: bytes = None, headers: dict = None, timeout: int = None) -> dict:
    """Safe Garena API request with error handling."""
    timeout = timeout or _TIMEOUT
    try:
        if method == "GET":
            r = requests.get(url, params=params, verify=False,
                             headers=headers or _HR, timeout=timeout)
        else:
            r = requests.post(url, data=body, params=params, verify=False,
                              headers=headers or _HR, timeout=timeout)
        # Handle gzip
        content = r.content
        if r.headers.get('Content-Encoding') == 'gzip':
            content = gzip.GzipFile(fileobj=BytesIO(content)).read()
        try:
            return r.json()
        except:
            return {"raw": content.hex(), "status": r.status_code}
    except requests.exceptions.Timeout:
        return {"error": "timeout", "msg": "انتهت مهلة الاتصال"}
    except requests.exceptions.ConnectionError:
        return {"error": "connection", "msg": "فشل الاتصال بالخادم"}
    except Exception as e:
        return {"error": str(e)}


def get_open_id(access_token: str) -> str | None:
    """Resolve access_token → open_id (DIRECT Garena API)."""
    data = _garena_request(
        'https://100067.connect.garena.com/oauth/token/inspect',
        params={'token': access_token}
    )
    return data.get('open_id')


def validate_token(access_token: str) -> dict:
    """Validate token with Garena — DIRECT call."""
    data = _garena_request(
        'https://100067.connect.garena.com/oauth/token/inspect',
        params={'token': access_token}
    )
    if data.get('open_id'):
        return {
            'valid': True,
            'open_id': data['open_id'],
            'expires': data.get('expires', 'غير معروف'),
            'app_id': data.get('app_id', ''),
        }
    return {'valid': False, 'error': data.get('error', 'رمز غير صالح')}


def major_login(payload: bytes) -> bytes:
    """Direct MajorLogin to Garena servers."""
    try:
        ctx = ssl._create_unverified_context()
        c = http.client.HTTPSConnection('loginbp.ggpolarbear.com', timeout=_TIMEOUT, context=ctx)
        c.request('POST', '/MajorLogin', body=payload, headers=_HR)
        rs = c.getresponse()
        raw = rs.read()
        if rs.getheader('Content-Encoding') == 'gzip':
            raw = gzip.GzipFile(fileobj=BytesIO(raw)).read()
        c.close()
        return raw
    except Exception as e:
        logger.error("major_login error: %s", e)
        return b''


def build_login_payload(access_token: str, open_id: str) -> bytes:
    ts = str(datetime.now())[:-7].encode()
    dT = _dT.replace(_TS_PH, ts)
    dT = dT.replace(_AT_PH, access_token.encode())
    dT = dT.replace(_OID_PH, open_id.encode())
    return _enc(dT)


# ─── Player Info (DIRECT) ─────────────────────────────────────────────────────

def get_player_info(access_token: str) -> dict:
    """
    Get player information — DIRECT Garena API calls only.
    No third-party APIs involved.
    """
    try:
        oid = get_open_id(access_token)
        if not oid:
            return {'error': 'فشل في التحقق من التوكن'}

        pyl = build_login_payload(access_token, oid)
        mr = major_login(pyl)
        if not mr:
            return {'error': 'فشل تسجيل الدخول'}

        mlr = _pbF(mr)
        if 8 not in mlr:
            return {'error': 'استجابة غير صالحة'}

        tok = mlr[8].decode()
        k = mlr[22] if 22 in mlr else _K
        iv = mlr[23] if 23 in mlr else _IV
        url = mlr[10].decode() if 10 in mlr else ''

        player = {'status': 'success', 'open_id': oid}

        # GetLoginData — direct Garena call
        if url:
            try:
                r = requests.post(
                    f'{url}/GetLoginData', data=pyl,
                    headers={**_HR, 'Authorization': f'Bearer {tok}'},
                    verify=False, timeout=_TIMEOUT
                )
                if r.status_code == 200 and r.content:
                    try:
                        resp = _pbF(r.content)
                        if 2 in resp:
                            dec = AES.new(k, AES.MODE_CBC, iv).decrypt(resp[2])
                            sub = _pbF(dec)
                            if 2 in sub:
                                info = _pbF(sub[2])
                                if 1 in info: player['uid'] = info[1]
                                if 3 in info: player['name'] = info[3].decode('utf-8', errors='ignore')
                                if 4 in info: player['level'] = info[4]
                                if 5 in info: player['rank'] = info[5]
                                if 6 in info: player['exp'] = info[6]
                    except Exception:
                        pass
            except Exception:
                pass

        return player
    except Exception as e:
        return {'error': str(e)}


# ─── Change Name (DIRECT) ─────────────────────────────────────────────────────

def change_name(access_token: str, new_name: str) -> dict:
    """Change in-game nickname — DIRECT Garena API."""
    try:
        oid = get_open_id(access_token)
        if not oid:
            return {'error': 'فشل في التحقق من التوكن'}

        pyl = build_login_payload(access_token, oid)
        mr = major_login(pyl)
        if not mr:
            return {'error': 'فشل تسجيل الدخول'}

        mlr = _pbF(mr)
        tok = mlr[8].decode()
        k = mlr[22] if 22 in mlr else _K
        iv = mlr[23] if 23 in mlr else _IV

        # GetLoginData
        try:
            requests.post(
                f'{mlr[10].decode()}/GetLoginData', data=pyl,
                headers={**_HR, 'Authorization': f'Bearer {tok}'},
                verify=False, timeout=8
            )
        except:
            pass

        npyl = _encKIV(_pb1s(new_name), k, iv)
        r = requests.post(
            'https://loginbp.ggpolarbear.com/MajorModifyNickname',
            data=npyl,
            headers={**_HR, 'Authorization': f'Bearer {tok}'},
            verify=False, timeout=_TIMEOUT
        )
        return {'status': r.status_code, 'response': r.content.hex()}
    except Exception as e:
        return {'error': str(e)}


# ─── Check Links (DIRECT Garena API) ──────────────────────────────────────────

def check_links(access_token: str) -> dict:
    """Check platform links — DIRECT Garena API."""
    return _garena_request(
        'https://100067.connect.garena.com/bind/app/platform/info/get',
        params={'access_token': access_token},
        headers={
            'User-Agent': 'GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
        }
    )


# ─── Bind Info (DIRECT Garena API) ────────────────────────────────────────────

def check_bind_info_direct(access_token: str) -> dict:
    """
    Check email bind info — DIRECT Garena API.
    Uses the official Garena crown endpoint.
    """
    return _garena_request(
        'https://100067.connect.garena.com/bind/app/get_email',
        params={'access_token': access_token}
    )


# ─── Utility ──────────────────────────────────────────────────────────────────

def is_success(response: dict) -> bool:
    if response.get('error'):
        return False
    return response.get('success', response.get('status', 0)) in (True, 1, 200)

def extract_error(response: dict) -> str:
    if response.get('error'):
        return str(response['error'])
    if response.get('msg'):
        return str(response['msg'])
    if response.get('message'):
        return str(response['message'])
    return str(response)

def convert_seconds(seconds) -> str:
    try:
        seconds = int(seconds)
    except:
        return "0s"
    if seconds <= 0:
        return "0s"
    d, r = divmod(seconds, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    parts = []
    if d: parts.append(f"{d}ي")
    if h: parts.append(f"{h}س")
    if m: parts.append(f"{m}د")
    if s: parts.append(f"{s}ث")
    return ' '.join(parts) if parts else "0s"
