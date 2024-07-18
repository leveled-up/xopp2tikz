import gzip
import sys
import xml.etree.ElementTree as ET

data = ""
with gzip.open(sys.argv[1], mode='rb') as f:
    data = f.read().decode("utf-8")
tree = ET.fromstring(data)


def warn(*args):
    print("%", *args)


page: ET.Element | None = None
for child in tree:
    if child.tag == "page":
        if page is None:
            page = child
        else:
            warn("Warning: Only 1 page is supported")

if page is None:
    print("Error: no pages")
    exit(1)

print(
    """\\documentclass{standalone}
\\usepackage{tikz}
\\usepackage{amsmath}
\\usepackage{amssymb}
\\begin{document}
\\begin{tikzpicture}
""")

color_counter = 0


def color_cmd(attrib: dict[str, str]) -> tuple[str, str]:
    if "color" not in attrib:
        return ("black", "")
    hexcode = attrib["color"][1:7]
    global color_counter
    color_counter += 1
    n = "color" + str(color_counter)
    return (n, "\\definecolor{" + n + "}{HTML}{" + hexcode + "}")


def font_size_cmd(size: str) -> str:
    s = float(size)
    return "\\fontsize{" + str(s) + "}{" + str(1.2 * s) + "}\\selectfont{}"


def position(x: str, y: str) -> str:
    return f"({float(x) / 30}, -{float(y) / 30})"


def pairs_iter(items):
    mem = None
    for item in items:
        if mem is None:
            mem = item
        else:
            yield (mem, item)
            mem = None


for layer in page:
    if layer.tag != "layer":
        continue
    for item in layer:
        attrib = item.attrib
        warn(item.tag, item.attrib)
        match item.tag:
            case "stroke":
                if attrib["tool"] not in ("pen", "highlighter"):
                    warn("Warning: Only pen + highlighter tool supported")
                if item.text is None:
                    warn("Warning: skipping empty stroke")
                    continue

                color_name, color_ = color_cmd(attrib)
                print(color_)
                if attrib["tool"] == "highlighter":
                    color_name += ", draw opacity=0.5 "
                width = str(float(attrib["width"]) / 10) + "mm"
                style = ""
                if "style" in attrib:
                    match attrib["style"]:
                        case "dash":
                            style = ", dashed"
                        case "dashdot":
                            style = ", dash dot"
                        case "dot":
                            style = ", dotted"
                        case _:
                            warn("Unsupported line style ", attrib["style"])
                fill = ""
                if "fill" in attrib:
                    fill = ", fill=" + color_name + ", fill opacity=0.5"
                coord = " -- ".join(
                    position(x, y) for x, y in pairs_iter(item.text.split())
                )
                print("\\draw [line width=" + width + ", " +
                      color_name + style + fill + "] " + coord + ";")
            case "teximage":
                height = float(attrib["bottom"]) - float(attrib["top"])
                size = font_size_cmd(str(height / 2))
                pos = position(attrib["left"], attrib["top"])
                color_name, color_ = color_cmd(attrib)
                print(color_)
                print(
                    "\\node[" + color_name + ",anchor = west] at ", pos)
                print(" {" + size + "$\\displaystyle " +
                      attrib["text"] + "$};")
            case "text":
                if attrib["font"] != "Sans":
                    warn("Warning: text font changing unsupported")
                if item.text is None:
                    warn("Warning: skipping empty text node")
                    continue

                size = font_size_cmd(attrib["size"])
                pos = position(attrib["x"], attrib["y"])
                color_name, color_ = color_cmd(attrib)
                print(color_)
                print(
                    "\\node[" + color_name + ",anchor = west] at ", pos)
                print(" {" + size + item.text + "};")
            case "image":
                warn("Image not implemented")
                # TODO: base64 decode, write to FS, includegraphics
            case _:
                warn("Warning: Item unsupported:", item.tag,
                     item.attrib)  # , child_.text)

print("""
\\end{tikzpicture}
\\end{document}
""")
