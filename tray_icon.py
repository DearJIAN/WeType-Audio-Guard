"""Original Pillow-drawn whale; no third-party graphics or trademarks."""
from PIL import Image, ImageDraw


def whale_icon(size=32, enabled=False, error=False):
    if size < 16:
        raise ValueError('Tray icon size must be at least 16')
    scale = 4
    image = Image.new('RGBA', (size * scale, size * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    unit = size * scale / 64
    def box(coords): return tuple(round(c * unit) for c in coords)
    def polygon(coords, color):
        draw.polygon([(round(x * unit), round(y * unit)) for x,y in coords], fill=color)
    body = '#123F68' if enabled else '#657580'
    accent = '#39B8D5' if enabled else '#A4B1B8'
    # Broad tail and a round, forward-facing head survive 16px rendering.
    polygon([(42,34),(49,24),(49,16),(57,21),(62,17),(61,29),(54,37),(45,43)],body)
    draw.ellipse(box((5,20,51,53)),fill=body)
    draw.ellipse(box((9,37,44,51)),fill=accent)
    polygon([(28,34),(39,39),(30,47),(26,42)],body)
    draw.ellipse(box((14,29,19,34)),fill='white')
    draw.ellipse(box((16,30,19,33)),fill='#061E31')
    draw.arc(box((8,33,25,44)),5,105,fill=body,width=max(1,round(2*unit)))
    # A small sea-blue water drop gives the silhouette a whale cue.
    polygon([(25,16),(29,7),(32,15),(29,20)],accent)
    if error:
        draw.ellipse(box((44,42,63,61)),fill='#F6B642',outline='#123F68',width=max(1,round(unit)))
        draw.line(box((53,46,53,53)),fill='#123F68',width=max(1,round(2*unit)))
        draw.ellipse(box((52,56,54,58)),fill='#123F68')
    return image.resize((size,size), Image.Resampling.LANCZOS)
