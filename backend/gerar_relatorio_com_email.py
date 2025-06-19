import smtplib
from email.message import EmailMessage
from fpdf import FPDF
import datetime
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

EMAIL_ORIGEM = os.getenv("EMAIL_ORIGEM")
SENHA_APP = os.getenv("SENHA_APP")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")

# === Gerar relatório PDF simples com logo ===
def gerar_pdf(nome_arquivo="relatorio_avaliacao.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Relatório de Avaliação do Modelo", ln=True, align="C")
    pdf.ln(10)

    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=20, w=40)
        pdf.ln(30)

    pdf.set_font("Arial", "", 12)
    data = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(200, 10, f"Gerado em: {data}", ln=True)

    pdf.ln(10)
    pdf.multi_cell(0, 10, "Este é um relatório automático gerado pelo sistema de predição forense.\nOs dados estão disponíveis no dashboard.")

    pdf.output(nome_arquivo)
    print(f"✅ PDF gerado: {nome_arquivo}")
    return nome_arquivo

# === Enviar e-mail com o PDF em anexo ===
def enviar_email(anexo_pdf):
    msg = EmailMessage()
    msg["Subject"] = "📊 Relatório de Avaliação do Modelo"
    msg["From"] = EMAIL_ORIGEM
    msg["To"] = EMAIL_DESTINO
    msg.set_content("Olá,\n\nSegue em anexo o relatório automático gerado pelo sistema.\n\nAtt,\nSistema Forense")

    with open(anexo_pdf, "rb") as f:
        pdf_data = f.read()
        msg.add_attachment(pdf_data, maintype="application", subtype="pdf", filename=anexo_pdf)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ORIGEM, SENHA_APP)
        smtp.send_message(msg)
        print("📧 E-mail enviado com sucesso!")

if __name__ == "__main__":
    nome_pdf = gerar_pdf()
    enviar_email(nome_pdf)
