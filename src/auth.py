"""
حماية بسيطة للوحة - Integrated Auth
إذا ضبطت DASHBOARD_TOKEN في Railway Variables، سيطلبها
"""
import os
from fastapi import Request, HTTPException

TOKEN = os.environ.get("DASHBOARD_TOKEN", "").strip()

def check_auth(request: Request):
    if not TOKEN:
        return True  # لا حماية إذا لم يضبط
    # يقبل ?token= أو Header
    q = request.query_params.get("token", "")
    h = request.headers.get("x-dashboard-token", "")
    if q == TOKEN or h == TOKEN:
        return True
    raise HTTPException(status_code=401, detail="Unauthorized - أضف ?token=YOUR_TOKEN")
