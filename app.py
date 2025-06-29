
from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF
from datetime import datetime
import random
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_postcard', methods=['POST'])
def generate_postcard():
    name = request.form['name']
    address1 = request.form['address1']
    address2 = request.form['address2']
    address3 = request.form['address3']
    address4 = request.form['address4']
    zipcode = request.form['zipcode']
    message = request.form['message']

    # Replace date placeholder
    today_date = datetime.now().strftime("%d %b %Y")
    message = message.replace("Today's date", today_date)

    doc = fitz.open("india_mail_postcard_message.pdf")
    page = doc[0]

    # --- To Address --- #
    page.insert_text((300, 105), name, fontsize=12, fontname="helv")
    page.insert_text((300, 135), address1, fontsize=12, fontname="helv")
    page.insert_text((300, 165), address2, fontsize=12, fontname="helv")
    page.insert_text((300, 195), address3, fontsize=12, fontname="helv")
    page.insert_text((300, 225), address4, fontsize=12, fontname="helv")
    page.insert_text((320, 200), zipcode, fontsize=12, fontname="helv")

    # --- Message --- #
    # Define the message area on the left side of the postcard
    message_rect = fitz.Rect(20, 50, 280, 280)  # x0, y0, x1, y1

    # Insert the new message, top-aligned
    page.insert_textbox(message_rect, message, fontsize=12, fontname="helv", align=fitz.TEXT_ALIGN_LEFT)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = random.randint(1000, 9999)
    filename = f"postcard_{timestamp}_{random_num}.pdf"
    output_path = f"static/{filename}"
    doc.save(output_path)
    doc.close()
    return render_template("postcard.html", postcard_url=output_path, filename=filename)

@app.route('/delete/<filename>')
def delete_file(filename):
    try:
        os.remove(f"static/{filename}")
        return "", 204
    except FileNotFoundError:
        return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)
