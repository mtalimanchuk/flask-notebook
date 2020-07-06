from pathlib import Path
from typing import Union

from flask import Flask, render_template, Response, jsonify, request


PROTECTED_URLS = {
    "root": "/",
    "index": "/index",
    "search": "/search",
}

APP_PATH = Path(__file__).parent
TEMPLATES_PATH = APP_PATH / "templates"
NOTEBOOKS_ROOT_PATH = APP_PATH / "notes"
if not NOTEBOOKS_ROOT_PATH.exists():
    print(
        f"\n[!] An empty root directory for notes ({NOTEBOOKS_ROOT_PATH.absolute()}) "
        "will be created.\n"
        "Make sure to add notes first.\n"
    )
NOTEBOOKS_ROOT_PATH.mkdir(exist_ok=True, parents=True)


def load_html(path: Union[Path, str], clean: bool = False) -> str:
    """Load note source file as string

    Args:
        path (Union[Path, str]): note path
        clean (bool, optional): whether to clean the text or not. Defaults to False.

    Returns:
        str: file contents
    """

    path = Path(path)
    with path.open("r", encoding="utf-8") as note_f:
        content = note_f.read()

    if clean:
        content = content.lower()

    return content


class Search:
    def __init__(self, root_dir: Union[Path, str]):
        """Create search object and scan root_dir

        Usage:
            search = Search("notes/root/dir")
            results = search("port scanning")

        Args:
            root_dir (Union[Path, str]): Notebooks root directory
        """

        self._root_dir = Path(root_dir)
        self._all = self._refresh_source()

    def _refresh_source(self) -> dict:
        """Return all notes as dict

        Returns:
            dict:
            {
                "relative/path/my_note1.html": "note1 text",
                "relative/path/my_note2.html": "note2 text",
            }

        """

        all_notes = {}

        for path in self._root_dir.glob("**/*.html"):
            content = load_html(path, clean=True)
            relative_path = str(path.relative_to(self._root_dir))

            all_notes[relative_path] = content

        return all_notes

    def __call__(self, pattern: str, current_dir: Union[Path, str]) -> list:
        """Return a list of paths with matched text.

        Args:
            pattern (str): searches for this pattern inside the current_dir's contents
            current_dir (Union[Path, str]): directory to search inside

        Returns:
            list: paths to notes
        """

        pattern = pattern.lower()
        results = []

        for name, text in self._all.items():
            if (name.startswith(current_dir)) and (pattern in name.lower() or pattern in text):
                results.append(name)

        # added this to test spinner
        from datetime import datetime, timedelta
        finish = datetime.now() + timedelta(seconds=2)
        while datetime.now() < finish:
            pass

        return results


app = Flask(__name__, template_folder=TEMPLATES_PATH)

search = Search(root_dir=NOTEBOOKS_ROOT_PATH)


@app.route(PROTECTED_URLS["root"])
@app.route(PROTECTED_URLS["index"])
def index():
    return render_template("index.html", current_dir="")


@app.route(PROTECTED_URLS["search"])
def run_search():
    pattern = request.args.get("text", "")
    current_dir = request.args.get("dir", "")

    results = search(pattern, current_dir)

    return jsonify(results)


@app.route("/<path:path>")
def show_content(path):
    canonical_path = NOTEBOOKS_ROOT_PATH / path
    if not canonical_path.exists():
        response = Response("Not found :(", status=404)
    elif canonical_path.is_dir():
        response = render_template("index.html", current_dir=path)
    else:
        response = load_html(path, clean=False)

    return response


if __name__ == "__main__":
    app.run()
