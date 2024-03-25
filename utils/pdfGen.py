import streamlit as st
from fpdf import FPDF
from datetime import datetime
import io
import base64

def create_download_link(val, filename = f'HNотчет_{datetime.now()}'):
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Загрузить отчет</a>'

def exportToPDF(htmlCode, imgBuffers: list):
    export_as_pdf = st.button("Экспорт отчета в PDF")
    if export_as_pdf:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(40, 10, htmlCode)
        for buf in imgBuffers:
            buf_ = io.BytesIO()
            buf.write_image(
                buf_,format="png",scale=2,
            )
            buf_.seek(0)
            pdf.image(buf_)
        html = create_download_link(pdf.output(dest="S").encode("latin-1"))
        st.markdown(html, unsafe_allow_html=True)