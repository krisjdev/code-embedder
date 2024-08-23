import argparse, urllib.request
from pathlib import Path

class FileInfo():
    def __init__(self, file_path: str, file_name: str, download_path: str, commit_hash: str, original_link:str, start_end_line_numbers: tuple = (None, None)):
        self.file_path = file_path
        self.download_path = download_path
        self.file_name = file_name
        self.commit_hash = commit_hash
        self.start_line_number = start_end_line_numbers[0]
        self.end_line_number = start_end_line_numbers[1]
        self.original_link = original_link

        self.file_content = None
        self.file_encoding = None

        self.html = []

        self.highlight_range_start = -1
        self.highlight_range_end = -1

    def add_highlight_range(self, range:str):

        if range is None:
            return
        
        split_range = range.split("-")

        self.highlight_range_start = int(split_range[0])
        self.highlight_range_end = int(split_range[1])

    def fetch_content(self):
        open_url = urllib.request.urlopen(self.download_path)
        encoding = open_url.headers.get_content_charset()
        content = open_url.readlines()

        self.file_content = content
        self.file_encoding = encoding

    def _lines_specified(self) -> bool:
        return not (self.start_line_number is None and self.end_line_number is None)

    def generate_html_table(self):
        
        self.html.append("<div class=\"code-box\">\n\t<div class=\"title-box\">")

        # title box
        self.html.append(f"\t\t<p class=\"file\"><a href=\"{self.original_link}\">{self.file_path}{self.file_name}</a></p>")
        
        if self._lines_specified():
            self.html.append(f"\t\t<p class=\"commit\">Lines {self.start_line_number} to {self.end_line_number} from <a class=\"monospace\" href=\"#\">{self.commit_hash[0:8]}</a></p>")
        else:
            self.html.append(f"\t\t<p class=\"commit\">Full file from <a class=\"monospace\" href=\"#\">{self.commit_hash[0:8]}</a></p>")

        self.html.append("\t</div>")


        # content box
        self.html.append("\t<div class=\"content\">\n\t\t<table class=\"code-listing\">\n\t\t\t<tbody>")

        _start_range = None
        _end_range = None
        if self._lines_specified():
            _start_range = self.start_line_number
            _end_range = self.end_line_number + 1
        else:
            _start_range = 0
            _end_range = len(self.file_content)

        for i in range(_start_range, _end_range):
            self.html.append(f"\t\t\t\t<tr class=\"code-row{' code-highlight' if (i >= self.highlight_range_start and i <= self.highlight_range_end) else ''}\">")
            self.html.append(f"\t\t\t\t\t<td id=\"l{i}\" class=\"lineno\">{i}</td>")
            self.html.append(f"\t\t\t\t\t<td id=\"lc{i}\" class=\"linecontent\">{self.file_content[i].decode(self.file_encoding).rstrip()}</td>")
            self.html.append(f"\t\t\t\t</tr>")

        self.html.append(f"\t\t\t</tbody>\n\t\t</table>\n\t</div>\n</div>")


    def __repr__(self):
        return f"Path: {self.file_path}\n\tfile name: {self.file_name}\n\tstart: {self.start_line_number}, end: {self.end_line_number}\n\tcommit: {self.commit_hash}\n\tURL: {self.download_path}"

def extract_file_info(link:str) -> FileInfo:
    split_link = link.split("/")

    github_index = None
    blob_index = None

    # find and remove anything before (and including) the "github.com" string
    for i in range(len(split_link)):
        if split_link[i] == "github.com":
            github_index = i

    for i in range(github_index, -1, -1):
        split_link.pop(i)


    # locate "blob" and sha
    for i in range(len(split_link)):
        if split_link[i] == "blob" and len(split_link[i+1]) == 40:
            blob_index = i


    file_string = ""
    for i in range(len(split_link)-1):
        if i == blob_index or i == blob_index + 1:
            continue

        file_string += split_link[i]
        file_string += "/"


    file_and_lines = split_link[-1].split("#")
    file_name = file_and_lines[0]

    split_link[blob_index] = "raw"
    download_url = "http://github.com/" + "/".join(split_link)

    if len(file_and_lines) == 1:
        return FileInfo(file_string, file_name, download_url, split_link[blob_index+1], link)
    elif len(file_and_lines) == 2:
        start = None
        end = None

        lines = file_and_lines[1].split("-")
        start = int(lines[0][1:]) # [1:] to get rid of L from L123
        end = int(lines[1][1:])

        return FileInfo(file_string, file_name, download_url, split_link[blob_index+1], link, (start, end))

def main():
    parser = argparse.ArgumentParser(
        description="Convert GitHub permalinks into HTML widgets that can be embedded. Intended to be used with the Hugo PaperMod theme."
    )
    parser.add_argument("link", help="GitHub permalink to code")
    # parser.add_argument("-o", "--output", help="output directory")
    parser.add_argument("-hl", "--highlight", help="select lines to highlight (specify range, start-end)")

    args = parser.parse_args()

    # github link: 
    # https://github.com/titan-compiler-project/titan/blob/99a0e956a70cc50139cb0dc34e0652299f013924/titan/compiler/spirv.py#L12-L29

    # github raw link:
    # https://github.com/titan-compiler-project/titan/raw/99a0e956a70cc50139cb0dc34e0652299f013924/titan/compiler/spirv.py

    info = extract_file_info(args.link)
    info.add_highlight_range(args.highlight)

    # get current path of script
    # Path(__file__).parent

    info.fetch_content()
    info.generate_html_table()

    with open(f"{info.file_path.replace('/', '_')}_{info.file_name.replace('.', '_')}_l{info.start_line_number}-{info.end_line_number}_h{info.highlight_range_start}-{info.highlight_range_end}.html", "w") as f:
        for line in info.html:
            f.writelines(line)


if __name__ == "__main__":
    main()