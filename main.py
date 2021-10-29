import math
import matplotlib.pyplot as plt
from PIL import ImageDraw, Image as PILImage, ImageFont
from flask.globals import request
from wand.image import Image
from io import BytesIO
import flask
import requests

flask_app = flask.Flask(__name__)


@flask_app.route("/electionimage", methods=["post"])
def election_image():
    """
    Endpoint for generating an election image from the data provided
    in the request body.
    candidates (list) - a list of candidates with the information relevant to
    the generation of the image.
    electorate_size (int) - the size of the electorate.
    turnout (int) - the amount of people from that electorate that showed
    and voted.
    include_nonvoters (boolean) - used to determine whether or not nonvoters
    should be include in the pie chart.
    generate_table (boolean) - used to determine whether a table or a
    pie chart should be generated.
    """
    content = request.json
    candidates = content["candidates"]
    electorate_size = content["electorate_size"]
    turnout = content["turnout"]
    include_nonvoters = content["include_nonvoters"]
    generate_table = content["generate_table"]
    under_1k = []
    the_rest = []

    # Candidates that got under 1,000 votes get bundled into one category.
    for candidate in candidates:
        if candidate["votes"] > 1000:
            the_rest.append(candidate)
        else:
            under_1k.append(candidate)

    nonvoters = electorate_size - turnout
    under_1k_total = sum([c["votes"] for c in under_1k])
    parent_pie_values = [c["votes"] for c in the_rest]
    parent_pie_labels = []
    # this is primarily used to shorten long party names.
    for c in the_rest:
        party_name = c["party_name"]
        parent_pie_labels.append(f"{party_name} ({c['votes']:,} votes)")

    parent_pie_values.append(under_1k_total)
    parent_pie_labels.append(f"Others ({under_1k_total:,} votes)")
    if nonvoters != 0 and include_nonvoters:
        parent_pie_values.append(nonvoters)
        parent_pie_labels.append(f"Didn't Vote ({nonvoters:,} votes)")

    plt.tight_layout()
    fig, ax1 = plt.subplots()

    if generate_table is False:
        ax1.pie(parent_pie_values, radius=0.6, labels=parent_pie_labels)
    else:
        # This section is for the table.
        ax1.set_axis_off()
        rows = []

        # Almost identical to the loop above, however this is used to produce a 2d list.

        # Each list is considered a row in the table.
        for c in candidates:
            party_name = c["party_name"]
            rows.append(
                [
                    c["name"],
                    party_name,
                    f"{c['votes']:,}",
                    "{:.1%}".format(c["vote_share"]),
                    c["vote_share_change"],
                ]
            )

        table = ax1.table(
            cellText=rows,
            loc="upper center",
            colLabels=[
                "Candidate",
                "Party",
                "Votes",
                "Vote Share",
                "Vote Share Change",
            ],
            cellLoc="center",
        )
        # Ensure that the size of some of the columns aren't too big for the data, or too small for the data.
        table.auto_set_column_width(col=list(range(len(candidates))))
        cells = table.get_celld()

        # The only way i've found that actually sets the height of all rows in the table.
        for i in range(5):
            for j in range(0, 13):
                cells[(j, i)].set_height(0.065)

        # Stops the front from resizing.
        table.auto_set_font_size(False)

    print("Sending file")
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    return flask.send_file(buffer, attachment_filename="electionimg.png")


