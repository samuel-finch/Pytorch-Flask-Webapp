import flask
from flask import Flask, request, render_template
import numpy as np
from collections import OrderedDict
import torch
from torch import nn
from torchvision import transforms, models, datasets
from PIL import Image
import io
import json

app = Flask(__name__)

@app.route("/")
def index():
    return flask.render_template('index.html')

def prepare_image(image, target_size):
    """Do image preprocessing before prediction on any data.
    :param image:       original image
    :param target_size: target image size
    :return:
                        preprocessed image
    """

    if image.mode != 'RGB':
        image = image.convert("RGB")

    # Resize the input image nad preprocess it.
    image = transforms.Resize(target_size)(image)
    image = transforms.ToTensor()(image)

    # Convert to Torch.Tensor and normalize.
    image = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])(image)

    # Add batch_size axis.
    image = image[None]
    
    return torch.autograd.Variable(image, volatile=True)

@app.route('/predict', methods=['POST'])
def make_prediction():
    if request.method == 'POST':

        # get uploaded image
        file = request.files['image']
        if not file:
            return render_template('index.html', label="No file uploaded")

        image = flask.request.files["image"].read()
        image = Image.open(io.BytesIO(image))
        image = prepare_image(image, target_size=(224, 224))

        output = model(image)

        output = output.numpy().ravel()
        labels = meth_agn_v2(output,0.5)
        
        label_array = [ cat_to_name[str(i)] for i in labels]
        label = ",".join(label_array )
        
        # label = cat_to_name[str(new.argmax())]
        

        return render_template('index.html', label=label)

def meth_agn_v2(x, thresh):
    idx, = np.where(x > thresh)
    return idx[np.argsort(x[idx])]

def init_model():
    np.random.seed(2019)
    torch.manual_seed(2019)
    resnet = models.resnet50()
    num_ftrs = resnet.fc.in_features
    resnet.fc = torch.nn.Linear(num_ftrs, 20)
    resnet.load_state_dict(torch.load('model.pth', map_location='cpu'))

    for param in resnet.parameters():
        param.requires_grad = False
    resnet.eval()
    return resnet


if __name__ == '__main__':
    # initialize model
    model = init_model()
    # initialize labels
    
    with open('cat_to_name.json', 'r') as f:
        cat_to_name = json.load(f)
    # start app
    app.run(host='0.0.0.0', port=8000)