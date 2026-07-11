class GenerateButtonStyle:

    ENABLED = """
    QPushButton{

        background:#22C55E;

        color:white;

        border:none;

        border-radius:12px;

        padding:12px;

        font-size:15px;

        font-weight:bold;

    }

    QPushButton:hover{

        background:#16A34A;

    }

    QPushButton:pressed{

        background:#15803D;

    }
    """

    DISABLED = """
    QPushButton{

        background:#2A2A2A;

        color:#808080;

        border:1px solid #404040;

        border-radius:12px;

        padding:12px;

        font-size:15px;

        font-weight:bold;

    }
    """