from __future__ import annotations

from pathlib import Path

import fitz
from ebooklib import epub


class CoverExtractor:
    def pdf(self, file, output):
        source = Path(file)
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with fitz.open(source) as pdf:
            if pdf.page_count <= 0:
                return None
            pixmap = pdf[0].get_pixmap(dpi=180, alpha=False)
            pixmap.save(destination)
        return destination if destination.is_file() else None

    def epub(self, file, output):
        source = Path(file)
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        book = epub.read_epub(str(source))

        preferred = []
        fallback = []
        for item in book.get_items():
            name = str(item.get_name()).casefold()
            media_type = str(getattr(item, "media_type", "")).casefold()
            if not media_type.startswith("image/"):
                continue
            if "cover" in name:
                preferred.append(item)
            else:
                fallback.append(item)

        for item in preferred + fallback[:1]:
            content = item.get_content()
            if not content:
                continue
            suffix = Path(item.get_name()).suffix.lower()
            if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
                suffix = ".jpg"
            actual = destination.with_suffix(suffix)
            actual.write_bytes(content)
            return actual
        return None

    def extract(self, file, output_folder) -> Path | None:
        source = Path(file)
        folder = Path(output_folder)
        folder.mkdir(parents=True, exist_ok=True)
        destination = folder / "cover.jpg"
        try:
            if source.suffix.lower() == ".pdf":
                return self.pdf(source, destination)
            if source.suffix.lower() == ".epub":
                return self.epub(source, destination)
        except Exception:
            return None
        return None
