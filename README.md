# 🤖 Vigilante Automático de Notificaciones (BOE)

Este proyecto automatiza la búsqueda de notificaciones en el **BOE (Tablón Edictal Único)**. Utiliza Python y Selenium para realizar consultas diarias y envía un informe detallado por correo electrónico, incluyendo una **captura de pantalla** de los resultados encontrados.

Funciona de forma 100% gratuita en la nube mediante **GitHub Actions**. No necesitas un servidor propio ni tener tu ordenador encendido.

---

## ✨ Características principales
* **Búsqueda Multi-criterio**: Permite vigilar DNI, nombres, matrículas o expedientes simultáneamente.
* **Captura de Pantalla**: Adjunta una imagen real de la consulta como prueba visual.
* **Compatibilidad Universal**: Soporta cuentas de **Gmail, Outlook, Hotmail y Live**.
* **Ejecución Programada**: Configurado para ejecutarse automáticamente cada día (09:00 AM hora de España).
* **Privacidad y Seguridad**: Tus datos personales nunca se escriben en el código; se gestionan mediante secretos cifrados de GitHub.

---

## 🚀 Configuración paso a paso

### 1. Preparar tu cuenta de Correo
El robot necesita una **Contraseña de Aplicación** (código de 16 letras) para enviar correos de forma segura.

* **Si usas Gmail**: Sigue [estos pasos oficiales](https://support.google.com/accounts/answer/185833).
* **Si usas Outlook/Hotmail**: Sigue [estos pasos oficiales](https://support.microsoft.com/es-es/account-billing/uso-de-contrase%C3%B1as-de-aplicaci%C3%B3n-con-apps-que-no-admiten-la-verificaci%C3%B3n-en-dos-pasos-58018d96-580e-4a7b-9744-10439e65044a).

### 2. Crear tu propia copia (Fork)
Haz clic en el botón **"Fork"** arriba a la derecha en este repositorio para tener tu propia copia funcional.

### 3. Configurar tus Secretos
En tu repositorio, ve a **Settings** > **Secrets and variables** > **Actions** y añade estos secretos:

| Secreto | Descripción | Ejemplo |
| :--- | :--- | :--- |
| `EMAIL_ORIGEN` | Tu correo emisor. | `tu_correo@gmail.com` |
| `EMAIL_PASSWORD` | El código de 16 letras de la App. | `abcd efgh ijkl mnop` |
| `EMAIL_DESTINO` | Correo donde recibirás la alerta. | `avisos@correo.com` |
| `TEXTO_BUSQUEDA` | Tu DNI, Matrícula o Nombre. | `"JUAN PEREZ" .O 12345678X` |
| `FECHA_DESDE` | Opcional. Fecha mínima de publicación para evitar avisos repetidos de notificaciones antiguas. | `26/04/2026` |
| `FECHA_HASTA` | Opcional. Fecha máxima de publicación si quieres acotar un periodo cerrado. | `30/04/2026` |

---

## 📅 Acotar la búsqueda por fecha

Si el BOE ya ha publicado una notificación y no quieres recibir la misma alerta todos los días, añade el secreto opcional `FECHA_DESDE` en **Settings** > **Secrets and variables** > **Actions**.

Para buscar solo publicaciones posteriores a una notificación ya detectada, usa el día siguiente como `FECHA_DESDE`. Por ejemplo, si la notificación salió el `25/04/2026`, configura `FECHA_DESDE` como `26/04/2026`.

El formato recomendado es `DD/MM/AAAA`, aunque el script también acepta `AAAA-MM-DD`. Si necesitas revisar un intervalo concreto, también puedes añadir `FECHA_HASTA`.

---

## 💡 Cómo usar el buscador avanzado (`.O`)

El script permite el uso del operador **`.O`** (mayúsculas y con puntos) para vigilar varios datos a la vez:

* **Persona + DNI**: `"PEDRO GARCIA" .O 12345678X`
* **Varios vehículos**: `1234ABC .O 5678DEF`
* **Combinado**: `"PEDRO GARCIA" .O 12345678X .O 1234ABC`

---

## 🕒 Frecuencia de ejecución
El sistema se ejecuta diariamente a las **09:00 AM (España)**.
Para cambiarlo, edita `.github/workflows/main.yml` en la línea:
`cron: '0 8 * * *'` (Formato UTC).

---

## ⚖️ Descargo de Responsabilidad (Disclaimer)

Este software se proporciona "tal cual", sin garantía de ningún tipo. Su uso es bajo su propia responsabilidad.

* **No oficial**: Este proyecto NO es un servicio oficial del BOE ni de ningún organismo público.
* **Responsabilidad**: El usuario debe verificar sus notificaciones por cauces oficiales. El autor no responde por fallos técnicos o cambios en la web del BOE.
* **Privacidad**: El script no recopila datos; todo se gestiona de forma privada en su entorno de GitHub.

---

## 🛠️ Instalación Local
1. Instala dependencias: `pip install -r requirements.txt`.
2. Configura tus variables de entorno.
3. Ejecuta: `python vigilante.py`.

---
⭐ Si te resulta útil, ¡dale una estrella al repositorio!
