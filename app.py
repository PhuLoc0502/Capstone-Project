import os
import torch
import numpy as np
import cv2
import pydicom
import base64
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from monai.networks.nets import UNet
from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Kiểm tra handlers DICOM
try:
    import gdcm
    HAVE_GDCM = True
except ImportError:
    HAVE_GDCM = False

try:
    import pylibjpeg
    HAVE_PYLIBJPEG = True
except ImportError:
    HAVE_PYLIBJPEG = False

def load_model():
    model = UNet(
        spatial_dims=2,
        in_channels=1,
        out_channels=1,
        channels=( 32, 64, 128, 256, 512 ),
        strides=(2, 2, 2, 2),
        num_res_units=2,
    )
    model.load_state_dict(torch.load("unet_xray_segmentation1418.pth", map_location=torch.device('cpu')))
    model.eval()
    return model

model = load_model()

def safe_dicom_value(dicom, tag, default='N/A'):
    """Lấy giá trị DICOM an toàn với nhiều fallback"""
    try:
        # Thử lấy theo attribute
        value = getattr(dicom, tag, default)
        if value and str(value).strip():
            return str(value)
        
        # Thử lấy theo tag
        if hasattr(dicom, 'get'):
            value = dicom.get(tag, default)
            if value and str(value).strip():
                return str(value)
                
        return str(default)
    except:
        return str(default)

def extract_metadata(dicom):
    """Trích xuất metadata với xử lý lỗi đầy đủ"""
    return {
        'patient_name': safe_dicom_value(dicom, 'PatientName'),
        'patient_id': safe_dicom_value(dicom, 'PatientID'),
        'study_date': safe_dicom_value(dicom, 'StudyDate'),
        'modality': safe_dicom_value(dicom, 'Modality')
    }

# def process_dicom_pixels(dicom):
#     """Xử lý pixel data với giải nén tự động và chuẩn hóa"""
#     try:
#         # Thử giải nén tự động
#         pixel_array = dicom.pixel_array
#     except:
#         if HAVE_GDCM:
#             try:
#                 dicom.decompress('gdcm')
#                 pixel_array = dicom.pixel_array
#             except:
#                 if HAVE_PYLIBJPEG:
#                     try:
#                         dicom.decompress('pylibjpeg')
#                         pixel_array = dicom.pixel_array
#                     except:
#                         raise ValueError("Không thể giải nén DICOM với các thư viện hiện có")
#                 else:
#                     raise ValueError("Không tìm thấy thư viện giải nén phù hợp")
    
#     # Áp dụng các phép biến đổi
#     pixel_array = apply_modality_lut(pixel_array, dicom)
#     pixel_array = apply_voi_lut(pixel_array, dicom)
    
#     # Chuẩn hóa ảnh về dạng uint8 (0-255)
#     if pixel_array.dtype != np.uint8:
#         pixel_array = (pixel_array - np.min(pixel_array)) / (np.max(pixel_array) - np.min(pixel_array)) * 255
#         pixel_array = pixel_array.astype(np.uint8)
    
#     # Đảm bảo ảnh là grayscale 1 channel
#     if len(pixel_array.shape) == 3:
#         pixel_array = cv2.cvtColor(pixel_array, cv2.COLOR_RGB2GRAY)
#     elif len(pixel_array.shape) > 3:
#         raise ValueError("Ảnh DICOM có số chiều không hỗ trợ")
    
