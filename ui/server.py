from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse

from core.parser import parse_book, extract_book_text
from core.cleaner import clean_text

BOOK_FOLDER = Path("Books")
BOOK_FOLDER.mkdir(exist_ok=True)

app = FastAPI(title="Audiobook Studio")


@app.get("/", response_class=HTMLResponse)
async def home():

    return """
<!DOCTYPE html>

<html>

<head>

<title>Audiobook Studio</title>

<style>

body{
background:#202124;
color:white;
font-family:Arial;
text-align:center;
padding:50px;
}

.container{
width:700px;
margin:auto;
background:#303134;
padding:30px;
border-radius:10px;
}

button{
padding:10px 25px;
font-size:16px;
cursor:pointer;
}

</style>

</head>

<body>

<div class="container">

<h1>📚 Audiobook Studio</h1>

<h2>Version 0.5</h2>

<form
action="/upload"
method="post"
enctype="multipart/form-data">

<input
type="file"
name="book">

<br><br>

<button>

Upload Book

</button>

</form>

</div>

</body>

</html>

"""


@app.post("/upload", response_class=HTMLResponse)
async def upload(book: UploadFile = File(...)):

    destination = BOOK_FOLDER / book.filename

    with open(destination, "wb") as f:
        f.write(await book.read())

    info = parse_book(destination)

    text = extract_book_text(destination)

    text = clean_text(text)

    preview = text[:3000]

    preview = preview.replace("<", "&lt;").replace(">", "&gt;")

    return f"""

<!DOCTYPE html>

<html>

<head>

<title>{info["title"]}</title>

<style>

body{{
background:#202124;
color:white;
font-family:Arial;
padding:40px;
}}

pre{{
background:#303134;
padding:20px;
border-radius:10px;
white-space:pre-wrap;
}}

</style>

</head>

<body>

<h1>📚 Book Imported</h1>

<hr>

<h2>{info["title"]}</h2>

<p><b>Author:</b> {info["author"]}</p>

<p><b>Pages:</b> {info["pages"]}</p>

<p><b>Language:</b> {info["language"]}</p>

<p><b>Type:</b> {info["type"]}</p>

<hr>

<h2>Clean Preview</h2>

<pre>

{preview}

</pre>

<br>

<a href="/">Upload another book</a>

</body>

</html>

"""