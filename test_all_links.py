import time
import http.client
import urllib.parse

verified_test_links = [
    ('Radio Kerry Live (Ireland)', 'http://playerservices.streamtheworld.com/api/livestream-redirect/RADIO_KERRY.mp3'),
    ('Shannonside FM (Ireland)', 'http://edge.audioxi.com/SHANNONSIDE'),
    ('Highland Radio (Ireland)', 'http://playerservices.streamtheworld.com/api/livestream-redirect/HIGHLAND_RADIO.mp3'),
    ('Galway Bay FM (Ireland)', 'https://wg.cdn.tibus.net/galwaybay.mp3'),
    ('Live 95FM Limerick (Ireland)', 'https://wg.cdn.tibus.net/Live95fm'),
    ('LMFM Sports (Ireland)', 'https://wg.cdn.tibus.net/LMFM'),
    ('Cork 96FM / RedFM (Ireland)', 'https://wg.cdn.tibus.net/Cork96'),
    ('South East Radio (Ireland)', 'https://playerservices.streamtheworld.com/api/livestream-redirect/SOUTH_EAST_RADIO.mp3'),
    ('East Coast FM (Ireland)', 'https://live-bauerie.sharp-stream.com/EASTCOAST'),
    ('BBC Radio Scotland (Scotland)', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_scotland_fm'),
    ('BBC Radio Solent (UK)', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_solent'),
    ('BBC Radio Cumbria (UK)', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_cumbria'),
    ('BBC Radio Oxford (UK)', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_oxford'),
    ('BBC Radio Kent (UK)', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_kent'),
    ('Ukhozi FM (South Africa)', 'https://playerservices.streamtheworld.com/api/livestream-redirect/UKHOZIFMAAC_SC'),
    ('Thobela FM (South Africa)', 'https://playerservices.streamtheworld.com/api/livestream-redirect/THOBELAAAC.aac'),
    ('Lesedi FM (South Africa)', 'https://playerservices.streamtheworld.com/api/livestream-redirect/LESEDIAAC_SC')
]

def test_url(url, timeout=3.5):
    parsed = urllib.parse.urlparse(url)
    is_https = parsed.scheme == 'https'
    host = parsed.netloc
    path = parsed.path
    if parsed.query:
        path += '?' + parsed.query
        
    t0 = time.time()
    conn = None
    try:
        if is_https:
            conn = http.client.HTTPSConnection(host, timeout=timeout)
        else:
            conn = http.client.HTTPConnection(host, timeout=timeout)
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*'
        }
        conn.request('GET', path, headers=headers)
        res = conn.getresponse()
        lat = (time.time() - t0) * 1000
        status = res.status
        content_type = res.getheader('Content-Type', 'audio/mpeg')
        
        # Follow Redirects
        if status in (301, 302, 307, 308):
            loc = res.getheader('Location')
            conn.close()
            return test_url(loc, timeout)
            
        conn.close()
        return status, lat, content_type
    except Exception as e:
        if conn:
            conn.close()
        return 'ERROR', (time.time() - t0) * 1000, str(e)

print("==========================================================================")
print(f"{'STATION / CHANNEL NAME':<34} | {'STATUS':<8} | {'TIME':<7} | {'CONTENT-TYPE'}")
print("==========================================================================")

for name, url in verified_test_links:
    status, lat, c_type = test_url(url)
    if status == 200:
        print(f"{name:<34} | [OK 200]  | {lat:5.0f}ms | {c_type}")
    else:
        print(f"{name:<34} | [{status}] | {lat:5.0f}ms | {c_type[:25]}")

print("==========================================================================")