#     return pixel_array
########################################################################################################################
def process_dicom_pixels(dicom):
    """Xử lý pixel data với giải nén tự động, chuẩn hóa và đảo màu"""
    try:
        # Thử giải nén tự động
        pixel_array = dicom.pixel_array
    except:
        if HAVE_GDCM:
            try:
                dicom.decompress('gdcm')
                pixel_array = dicom.pixel_array
            except:
                if HAVE_PYLIBJPEG:
                    try:
                        dicom.decompress('pylibjpeg')
                        pixel_array = dicom.pixel_array
                    except:
                        raise ValueError("Không thể giải nén DICOM với các thư viện hiện có")
                else:
                    raise ValueError("Không tìm thấy thư viện giải nén phù hợp")
    
    # Áp dụng các phép biến đổi
    pixel_array = apply_modality_lut(pixel_array, dicom)
    pixel_array = apply_voi_lut(pixel_array, dicom)
    
    # Chuẩn hóa ảnh về dạng uint8 (0-255)
    if pixel_array.dtype != np.uint8:
        pixel_array = (pixel_array - np.min(pixel_array)) / (np.max(pixel_array) - np.min(pixel_array)) * 255
        pixel_array = pixel_array.astype(np.uint8)
    
    # Đảo màu ảnh DICOM (vì ảnh X-quang thường cần invert)
    pixel_array = cv2.bitwise_not(pixel_array)
    
    # Đảm bảo ảnh là grayscale 1 channel
    if len(pixel_array.shape) == 3:
        pixel_array = cv2.cvtColor(pixel_array, cv2.COLOR_RGB2GRAY)
    elif len(pixel_array.shape) > 3:
        raise ValueError("Ảnh DICOM có số chiều không hỗ trợ")
    
    return pixel_array
########################################################################################################################

@app.route('/')
def home():
    return render_template('web.html')

@app.route('/info')
def info():
    return render_template('info.html')

@app.route('/process-dicom', methods=['POST'])
def process_dicom():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded', 'metadata': {}})
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected', 'metadata': {}})
    
    try:
        # Lưu file tạm
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Đọc DICOM
        dicom = pydicom.dcmread(filepath, force=True)
        print(f"\nĐang xử lý: {filename}")
        print(f"Transfer Syntax: {getattr(dicom.file_meta, 'TransferSyntaxUID', 'Unknown')}")
        
        # Xử lý ảnh và chuẩn hóa
        original_img = process_dicom_pixels(dicom)
        
        # Resize về kích thước model yêu cầu (256x256)
        original_img = cv2.resize(original_img, (256, 256))
        
        # Kiểm tra lại số kênh màu
        if len(original_img.shape) == 2:
            original_img = np.expand_dims(original_img, axis=-1)  # Thêm channel dimension
        
        # Chuẩn bị đầu vào cho model
        img_input = original_img.astype(np.float32) / 255.0
        img_input = np.expand_dims(img_input, axis=0)  # Thêm batch dimension
        
        # Dự đoán bằng model
        tensor_img = torch.tensor(img_input, dtype=torch.float32).permute(0, 3, 1, 2)
        
        with torch.no_grad():
            output = model(tensor_img)
        
        # Xử lý kết quả
        pred_mask = (output.squeeze().numpy() > 0.5).astype(np.uint8) * 255
        
        # Tạo overlay
        overlay = cv2.addWeighted(
            cv2.cvtColor(original_img, cv2.COLOR_GRAY2BGR),
            0.7,
            cv2.applyColorMap(pred_mask, cv2.COLORMAP_JET),
            0.3,
            0
        )
        
        # Chuyển đổi sang base64 (định dạng PNG)
        _, buffer_orig = cv2.imencode('.png', original_img)
        _, buffer_mask = cv2.imencode('.png', pred_mask)
        _, buffer_overlay = cv2.imencode('.png', overlay)
        
        return jsonify({
            'original': f"data:image/png;base64,{base64.b64encode(buffer_orig).decode('utf-8')}",
            'mask': f"data:image/png;base64,{base64.b64encode(buffer_mask).decode('utf-8')}",
            'overlay': f"data:image/png;base64,{base64.b64encode(buffer_overlay).decode('utf-8')}",
            'metadata': extract_metadata(dicom),
            'width': original_img.shape[1],
            'height': original_img.shape[0]
        })
        
    except Exception as e:
        print(f"Lỗi xử lý: {str(e)}")
        return jsonify({
            'error': str(e),
            'metadata': {
                'patient_name': 'Error',
                'patient_id': 'Error',
                'study_date': 'Error',
                'modality': 'Error'
            }
        })

if __name__ == '__main__':
    print("\n=== CẤU HÌNH HỆ THỐNG ===")
    print(f"GDCM: {'Có' if HAVE_GDCM else 'Không'}")
    print(f"pylibjpeg: {'Có' if HAVE_PYLIBJPEG else 'Không'}")
    print("=========================")
    
    app.run(debug=True)