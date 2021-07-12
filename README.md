# clearpath_extract
This app is responsible for:
    1 - making inferences with your model stored in model.pickle
    2 - Generating a PCPR and emailing it to the patient
    3 - emailing the report to the patient


1. Your model:
    - This project expects your model to be stored in a file named model.pickle in the base directory of this project
    - This project expects your model to have a method named predict (i.e y = model.predict(x)).
        - See src/model_wrapper.py and change the predict code as needed
    
    - Predictions:
        - Predictions are expected to be sequential, 1 for every sentence in the input data.
    
2. PCPR Gtion and Email
    - the PCPR generation code provided is not very configurable and is more of a draft. Apologies, but you'll likely need 
        to do a lot of testing to generate the pdf image that you are looking for.
      
    - Your email username and password should be stored in credentials.txt, space delimited.