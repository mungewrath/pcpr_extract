"""
A simple wrapper for a model. Just re-write the predict() function below to match your model
"""

class clearPathModel:
    def __init__(self, model):
        self.model = model

    def predict(self, input_data):
        return self.model.predict(input_data)