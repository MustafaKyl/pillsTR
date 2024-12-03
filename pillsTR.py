import numpy as np
import pandas as pd
from google.cloud import vision
from google.oauth2.service_account import Credentials
import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json




#df = pd.read_excel("internship_datasets/pillListTR.xlsx")
#df.head()
#columns = np.array(df.iloc[1,:])
#df.columns = columns
#df.columns = df.columns.str.replace("\n"," ")
#df.columns
#df.drop([0,1], axis=0, inplace=True)
#df.index -=1
#df = df["İlaç Adı"].apply(lambda x:x.lower())
#df = pd.DataFrame(df)
#df.to_csv("internship_datasets/pillsTR.csv")



credentials_dict = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])

credentials = Credentials.from_service_account_info(credentials_dict)
client = vision.ImageAnnotatorClient(credentials=credentials)

df= pd.read_csv("pillsTR.csv")
df = df.iloc[:, 1:]

downloadImage = st.file_uploader("Resim Yükleyiniz")


if downloadImage is not None:
    st.image(downloadImage.getvalue())

    image = vision.Image(content=downloadImage.getvalue())

    response = client.text_detection(image=image)
    texts = response.text_annotations


    if texts:
        print(f"Tanımlanan metin: {texts[0].description}")
    else:
        print("Hiçbir metin tespit edilemedi.")

    text = texts[0].description
    text = re.sub(r"[^\w\s]", "", text)

    turkish_chars = {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "Ç": "C",
        "Ğ": "G",
        "İ": "I",
        "Ö": "O",
        "Ş": "S",
        "Ü": "U",
    }

    # Karakterleri değiştir
    for turkish_char, english_char in turkish_chars.items():
        text = text.replace(turkish_char, english_char)

    def get_side_effects(drug_name):
     try:
         url = f"https://www.ilacprospektusu.com/ilac/25/{drug_name}"
         response = requests.get(url)
         soup = BeautifulSoup(response.text, "html.parser")
         prospektus = soup.find(id="prospektus")
         for a_tag in prospektus.find_all('a'):
             a_tag.unwrap()
         return prospektus

     except Exception as e:
         st.header("Verileri çekerken bir hata oluştu!!!")


    def has_two_common_words(drug_name, text):
        # İlaç adını ve karşılaştırma metnini kelimelere ayır
        stop_words = ["mg", "film", "kaplı", "tablet"]

        # Stop words listesindeki kelimeleri kaldır
        drug_words = [word for word in drug_name.lower().split() if word not in stop_words]
        text_words = text.lower().split()

        # Kesişen kelimelerin sayısını kontrol et
        common_word_count = sum(1 for word in drug_words if word in text_words)

        # En az 3 eşleşme olup olmadığını kontrol et
        return common_word_count >= 2


    pillName = df.loc[
        (df["İlaç Adı"].apply(lambda x: has_two_common_words(x, text))) &
        (df["İlaç Adı"].apply(lambda x: x.split()[0].lower() in text.lower()))
        ].iloc[0]


    pillName = pillName.str.replace(" ", "-")
    side_effects = get_side_effects(pillName[0])

    st.markdown(side_effects,unsafe_allow_html=True)

