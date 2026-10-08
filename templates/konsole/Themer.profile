[Appearance]
ColorScheme={{ scheme }}
Font={{ fonts.mono }},{{ fonts.mono-size }},-1,5,{{ fonts.mono-weight }},0,0,0,0,0,0,0,0,0,0,1
BoldIntense=true
LineSpacing={{ konsole.line-spacing }}

[Cursor Options]
CursorShape=1
UseCustomCursorColor=true
CustomCursorColor={{ accent | rgb }}
CustomCursorTextColor={{ bg | rgb }}

[General]
Name=Themer
Parent=FALLBACK/
TerminalMargin={{ konsole.margin }}
TerminalCenter=false
ShowTerminalSizeHint=false

[Interaction Options]
UnderlineFilesEnabled=true

[Scrolling]
HistoryMode=2
ScrollBarPosition=2
ScrollFullPage=false

[Terminal Features]
BlinkingCursorEnabled=true
