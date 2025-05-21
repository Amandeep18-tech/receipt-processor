import spacy
import subprocess

def load_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except:
        subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
        return spacy.load("en_core_web_sm")

nlp = load_spacy_model()
