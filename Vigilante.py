import os
import time
import smtplib
from datetime import datetime
from email.message import EmailMessage
from selenium import webdriver
from selenium.common.exceptions import InvalidElementStateException
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
FECHA_DESDE = os.environ.get('FECHA_DESDE')
FECHA_HASTA = os.environ.get('FECHA_HASTA')

FORMATO_FECHA_BOE = "%d/%m/%Y"
FORMATOS_FECHA_ADMITIDOS = (FORMATO_FECHA_BOE, "%Y-%m-%d")

URL_BOE = "https://www.boe.es/notificaciones/notificaciones.php"
FRASE_SIN_RESULTADOS = "No se han encontrado documentos que satisfagan sus criterios de búsqueda"


def normalizar_fecha(fecha):
    if not fecha:
        return None

    fecha = fecha.strip()
    if not fecha:
        return None

    for formato in FORMATOS_FECHA_ADMITIDOS:
        try:
            return datetime.strptime(fecha, formato).strftime(FORMATO_FECHA_BOE)
        except ValueError:
            continue

    raise ValueError(
        f"Formato de fecha no válido: {fecha}. Usa DD/MM/AAAA o AAAA-MM-DD."
    )


def valor_para_input(campo, valor):
    tipo = (campo.get_attribute("type") or "").lower()
    if tipo == "date":
        return datetime.strptime(valor, FORMATO_FECHA_BOE).strftime("%Y-%m-%d")
    return valor


def campo_tiene_valor(campo, valor):
    valor_actual = campo.get_attribute("value")
    return valor_actual in {valor, valor_para_input(campo, valor)}


def describir_campo(campo):
    atributos = []
    for atributo in ("name", "id", "type", "placeholder"):
        valor = campo.get_attribute(atributo)
        if valor:
            atributos.append(f"{atributo}='{valor}'")
    return ", ".join(atributos) if atributos else "sin atributos identificativos"


def rellenar_campo(campo, valor, driver=None, nombre_campo="campo"):
    if valor is None:
        return

    valor_input = valor_para_input(campo, valor)
    driver = driver or getattr(campo, "_parent", None)

    if driver:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)

    usar_javascript = False
    try:
        if campo.is_displayed() and campo.is_enabled():
            campo.clear()
            campo.send_keys(valor_input)
            if campo_tiene_valor(campo, valor):
                return
            print(f"{nombre_campo} no quedó fijado con escritura normal; se usará JavaScript.")
            usar_javascript = True
        else:
            print(f"{nombre_campo} no está visible o habilitado; se usará JavaScript si es posible.")
            usar_javascript = True
    except InvalidElementStateException:
        print(f"{nombre_campo} no permite escritura normal; se usará JavaScript si es posible.")
        usar_javascript = True

    if usar_javascript and driver:
        driver.execute_script(
            """
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """,
            campo,
            valor_input,
        )

    if campo_tiene_valor(campo, valor):
        print(f"{nombre_campo} fijado correctamente mediante JavaScript.")
    else:
        print(f"Aviso: {nombre_campo} podría no haberse fijado correctamente.")


def input_rellenable(campo):
    tipo = (campo.get_attribute("type") or "text").lower()
    return tipo not in {"hidden", "submit", "button", "image", "radio", "checkbox"}


def ordenar_campos_por_preferencia(campos):
    unicos = []
    ids_vistos = set()
    for campo in campos:
        if campo.id in ids_vistos or not input_rellenable(campo):
            continue
        ids_vistos.add(campo.id)
        unicos.append(campo)

    visibles_habilitados = [campo for campo in unicos if campo.is_displayed() and campo.is_enabled()]
    fallback = [campo for campo in unicos if campo not in visibles_habilitados]
    return visibles_habilitados + fallback


