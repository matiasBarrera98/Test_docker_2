import streamlit as st
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.utils import get_file
import numpy as np
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from google.cloud import storage
from explain import main_funct
from datetime import datetime
import os
import json

from helpers import *

######################################################################################

# Funcionalidad almacenamiento de los datos

creds = Credentials.from_service_account_info(json.loads(os.getenv('GCP')))
bq_client = bigquery.Client(credentials=creds)
storage_client = storage.Client(credentials=creds)
model_url = "https://storage.googleapis.com/respaldo_api_cne/model_finetune.h5"

TABLA_PACIENTE = 'acquired-winter-316123.capstone.diagnostico'


def save_image(image):
    file_name = image.name
    bucket = storage_client.bucket('melanoma_capstone_bucket')
    blob = bucket.blob(file_name)
    try:
        blob.upload_from_file(file_obj=image, rewind=True)
    except Exception as e:
        st.error(f'Error al respaldar imágen {e}')
        return False
    else:
        return blob.public_url


def get_last_id():
    q = f'SELECT MAX(diagnostico_id) FROM {TABLA_PACIENTE}'
    res = bq_client.query(q)
    res = list(res)[0][0]
    return res if res else 0


def submit_info(img, fecha_nac, trabajo, region, enf_cron, sexo, fam, canc_ant, diag, prob, ai):
    last_id = get_last_id() + 1
    url_img = save_image(img)
    fecha_now = datetime.now().strftime('%Y-%m-%d')
    if url_img:
        record_dict = {
            'diagnostico_id': last_id,
            'fecha_nacimiento': fecha_nac.strftime('%Y-%m-%d'),
            'fecha_diagn': fecha_now,
            'sexo': sexo,
            'trabajo': trabajo,
            'region': region,
            'enfermedad_cronica': enf_cron,
            'fam_cancer': fam,
            'cancer_antes': canc_ant,
            'url_img': url_img,
            'radiologo': diag,
            'prob_ai': float(prob),
            'diag_ai': bool(ai)
        }
        try:
            bq_client.insert_rows_json(TABLA_PACIENTE, [record_dict])
        except Exception as e:
            st.error(f'Error al guardar los datos del paciente {e}')
            return False
        else:
            st.success(f'Datos Guardados Correctamente')
            return True

#####################################################################################

prediction = None

st.set_page_config(page_title="Melanoma AI", page_icon="🔬")

# Esquinas redondeadas de imágenes
st.markdown(
    f"""
    <style>
        img {{
            border-radius: 10px;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# Función de carga del model
@st.cache_resource
def load_model_from_file():
    path = get_file("model_finetune.h5", model_url)
    model = load_model(path)
    return model

model = load_model_from_file()


# Procesamiento Imágen subida por usuario
def preproc_img(image):
    img = load_img(image, target_size=(300, 300))
    img = img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img /= 255.0
    return img

st.title("AI para la detección del cáncer de piel")

# Widget para subir archivo a procesar
img = st.file_uploader("Selecciona la imágen a evaluar", type=None, label_visibility="visible")


# Proceso de predicción
if img is not None:
    size = (300,300)
    image = preproc_img(img)
    prob_pred = model.predict(image, verbose=0)[0][0]
    prediction = np.round(prob_pred) == 1
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"### Probabilidad de cáncer: \n ### {np.round(prob_pred * 100, 2)}%")
    with col2:
        st.image(img)
    with col3:
        st.image(main_funct(img, model))

# Formulario para los datos del paciente
with st.form('datos_paciente', clear_on_submit=True):
    st.subheader("Ingrese datos del paciente")
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_nac = st.date_input('Edad', format='DD/MM/YYYY')
        trabajo = st.selectbox(label="Trabajo", options=categorias_trabajo, placeholder="Elija una opción")
        region = st.selectbox(label="Región Residencia", options=regiones_chile, placeholder="Ingrese opción" )
        ef_cron = st.selectbox(label="Enfermedad crónica", options=enfermedades_cronicas_comunes, placeholder="Ingrese Opción...")
    with col2:
        sexo = st.radio('Sexo', ['Masculino', 'Femenino'])
        fam_canc = st.radio('Antecedentes familiares de cáncer', ['Si', 'No']) == 'Si'
        ant_cancer = st.radio('Paciente con cáncer anteriormente', ['Si', 'No']) == 'Si'
        canc_diag = st.radio('Diagnóstico Radiólogo', ['Maligno', 'Benigno', 'Requiere más evaluación'])
    colsub1, colsub2, colsub3 = st.columns(3)
    with colsub2:
        submit_button = st.form_submit_button('Enviar diagnóstico')

# Botón de submit
if submit_button:
    io = "Ingrese opción"
    if prediction is None or trabajo == io or region == io or ef_cron == io:
        st.error("Debes realizar una predicción con la IA y rellenar formulario")
    else:
        with st.spinner('Enviando los datos...'):
            corr = submit_info(img, fecha_nac, trabajo, region, 
                        ef_cron, sexo, fam_canc, ant_cancer, 
                        canc_diag, prob_pred, prediction)
        

    
