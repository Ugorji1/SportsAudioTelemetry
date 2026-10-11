import urllib.request
import json
import time

radio_streams = [
    ('Radio Kerry Live (Ireland)', 'http://playerservices.streamtheworld.com/api/livestream-redirect/RADIO_KERRY.mp3'),
    ('Highland Radio (Ireland)', 'http://playerservices.streamtheworld.com/api/livestream-redirect/HIGHLAND_RADIO.mp3'),
    ('South East Radio (Ireland)', 'https://playerservices.streamtheworld.com/api/livestream-redirect/SOUTH_EAST_RADIO.mp3'),
    ('East Coast FM (Ireland)', 'https://live-bauerie.sharp-stream.com/EASTCOAST'),
    ('BBC Radio Scotland FM', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_scotland_fm'),
    ('BBC Radio Solent (UK)', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_solent'),
    ('BBC Radio Cumbria (UK)', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_cumbria'),
    ('BBC Radio Oxford (UK)', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_oxford'),
    ('BBC Radio Kent (UK)', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_kent'),
    ('Ukhozi FM (South Africa)', 'https://playerservices.streamtheworld.com/api/livestream-redirect/UKHOZIFMAAC_SC'),
    ('Thobela FM (South Africa)', 'https://playerservices.streamtheworld.com/api/livestream-redirect/THOBELAAAC.aac'),
    ('Lesedi FM (South Africa)', 'https://playerservices.streamtheworld.com/api/livestream-redirect/LESEDIAAC_SC')
]

mixlr_channels = [
    ('Live 95 Sport (Treaty/Cobh)', 'sports-live95'),
    ('LMFM Sport Live 1 (Dundalk/Harps)', 'lmfm-sport-live-1'),
    ('LMFM Sport Live 2 (Regional)', 'lmfm-sport-live-2'),
    ('Torquay United TUFC Radio', 'officialtufc'),
    ('Tamworth FC Lambs Media', 'lambsmedia'),
    ('Wealdstone FC', 'wealdstone-fc'),
    ('Wealdstone FC (Alt)', 'wealdstonefc'),
    ('Braintree Town FC', 'braintree-town-fc'),
    ('Braintree Town FC (Alt)', 'braintreetownfc'),
    ('Solihull Moors', 'solihull-moors-fc'),
    ('Solihull Moors (Alt)', 'solihullmoorsfc'),
    ('Eastleigh FC', 'eastleigh-fc'),
    ('Chorley Magpie Radio', 'magpie-radio'),
    ('South Shields Mariners Live', 'marinerslive'),
    ('Chelmsford Radio Clarets', 'radio-clarets')
]

print("="*75)
print("1. TESTING 24/7 LIVE RADIO STREAMS")
print("="*75)
for name, url in radio_streams:
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            lat = (time.time() - t0) * 1000
            print(f"{name:<35} | [OK {resp.status}] | {lat:5.0f}ms | ACTIVE 24/7 🟢")
    except Exception as e:
        print(f"{name:<35} | [ERROR]    | {str(e)[:30]}")

print("\n" + "="*75)
print("2. TESTING MIXLR MATCHDAY CHANNELS (via API)")
print("="*75)
for name, slug in mixlr_channels:
    clean_slug = slug.replace('-', '')
    found = False
    for s in [slug, clean_slug]:
        api_url = f"https://apicdn.mixlr.com/v3/channel_view/{s}"
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                is_live = False
                stream_url = None
                broadcast_title = None
                for inc in data.get('included', []):
                    if inc.get('type') == 'broadcast':
                        is_live = True
                        stream_url = inc['attributes'].get('progressive_stream_url')
                        broadcast_title = inc['attributes'].get('title')
                
                status_desc = f"LIVE NOW 🔴: '{broadcast_title}'" if is_live else "VALID CHANNEL (Offline - Matchday Broadcast)"
                print(f"{name:<35} | [VALID SLUG: {s}] | {status_desc}")
                found = True
                break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
        except Exception as e:
            pass
    if not found:
        print(f"{name:<35} | [404 NOT FOUND] | Slug not active on Mixlr")

print("="*75)
