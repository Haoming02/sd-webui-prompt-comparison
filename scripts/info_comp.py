import os
import re

import gradio as gr
from modules.images import read_info_from_image
from modules.script_callbacks import on_ui_tabs
from PIL import Image, UnidentifiedImageError


def compare(folder: str, common: str) -> str:
    if not os.path.isdir(folder):
        return """<div class="image-info"><br><p>
            <span class="diff">Invalid Folder...</span>
            </p><br></div>"""

    images: list[Image.Image] = []
    for file in (os.path.join(folder, f) for f in os.listdir(folder)):
        if not os.path.isfile(file):
            continue
        try:
            images.append(Image.open(file))
        except UnidentifiedImageError:
            continue

    POSITIVE: list[list[str]] = []
    NEGATIVE: list[list[str]] = []
    PARAMETER: list[list[str]] = []

    COMMON_POSITIVE: set[str] = None
    COMMON_NEGATIVE: set[str] = None
    COMMON_PARAMETER: set[str] = None

    COMMA = ',(?=(?:[^"]*["][^"]*["])*[^"]*$)'

    for image in images:
        infotext, _ = read_info_from_image(image)
        if infotext is None:
            continue

        assert isinstance(infotext, str)
        if not infotext.strip():
            continue

        infotext = infotext.replace("<", "&lt;").replace(">", "&gt;")
        positive, chunks = infotext.split("Negative prompt:")
        negative, misc = chunks.split("Steps:")
        params, _ = misc.split("Version:")

        chunks = re.split(COMMA, f"Steps: {params}")
        POSITIVE.append([tag.strip() for tag in positive.split(",") if tag.strip()])
        NEGATIVE.append([tag.strip() for tag in negative.split(",") if tag.strip()])
        PARAMETER.append([tag.strip() for tag in chunks if tag.strip()])

    count: int = len(POSITIVE)
    for i in range(count):
        if i == 0:
            COMMON_POSITIVE = set(POSITIVE[i])
            COMMON_NEGATIVE = set(NEGATIVE[i])
            COMMON_PARAMETER = set(PARAMETER[i])
        else:
            COMMON_POSITIVE &= set(POSITIVE[i])
            COMMON_NEGATIVE &= set(NEGATIVE[i])
            COMMON_PARAMETER &= set(PARAMETER[i])

    manual = [tag.strip() for tag in common.split(",") if tag.strip()]
    for tag in manual:
        COMMON_POSITIVE.add(tag)
        COMMON_NEGATIVE.add(tag)
        COMMON_PARAMETER.add(tag)

    RESULT: str = ""

    def _add(part, common):
        nonlocal RESULT
        diff = False

        for p in part:
            if p in common:
                if diff:
                    RESULT += "</span>"
                diff = False
                RESULT += f"{p}, "
            else:
                if not diff:
                    RESULT += '<span class="diff">'
                diff = True
                RESULT += f"{p}, "

        RESULT = RESULT[:-2]
        if diff:
            RESULT += "</span>"

    for i in range(count):
        RESULT += '<div class="image-info"><p>'

        _add(POSITIVE[i], COMMON_POSITIVE)
        RESULT += "<br>"
        _add(NEGATIVE[i], COMMON_NEGATIVE)
        RESULT += "<br>"
        _add(PARAMETER[i], COMMON_PARAMETER)

        RESULT += "</p></div>"

    return RESULT


def img_ui():
    with gr.Blocks() as INFO_COMP:
        with gr.Row():
            inputs = gr.Textbox(
                value="",
                label="Input Directory",
                max_lines=1,
                lines=1,
                scale=4,
            )
            run = gr.Button(
                value="Process",
                variant="primary",
                scale=1,
            )
        commons = gr.Textbox(
            value="",
            label="Manual Common Prompts",
            max_lines=2,
            lines=1,
        )
        outputs = gr.HTML()

        run.click(fn=compare, inputs=[inputs, commons], outputs=[outputs])
    return [(INFO_COMP, "PromptCompare", "sd-webui-prompt-comparison")]


on_ui_tabs(img_ui)
