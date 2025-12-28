import os
import time
import smtplib
from email.message import EmailMessage
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ---
TEXTO_BUSQUEDA = os.environ.get('TEXTO_BUSQUEDA')
EMAIL_ORIGEN = os.environ.get('EMAIL_ORIGEN')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
EMAIL_DESTINO = os.environ.get('EMAIL_DESTINO')

URL_BOE = "https://www.boe.es/notificaciones/notificaciones.php"
FRASE_SIN_RESULTADOS = "No se han encontrado documentos que satisfagan sus criterios de búsqueda"

def enviar_correo_con_foto(asunto, mensaje, ruta_foto):
    msg = EmailMessage()
    msg.set_content(mensaje)
    msg['Subject'] = asunto
    msg['From'] = EMAIL_ORIGEN
    msg['To'] = EMAIL_DESTINO

    if os.path.exists(ruta_foto):
        with open(ruta_foto, 'rb') as f:
            file_data = f.read()
            msg.add_attachment(file_data, maintype='image', subtype='png', filename='captura_boe.png')

    # Configuración de Servidores SMTP
    if "gmail.com" in EMAIL_ORIGEN.lower():
        smtp_server, puerto = "smtp.gmail.com", 465
        metodo = "SSL"
    else: # Outlook / Hotmail / Live
        smtp_server, puerto = "smtp-mail.outlook.com", 587
        metodo = "STARTTLS"

    try:
        if metodo == "SSL":
            with smtplib.SMTP_SSL(smtp_server, puerto) as smtp:
                smtp.login(EMAIL_ORIGEN, EMAIL_PASSWORD)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, puerto) as smtp:
                smtp.starttls()
                smtp.login(EMAIL_ORIGEN, EMAIL_PASSWORD)
                smtp.send_message(msg)
        print("Correo enviado con éxito.")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

def vigilancia_diaria():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 20)
    ruta_captura = "resultado.png"

    try:
        driver.get(URL_BOE)
        input_texto = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name^='dato']")))
        input_texto.send_keys(TEXTO_BUSQUEDA)
        input_texto.send_keys(Keys.ENTER)
        
        time.sleep(5)
        driver.save_screenshot(ruta_captura)
        
        cuerpo = driver.find_element(By.TAG_NAME, "body").text
        
        if FRASE_SIN_RESULTADOS.lower() in cuerpo.lower():
            asunto = f"✅ BOE: Limpio ({TEXTO_BUSQUEDA})"
            mensaje = f"Consulta automática realizada. No hay multas nuevas para la matrícula {TEXTO_BUSQUEDA}."
        else:
            asunto = f"⚠️ ALERTA: Notificación encontrada ({TEXTO_BUSQUEDA})"
            mensaje = f"Se han detectado resultados. Revisa la captura adjunta o accede a: {URL_BOE}"

        enviar_correo_con_foto(asunto, mensaje, ruta_captura)
    finally:
        driver.quit()

if __name__ == "__main__":
    vigilancia_diaria()
