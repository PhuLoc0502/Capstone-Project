import cv2
import numpy as np

def is_dark_image(image, threshold=100):
    """Xét ảnh có tối không dựa vào độ sáng trung bình."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    print(f"Độ sáng trung bình: {brightness}")
    return brightness < threshold

def main():
    # Đường dẫn ảnh
    image_path = "C:\\Users\\pc\\Downloads\\Screenshot 2025-04-08 111752.png"

    # Đọc ảnh
    image = cv2.imread(image_path)

    if image is None:
        print("Không đọc được ảnh.")
        return

    # Kiểm tra ảnh tối
    if is_dark_image(image):
        print("Ảnh tối → Tiến hành đảo màu.")
        image = cv2.bitwise_not(image)
    else:
        print("Ảnh sáng → Không cần đảo màu.")

    # Hiển thị ảnh
    cv2.imshow("Ảnh hiển thị", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
