from config import MESSAGE_KEY, MAIL_USER 
from email.message import EmailMessage
import smtplib

EMISOR = MAIL_USER
CONTRA = MESSAGE_KEY

async def send_email(to, subject, body):
    mensaje = EmailMessage()
    mensaje['Subject'] = subject
    mensaje['From'] = EMISOR
    mensaje['To'] = to
    mensaje.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMISOR, CONTRA)
            smtp.send_message(mensaje)
    except Exception as e:
        return {"error": str(e)}

    return {"message": "Correo enviado correctamente"}
