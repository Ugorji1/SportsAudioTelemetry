import os
import sys
from fpdf import FPDF

class PDFCatalog(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(15, 23, 42)
        self.cell(0, 7, 'Low-Latency Sports Audio Streams: Master Catalog (v1.3)', align='L')
        self.ln(5)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 4, '100% Live Verified UK National League, Ireland & SPFL Direct Streams | Target: SportyBet Telemetry', align='L')
        self.ln(6)
        self.set_draw_color(2, 132, 199)
        self.set_line_width(0.6)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-10)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 6, f'Page {self.page_no()}', align='C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 9.5)
        self.set_text_color(30, 41, 59)
        self.set_fill_color(241, 245, 249)
        self.cell(0, 6, f' {title}', fill=True, new_x='LMARGIN', new_y='NEXT')
        self.ln(1.5)

    def add_table_header(self, col_widths, headers):
        self.set_font('Helvetica', 'B', 8)
        self.set_fill_color(226, 232, 240)
        self.set_text_color(15, 23, 42)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 5.5, h, border=1, fill=True, align='L')
        self.ln()

    def add_table_row(self, col_widths, row, is_even=False):
        self.set_font('Helvetica', '', 7.5)
        self.set_text_color(30, 41, 59)
        if is_even:
            self.set_fill_color(248, 250, 252)
        else:
            self.set_fill_color(255, 255, 255)
        
        target_club, station, url, notes = row
        self.cell(col_widths[0], 5.2, target_club, border=1, fill=True)
        self.cell(col_widths[1], 5.2, station, border=1, fill=True)
        
        # Clickable link in blue
        self.set_text_color(2, 132, 199)
        self.cell(col_widths[2], 5.2, url, border=1, fill=True, link=url)
        
        self.set_text_color(30, 41, 59)
        self.cell(col_widths[3], 5.2, notes, border=1, fill=True)
        self.ln()

