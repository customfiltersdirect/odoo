import base64
import io
from pikepdf import Pdf
from odoo import tools

class PikePdfStack:
    def process_from_stack(self):
        pdf = Pdf.new()

        for document in self:
            try:
                src = Pdf.open(io.BytesIO(base64.b64decode(document)))
                pdf.pages.extend(src.pages)
            except Exception as e:
                print("Reader Error: ",e)
                continue

        _buffer = io.BytesIO()
        pdf.save(_buffer)
        merged_pdf = _buffer.getvalue()
        _buffer.close()

        return merged_pdf

tools.pike_pdf_merge = PikePdfStack
