class ThemeManager:

    @staticmethod
    def oled():

        return """
QMainWindow{
    background:#000000;
}

QWidget{
    background:#000000;
    color:#F2F2F2;
    font-family:"Segoe UI";
    font-size:10pt;
}

QFrame{
    background:#090909;
    border:1px solid #1F1F1F;
    border-radius:12px;
}

QLabel{
    background:transparent;
    padding:2px;
    min-height:22px;
}

QGroupBox{
    background:#090909;
    border:1px solid #202020;
    border-radius:12px;
    margin-top:14px;
    padding-top:12px;
    font-weight:600;
}

QGroupBox::title{
    subcontrol-origin:margin;
    subcontrol-position:top left;
    left:12px;
    padding:2px 8px;
}

QPushButton{
    background:#151515;
    border:1px solid #2A2A2A;
    border-radius:10px;
    padding:8px 12px;
    min-height:34px;
}

QPushButton:hover{
    background:#202020;
}

QPushButton:pressed{
    background:#2A2A2A;
}

QPushButton:disabled{
    color:#555555;
}

QLineEdit{
    background:#111111;
    border:1px solid #2A2A2A;
    border-radius:8px;
    padding:6px;
    min-height:30px;
}

QTextEdit{
    background:#111111;
    border:1px solid #2A2A2A;
    border-radius:10px;
    padding:8px;
}

QPlainTextEdit{
    background:#111111;
    border:1px solid #2A2A2A;
    border-radius:10px;
    padding:8px;
}

QComboBox{
    background:#151515;
    border:1px solid #2A2A2A;
    border-radius:8px;
    padding:6px;
    min-height:30px;
}

QComboBox::drop-down{
    border:none;
    width:24px;
}

QComboBox QAbstractItemView{
    background:#111111;
    color:#F2F2F2;
    selection-background-color:#2979FF;
}

QSpinBox,
QDoubleSpinBox{
    background:#151515;
    border:1px solid #2A2A2A;
    border-radius:8px;
    padding:4px;
    min-height:30px;
}

QProgressBar{
    border:1px solid #2A2A2A;
    border-radius:8px;
    background:#111111;
    text-align:center;
    min-height:26px;
}

QProgressBar::chunk{
    background:#2979FF;
    border-radius:6px;
}

QListWidget{
    background:#101010;
    border:1px solid #2A2A2A;
    border-radius:10px;
    outline:none;
}

QListWidget::item{
    min-height:26px;
    padding:4px;
}

QListWidget::item:selected{
    background:#2979FF;
}

QTableWidget{
    background:#101010;
    border:1px solid #2A2A2A;
    border-radius:10px;
    gridline-color:#222222;
}

QTableWidget::item{
    padding:6px;
}

QHeaderView::section{
    background:#151515;
    border:none;
    padding:8px;
    min-height:28px;
}

QTabWidget::pane{
    border:1px solid #202020;
    border-radius:8px;
    margin-top:2px;
}

QTabBar::tab{
    background:#111111;
    border:1px solid #2A2A2A;
    border-top-left-radius:8px;
    border-top-right-radius:8px;
    padding:6px 14px;
    min-height:30px;
    margin-right:2px;
}

QTabBar::tab:selected{
    background:#202020;
}

QMenuBar{
    background:#090909;
    min-height:30px;
}

QMenuBar::item{
    padding:6px 10px;
}

QMenuBar::item:selected{
    background:#202020;
}

QMenu{
    background:#111111;
    border:1px solid #222222;
}

QMenu::item{
    padding:6px 24px;
}

QMenu::item:selected{
    background:#2979FF;
}

QStatusBar{
    background:#090909;
    min-height:28px;
}

QScrollBar:vertical{
    width:12px;
    background:#111111;
}

QScrollBar::handle:vertical{
    background:#444444;
    border-radius:6px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical{
    height:0px;
}

QScrollBar:horizontal{
    height:12px;
    background:#111111;
}

QScrollBar::handle:horizontal{
    background:#444444;
    border-radius:6px;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal{
    width:0px;
}

QSplitter::handle{
    background:#161616;
}

QDockWidget::title{
    background:#111111;
    padding:6px;
    text-align:center;
}

QToolTip{
    background:#1A1A1A;
    color:white;
    border:1px solid #444444;
}
"""