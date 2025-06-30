
from flask import Flask, render_template, request, send_file, Response
import fitz  # PyMuPDF
import io
from datetime import datetime
import random
import os
import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()
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

    # --- Stamp --- #
    # 450,10,530,90
    stamp_rect = fitz.Rect(350,0,560,105)
    page.insert_image(stamp_rect, filename="stamped.png")

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
    # Save PDF to a memory buffer
    pdf_buffer = io.BytesIO()
    doc.save(pdf_buffer)
    doc.close()
    pdf_buffer.seek(0)

    # Upload to S3
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION'),
        config=Config(signature_version='s3v4')
    )
    bucket_name = os.environ.get('AWS_BUCKET')
    s3.upload_fileobj(pdf_buffer, bucket_name, 'test/' + filename)

    return render_template("postcard.html", filename=filename)

@app.route('/get_postcard_pdf/<filename>')
def get_postcard_pdf(filename):
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION'),
        config=Config(signature_version='s3v4')
    )
    bucket_name = os.environ.get('AWS_BUCKET')
    s3_key = 'test/' + filename

    try:
        s3_response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        
        return Response(
            s3_response['Body'].read(),
            mimetype='application/pdf'
        )
    except s3.exceptions.NoSuchKey:
        return "File not found on S3", 404

@app.route('/delete/<filename>')
def delete_file(filename):
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION'),
            config=Config(signature_version='s3v4')
        )
        bucket_name = os.environ.get('AWS_BUCKET')
        s3.delete_object(Bucket=bucket_name, Key='test/' + filename)
        return "", 204
    except Exception as e:
        print(f"Error deleting file from S3: {e}")
        return "Error deleting file", 500

if __name__ == '__main__':
    app.run("0.0.0.0", debug=True)