@flask_app.route("/divisionimage", methods=["post"])
def division_image():
    title_font = ImageFont.truetype("static/Metropolis-Bold.otf", 40)
    key_font = ImageFont.truetype("static/Metropolis-SemiBold.otf", 25)
    division = request.json
    aye_members = division["aye_members"]
    no_members = division["no_members"]
    parties = division["parties"]

    def draw_ayes(draw: ImageDraw.ImageDraw, members: dict):
        columns = math.ceil(len(members) / 10)
        draw.text((100, 420), "Ayes", font=title_font, fill=(0, 0, 0))

        member_keys = list(members.keys())
        for column in range(columns + 1):
            for j, key in enumerate(member_keys[10 * (column - 1) : 10 * column]):
                colour = members[key]
                draw.ellipse(
                    [
                        (
                            80 + ((20 * column) + (2 * column)),
                            480 + (20 * j) + (2 * j),
                        ),
                        (
                            100 + ((20 * column) + (2 * column)),
                            500 + (20 * j) + (2 * j) - 2,
                        ),
                    ],
                    f"{colour}",
                )

    def draw_noes(draw: ImageDraw.ImageDraw, members: dict):
        columns = math.ceil(len(members) / 10)
        draw.text((100, 120), "Noes", font=title_font, fill=(0, 0, 0))
        member_keys = list(members.keys())
        for column in range(columns + 1):
            for j, key in enumerate(member_keys[10 * (column - 1) : 10 * column]):
                colour = members[key]
                draw.ellipse(
                    [
                        (
                            80 + ((20 * column) + (2 * column)),
                            180 + (20 * j) + (2 * j),
                        ),
                        (
                            100 + ((20 * column) + ((2 * column) - 2)),
                            200 + (20 * j) + ((2 * j) - 2),
                        ),
                    ],
                    f"{colour}",
                )

    def draw_keys(draw: ImageDraw.ImageDraw, parties: dict):
        for i, key in enumerate(parties.keys()):
            name = parties[key]["name"]
            w, h = draw.textsize(name)
            draw.text(
                (1600, 120 + (60 * i)),
                f"{name}",
                font=key_font,
                fill="#ffffff",
                anchor="lt",
            )
            draw.ellipse(
                [(1520, 110 + (60 * i)), (1570, 150 + (60 * i))],
                fill=f"{parties[key]['colour']}",
            )

    im = PILImage.new("RGB", (2100, 800), "#edebea")
    draw = ImageDraw.Draw(im)
    draw.rectangle([(1450, 0), (2100, 800)], fill="#b7dade")
    draw.polygon([(1300, 0), (1450, 0), (1450, 800)], fill="#b7dade")
    draw_ayes(draw, aye_members)
    draw_noes(draw, no_members)
    draw_keys(draw, parties)
    buffer = BytesIO()
    im.save(buffer, format="png")
    buffer.seek(0)
    print("Sending image")
    return flask.send_file(buffer, attachment_filename="divisionimage.png")


@flask_app.route("/pride", methods=["get"])
def pride():
    img_url = flask.request.args.get("img")

    if img_url is None or img_url == "":
        return flask.jsonify({"error": "invalid image url"})

    # get file extension
    split = img_url.split(".")
    extension = split[-1]

    # check if it has arguments after extension
    split = extension.split("?")
    if len(split) > 1:
        extension = split[0]

    response = requests.get(img_url)
    _img = BytesIO(response.content)
    _img.seek(0)

    with Image() as blended_image:
        with Image(file=_img) as avatar:
            if len(avatar.sequence) > 60:
                return flask.jsonify({"error": "Gif has too many frames"})

            with Image(filename="images/pride.png") as pride_image:
                pride_image.resize(width=800, height=800)
                pride_image.transparentize(0.6)

                def apply_pride(img):
                    img.resize(width=800, height=800)
                    img.composite(pride_image)

                if len(avatar.sequence) > 1:
                    for frame in avatar.sequence:
                        apply_pride(frame)
                        blended_image.sequence.append(frame)
                else:
                    apply_pride(avatar)
                    blended_image.sequence.append(avatar)

        buffer = BytesIO()
        blended_image.save(buffer)
        buffer.seek(0)

    return flask.send_file(buffer, attachment_filename=f"pride.{extension}")


@flask_app.route("/distort", methods=["get"])
def distort():
    img_url = flask.request.args.get("img")

    if img_url is None or img_url == "":
        return flask.jsonify({"error": "invalid image url"})

    # get file extension
    split = img_url.split(".")
    extension = split[-1]

    # check if it has arguments after extension
    split = extension.split("?")
    if len(split) > 1:
        extension = split[0]

    response = requests.get(img_url)
    _img = BytesIO(response.content)
    _img.seek(0)

    with Image() as new_image:
        with Image(file=_img) as img:
            if len(img.sequence) > 60:
                return flask.jsonify({"error": "Gif has too many frames"})

            def transform_image(image):
                image.resize(width=800, height=800)
                image.liquid_rescale(
                    width=int(image.width * 0.5),
                    height=int(image.height * 0.5),
                    delta_x=1,
                )
                image.liquid_rescale(
                    width=int(image.width * 1.5),
                    height=int(image.height * 1.5),
                    delta_x=2,
                )

            if len(img.sequence) > 1:
                for frame in img.sequence:
                    transform_image(frame)
                    new_image.sequence.append(frame)
            else:
                transform_image(img)
                new_image.sequence.append(img)

        magikd_buffer = BytesIO()
        new_image.save(magikd_buffer)
        magikd_buffer.seek(0)

    return flask.send_file(magikd_buffer, attachment_filename=f"distorted.{extension}")


if __name__ == "__main__":
    flask_app.run(host="0.0.0.0")
