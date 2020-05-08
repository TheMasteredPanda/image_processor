from wand.image import Image
from io import BytesIO
import flask
import requests

flask_app = flask.Flask(__name__)


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
