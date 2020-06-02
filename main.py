from wand.image import Image
from io import BytesIO
import flask
import requests

flask_app = flask.Flask(__name__)


@flask_app.route('/pride', methods=['get'])
def pride():
    img_url = flask.request.args.get('img')

    if img_url is None or img_url == '':
        return 'Invalid image url'

    response = requests.get(img_url)
    _img = BytesIO(response.content)
    _img.seek(0)

    with Image() as blended_image:
        with Image(file=_img) as avatar:
            if not len(avatar.sequence) > 60:
                return 'Gif has too many frames'

            with Image(filename='images/pride.png') as pride_image:
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

    return flask.send_file(buffer, attachment_filename='pride.png')


@flask_app.route('/distort', methods=['get'])
def distort():
    img_url = flask.request.args.get('img')

    if img_url is None or img_url == '':
        return ''

    response = requests.get(img_url)
    _img = BytesIO(response.content)
    _img.seek(0)

    with Image() as new_image:
        with Image(file=_img) as img:
            def transform_image(img):
                img.transform(resize='500x500>')
                img.liquid_rescale(width=int(img.width * 0.5), height=int(img.height * 0.5), delta_x=1)
                img.liquid_rescale(width=int(img.width * 1.5), height=int(img.height * 1.5), delta_x=2)
                img.transform(resize='500x500')

            if len(img.sequence) > 1:
                transform_image(img.sequence[0])
                new_image.sequence.append(img.sequence[0])
            else:
                transform_image(img)
                new_image.sequence.append(img)

        magikd_buffer = BytesIO()
        new_image.save(magikd_buffer)
        magikd_buffer.seek(0)

    return flask.send_file(magikd_buffer, attachment_filename='distorted.png')


if __name__ == '__main__':
    flask_app.run()