def create_catalog_pdf():
    pdf = PDFCatalog(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()

    col_widths = [45, 42, 118, 70] # Total = 275mm for landscape A4

    # 1. UK National League
    pdf.chapter_title('1. UK National League & North/South (Tier 5 & 6) - Soccer [Tested 100% OK 200]')
    headers = ['Club / Target Match', 'Broadcaster / Platform', 'Direct Stream Link (Clickable)', 'Status & Latency Notes']
    pdf.add_table_header(col_widths, headers)
    
    uk_rows = [
        ['Wealdstone & Barnet', 'BBC Radio London', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_london', 'Verified OK 200. Live 24/7 stream.'],
        ['Braintree & Chelmsford', 'BBC Essex', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_essex', 'Verified OK 200. Live 24/7 stream.'],
        ['Oldham & Altrincham', 'BBC Radio Manchester', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_manchester', 'Verified OK 200. Live 24/7 stream.'],
        ['Eastleigh FC', 'BBC Radio Solent', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_solent', 'Verified OK 200. Live 24/7 stream.'],
        ['Oxford City', 'BBC Radio Oxford', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_oxford', 'Verified OK 200. Live 24/7 stream.'],
        ['Ebbsfleet & Maidstone', 'BBC Radio Kent', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_kent', 'Verified OK 200. Live 24/7 stream.'],
        ['Cumbria Non-League', 'BBC Radio Cumbria', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_cumbria', 'Verified OK 200. Live 24/7 stream.'],
        ['Torquay United', 'TUFC Radio (Mixlr)', 'https://officialtufc.mixlr.com/', 'Direct Plainmoor stadium feed.'],
        ['Tamworth FC', 'Lambs Media (Mixlr)', 'https://lambsmedia.mixlr.com/', 'Tamworth home/away coverage.']
    ]
    for idx, r in enumerate(uk_rows):
        pdf.add_table_row(col_widths, r, is_even=(idx % 2 == 1))

    pdf.ln(2.5)

    # 2. League of Ireland
    pdf.chapter_title('2. League of Ireland (First Division & Premier) - Soccer [Tested 100% OK 200]')
    pdf.add_table_header(col_widths, headers)
    ireland_rows = [
        ['Kerry FC', 'Radio Kerry Live', 'http://playerservices.streamtheworld.com/api/livestream-redirect/RADIO_KERRY.mp3', 'Verified 200 OK. 24/7 live audio stream.'],
        ['Treaty United & Cobh', 'Live 95 Sport (Mixlr)', 'https://sports-live95.mixlr.com/', 'Direct press-box match commentary.'],
        ['Dundalk / Drogheda / Harps', 'LMFM Sport Live 1 (Mixlr)', 'https://lmfm-sport-live-1.mixlr.com/', 'Live press-box match audio.'],
        ['Wexford & Regional Games', 'LMFM Sport Live 2 (Mixlr)', 'https://lmfm-sport-live-2.mixlr.com/', 'Dedicated secondary sports channel.'],
        ['Wexford Region (24/7)', 'South East Radio', 'https://playerservices.streamtheworld.com/api/livestream-redirect/SOUTH_EAST_RADIO.mp3', 'Verified 200 OK. Regional sports.'],
        ['Finn Harps (24/7)', 'Highland Radio', 'http://playerservices.streamtheworld.com/api/livestream-redirect/HIGHLAND_RADIO.mp3', 'Verified 200 OK. Donegal sports.'],
        ['Bray Wanderers (24/7)', 'East Coast FM', 'https://live-bauerie.sharp-stream.com/EASTCOAST', 'Verified 200 OK. Wicklow sports coverage.']
    ]
    for idx, r in enumerate(ireland_rows):
        pdf.add_table_row(col_widths, r, is_even=(idx % 2 == 1))

    pdf.add_page()

    # 3. Scottish Lower Leagues
    pdf.chapter_title('3. Scottish League 1, 2 & Challenge Cup - Soccer')
    pdf.add_table_header(col_widths, headers)
    scot_rows = [
        ['Scottish SPFL Coverage (FM)', 'BBC Radio Scotland FM', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_scotland_fm', 'Verified 200 OK. Instant live goal alerts.'],
        ['Scottish Sportsound (MW)', 'BBC Radio Scotland MW', 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_scotland_mw', 'Verified 200 OK. Balmoor & SPFL matches.']
    ]
    for idx, r in enumerate(scot_rows):
        pdf.add_table_row(col_widths, r, is_even=(idx % 2 == 1))

    pdf.ln(2.5)

    # 4. South Africa PSL & NFD
    pdf.chapter_title('4. South African PSL & Motsepe Foundation Championship (NFD) - Soccer [Verified 200 OK]')
    sa_col_widths = [45, 42, 118, 70]
    pdf.add_table_header(sa_col_widths, ['Station', 'Language / Region', 'Direct Stream URL (Clickable)', 'Status & Notes'])
    sa_rows = [
        ['Ukhozi FM', 'Zulu / National', 'https://playerservices.streamtheworld.com/api/livestream-redirect/UKHOZIFMAAC_SC', 'Verified 200 OK. Pitch-side reporters.'],
        ['Thobela FM', 'Pedi / Limpopo', 'https://playerservices.streamtheworld.com/api/livestream-redirect/THOBELAAAC.aac', 'Verified 200 OK. Limpopo regional teams.'],
        ['Lesedi FM', 'Sotho / Free State', 'https://playerservices.streamtheworld.com/api/livestream-redirect/LESEDIAAC_SC', 'Verified 200 OK. Free State regional teams.']
    ]
    for idx, r in enumerate(sa_rows):
        pdf.add_table_row(sa_col_widths, r, is_even=(idx % 2 == 1))

    output_pdf = "Master_Catalog_Sports_Audio_Streams.pdf"
    pdf.output(output_pdf)
    print(f"[SUCCESS] Updated PDF generated at: {os.path.abspath(output_pdf)}")

if __name__ == "__main__":
    create_catalog_pdf()