def obtener_campos_fecha(driver):
    minusculas = "abcdefghijklmnopqrstuvwxyzáéíóúüñ"
    mayusculas = "ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ"
    traducir_atributos = (
        f"translate(concat(@name, ' ', @id, ' ', @placeholder), '{mayusculas}', '{minusculas}')"
    )
    xpath_explicitos = (
        "//input[not(translate(@type, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='hidden') "
        "and (translate(@type, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='date' "
        f"or contains({traducir_atributos}, 'fecha'))]"
    )

    campos_explicitos = ordenar_campos_por_preferencia(
        driver.find_elements(By.XPATH, xpath_explicitos)
    )
    visibles_explicitos = [campo for campo in campos_explicitos if campo.is_displayed() and campo.is_enabled()]
    if len(visibles_explicitos) >= 2:
        return visibles_explicitos[:2]

    xpath_etiquetas = (
        f"//*[contains(translate(normalize-space(.), '{mayusculas}', '{minusculas}'), "
        "'fecha de publicación')]"
    )
    etiquetas = driver.find_elements(By.XPATH, xpath_etiquetas)
    etiquetas.sort(key=lambda etiqueta: len(etiqueta.text or ""))

    tipo_normalizado = "translate(@type, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
    xpath_inputs_posteriores = (
        "(following::input[not("
        f"{tipo_normalizado}='hidden' or {tipo_normalizado}='submit' or "
        f"{tipo_normalizado}='button' or {tipo_normalizado}='image' or "
        f"{tipo_normalizado}='radio' or {tipo_normalizado}='checkbox')])[position() <= 6]"
    )

    for etiqueta in etiquetas:
        campos = ordenar_campos_por_preferencia(
            etiqueta.find_elements(By.XPATH, xpath_inputs_posteriores)
        )
        visibles = [campo for campo in campos if campo.is_displayed() and campo.is_enabled()]
        if len(visibles) >= 2:
            return visibles[:2]
        if len(campos) >= 2:
            return campos[:2]

    return campos_explicitos


def aplicar_filtro_fechas(driver):
    fecha_desde = normalizar_fecha(FECHA_DESDE)
    fecha_hasta = normalizar_fecha(FECHA_HASTA)

    if not fecha_desde and not fecha_hasta:
        return None, None

    campos_fecha = obtener_campos_fecha(driver)

    if fecha_desde and len(campos_fecha) < 1:
        raise RuntimeError("No se ha podido localizar el campo de fecha inicial del formulario del BOE.")
    if fecha_hasta and len(campos_fecha) < 2:
        raise RuntimeError("No se ha podido localizar el campo de fecha final del formulario del BOE.")

    if fecha_desde:
        print(f"Aplicando FECHA_DESDE: {fecha_desde} en {describir_campo(campos_fecha[0])}")
        rellenar_campo(campos_fecha[0], fecha_desde, driver, "FECHA_DESDE")
    if fecha_hasta:
        print(f"Aplicando FECHA_HASTA: {fecha_hasta} en {describir_campo(campos_fecha[1])}")
        rellenar_campo(campos_fecha[1], fecha_hasta, driver, "FECHA_HASTA")

    return fecha_desde, fecha_hasta


def descripcion_filtro_fechas(fecha_desde, fecha_hasta):
    if fecha_desde and fecha_hasta:
        return f" entre el {fecha_desde} y el {fecha_hasta}"
    if fecha_desde:
        return f" desde el {fecha_desde}"
    if fecha_hasta:
        return f" hasta el {fecha_hasta}"
    return ""


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
        rellenar_campo(input_texto, TEXTO_BUSQUEDA, driver, "TEXTO_BUSQUEDA")
        fecha_desde, fecha_hasta = aplicar_filtro_fechas(driver)
        input_texto.send_keys(Keys.ENTER)

        filtro_fechas = descripcion_filtro_fechas(fecha_desde, fecha_hasta)

        time.sleep(5)
        driver.save_screenshot(ruta_captura)

        cuerpo = driver.find_element(By.TAG_NAME, "body").text

        if FRASE_SIN_RESULTADOS.lower() in cuerpo.lower():
            asunto = f"✅ BOE: Limpio ({TEXTO_BUSQUEDA})"
            mensaje = f"Consulta automática realizada{filtro_fechas}. No hay notificaciones nuevas para {TEXTO_BUSQUEDA}."
        else:
            asunto = f"⚠️ ALERTA: Notificación encontrada ({TEXTO_BUSQUEDA})"
            mensaje = f"Se han detectado resultados{filtro_fechas}. Revisa la captura adjunta o accede a: {URL_BOE}"

        enviar_correo_con_foto(asunto, mensaje, ruta_captura)
    finally:
        driver.quit()


if __name__ == "__main__":
    vigilancia_diaria()
