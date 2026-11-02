"""Render original tray states at native and enlarged inspection sizes."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw
from tray_icon import whale_icon


def main():
    sheet=Image.new('RGB',(730,490),'#F4F7FA')
    d=ImageDraw.Draw(sheet)
    for row,(name,enabled,error) in enumerate([('Enabled',True,False),('Paused',False,False),('Error',False,True)]):
        y=25+row*155
        d.text((20,y),name,fill='#123F68')
        for column,size in enumerate((16,24,32)):
            x=130+column*195
            d.text((x,y),f'{size} x {size}',fill='#123F68')
            icon=whale_icon(size,enabled,error)
            sheet.paste(icon,(x,y+28),icon)
            enlarged=icon.resize((96,96),Image.Resampling.NEAREST)
            for by in range(0,96,8):
                for bx in range(0,96,8):
                    d.rectangle((x+45+bx,y+25+by,x+52+bx,y+32+by),fill='#FFFFFF' if (bx+by)//8%2 else '#DFE6EC')
            sheet.paste(enlarged,(x+45,y+25),enlarged)
    output=Path(__file__).resolve().parents[1]/'docs'/'whale-preview.png'
    sheet.save(output)
    print(output)

if __name__=='__main__': main()
