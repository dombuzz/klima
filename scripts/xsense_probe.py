"""Einmalige Diagnose: welche Daten liefert die X-Sense-Cloud für die Melder?

Gibt nur Feldnamen und unkritische Werte als Annotationen aus.
"""
import os

from xsense import XSense

SAFE = {'batInfo', 'isLifeEnd', 'alarmStatus', 'muteStatus', 'onLine', 'online', 'wifiRSSI',
        'wifiRssi', 'rfLevel', 'onlineTime', 'activate', 'lifeEnd', 'batLevel', 'battery'}


def keys(d, depth=0):
    out = []
    for k, v in (d or {}).items():
        if isinstance(v, dict) and depth < 2:
            out.append(f'{k}{{{",".join(keys(v, depth + 1))}}}')
        else:
            out.append(f'{k}={v}' if k in SAFE else k)
    return out


api = XSense()
api.init()
api.login(os.environ['XSENSE_USER'], os.environ['XSENSE_PASS'])
api.load_all()
raw = api.get_stations(next(iter(api.houses)))
for s in raw.get('stations', []):
    print(f'::notice::Liste {s.get("category")}: {keys(s)}')
for house in api.houses.values():
    for st in house.stations.values():
        print(f'::notice::{st.type} devices={len(st.devices or {})}')
        for page in ('2nd_mainpage', 'mainpage', f'info_{st.sn}', f'2nd_info_{st.sn}',
                     f'2nd_systime', f'2nd_status_{st.sn}', f'status_{st.sn}'):
            try:
                res = api.get_thing(st, page)
                code = api._lastres.status_code
                rep = res.get('state', {}).get('reported', {})
                print(f'::notice::{st.type} {page.replace(st.sn, "SN")}: {code} {keys(rep)}'[:900])
            except Exception as e:
                print(f'::notice::{st.type} {page.replace(st.sn, "SN")}: {type(e).__name__}')
        break
    break
