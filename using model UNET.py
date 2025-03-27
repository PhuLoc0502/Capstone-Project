from monai.networks.nets import UNet
import torch
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import os
import cv2

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Khởi tạo mô hình
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = UNet(
    spatial_dims=2,
    in_channels=1,
    out_channels=1,
    channels=(16, 32, 64, 128, 256),
    strides=(2, 2, 2, 2),
    num_res_units=2
).to(device)

# Load trọng số đã train
model.load_state_dict(torch.load("unet_xray_segmentation02.pth", map_location=device))
model.eval()  # Chuyển mô hình sang chế độ đánh giá

print("Model loaded successfully!")

# HÀM LOAD ẢNH VÀ CHUẨN HÓA
def load_image(image_path):
    image = Image.open(image_path).convert('L')  # Đọc ảnh grayscale
    image = image.resize((256, 256))  # Resize về kích thước (256,256)
    image = np.array(image, dtype=np.float32) / 255.0  # Chuẩn hóa về [0,1]
    image = np.expand_dims(image, axis=0)  # Thêm chiều kênh (1, H, W)
    return image

# HÀM TẠO ẢNH MASK CHỒNG LÊN ẢNH GỐC
def overlay_mask(image, mask, alpha=0.6):
    """ Chồng mask lên ảnh gốc với độ trong suốt alpha """
    mask = (mask * 255).astype(np.uint8)  # Chuyển mask về dạng uint8
    mask_colored = cv2.applyColorMap(mask, cv2.COLORMAP_JET)  # Áp heatmap màu
    mask_colored[mask == 0] = 0  # Loại bỏ vùng không có mask
    image_colored = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)  # Chuyển ảnh gốc sang BGR
    overlay = cv2.addWeighted(image_colored, 1 - alpha, mask_colored, alpha, 0)  # Kết hợp ảnh và mask
    return overlay

# Định nghĩa tập validation (Thay thế đường dẫn bằng dữ liệu thực tế)
test_img_path = "E:\\src DATN\\data\\Lung Segmentation\\CXR_png\\MCUCXR_0251_1.png"

# Load ảnh test
test_img = load_image(test_img_path)  # (1, 256, 256)

# Chuyển về tensor và đưa vào GPU nếu có
test_tensor = torch.tensor(test_img, dtype=torch.float32).unsqueeze(0).to(device)  # (B, 1, 256, 256)

# Dự đoán mask
with torch.no_grad():
    pred_mask = model(test_tensor).cpu().numpy()[0, 0]  # (256, 256)
    pred_mask = (pred_mask > 0.5).astype(np.uint8)  # Binarize mask (0 hoặc 1)

# Tạo ảnh mask chồng lên ảnh gốc
overlayed_image = overlay_mask(test_img[0], pred_mask)

# Hiển thị kết quả
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
axes[0].imshow(test_img[0], cmap="gray")
axes[0].set_title("Original X-ray")
axes[0].axis("off")

axes[1].imshow(pred_mask, cmap="gray")  # Mask màu xám
axes[1].set_title("Predicted Mask (Gray)")
axes[1].axis("off")

axes[2].imshow(overlayed_image)
axes[2].set_title("Overlay Mask on X-ray")
axes[2].axis("off")

plt.show()

########################################################################################
