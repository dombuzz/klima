"""Status der X-Sense-Rauchmelder abfragen und als smoke.json speichern.

Läuft als GitHub Action (siehe .github/workflows/rauchmelder.yml).
Zugangsdaten kommen aus den Umgebungsvariablen XSENSE_USER und XSENSE_PASS
(eigenes X-Sense-Konto, mit dem die Melder aus der App geteilt sind).

Die Datei enthält bewusst nur Raumnamen und Status, keine Seriennummern.
Für Alarme ist das nicht gedacht: die Abfrage läuft nur alle 30 Minuten.
"""
import json
import os
import sys
from datetime import datetime, timezone

OUT = sys.argv[1] if len(sys.argv) > 1 else 'smoke.json'
PREFIX = 'Rauchmelder | '


def clean_name(name: str) -> str:
    name = (name or '').strip()
    return name[len(PREFIX):] if name.startswith(PREFIX) else name


def to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def to_bool(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    return str(v) == '1'


def main():
    user, pw = os.environ.get('XSENSE_USER'), os.environ.get('XSENSE_PASS')
    if not user or not pw:
        sys.exit('XSENSE_USER und XSENSE_PASS fehlen')

    from xsense import XSense
    api = XSense()
    api.init()
    api.login(user, pw)
    api.load_all()

    melder = []
    for house in api.houses.values():
        for st in (house.stations or {}).values():
            for call in (api.get_station_state, api.get_state):
                try:
                    call(st)
                except Exception as e:  # einzelne Abfragen dürfen fehlschlagen
                    print(f'Hinweis: {call.__name__} für {st.type}: {e}')

            # WLAN-Melder ohne Basis: der Melder ist selbst die «Station»
            devices = list((st.devices or {}).values()) or [st]
            for d in devices:
                data = dict(st.data) if d is not st else {}
                data.update(d.data)
                # Nur Feldnamen loggen (Repo ist öffentlich, Logs auch)
                print(f'{d.type}: Felder {sorted(data.keys())}')
                online = d.online if d.online is not None else st.online
                melder.append({
                    'name': clean_name(d.name or st.name),
                    'typ': d.type or st.type,
                    'online': bool(online) if online is not None else None,
                    'batterie': to_int(data.get('batInfo')),      # 0 leer … 3 voll
                    'wlan': to_int(data.get('wifiRSSI')),         # dBm
                    'alarm': to_bool(data.get('alarmStatus')),
                    'lebensende': to_bool(data.get('isLifeEnd')),
                })

    melder.sort(key=lambda m: m['name'])
    out = {
        'checked': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'melder': melder,
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'{len(melder)} Melder gespeichert')


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        # Als Annotation ausgeben, damit der Grund in der Übersicht des Laufs steht
        print(f'::error::{type(e).__name__}: {e}')
        sys.exit(1)
