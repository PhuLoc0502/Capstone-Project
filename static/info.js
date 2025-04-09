// Khởi tạo các biến toàn cục
let dicomElement = document.getElementById('dicomViewer');
let imageElement = null;
let brightness = 0;
let scale = 1;
let rotation = 0;
let flipHorizontal = false;
let flipVertical = false;

// Hiển thị ảnh PNG/JPEG từ server
function displayOriginalImage(imageUrl) {
    dicomElement.innerHTML = '';
    imageElement = document.createElement('img');
    imageElement.src = imageUrl;
    
    // Đặt kích thước hiển thị ban đầu là 525x525px
    imageElement.style.width = '525px';
    imageElement.style.height = '525px';
    imageElement.style.objectFit = 'contain'; // Giữ tỷ lệ ảnh gốc
    imageElement.style.position = 'absolute';
    imageElement.style.top = '50%';
    imageElement.style.left = '50%';
    imageElement.style.transformOrigin = 'center';
    dicomElement.appendChild(imageElement);

    dicomElement.style.width = '525px'; // Đồng bộ với .dicom-container
    dicomElement.style.height = '525px';
    dicomElement.style.position = 'relative';
    dicomElement.style.backgroundColor = '#000';
    dicomElement.style.overflow = 'hidden';

    updateImageDisplay();
}

// Cập nhật hiển thị ảnh với các hiệu ứng
function updateImageDisplay() {
    if (!imageElement) return;
    imageElement.style.filter = `brightness(${100 + brightness}%)`;
    const scaleX = flipHorizontal ? -1 : 1;
    const scaleY = flipVertical ? -1 : 1;
    imageElement.style.transform = `translate(-50%, -50%) scale(${scale}) scaleX(${scaleX}) scaleY(${scaleY}) rotate(${rotation}deg)`;
}

// Hiển thị kết quả AI
// function displayAIResults(data) {
//     const resultContainer = document.getElementById('resultImages');
//     resultContainer.innerHTML = `
//         <div class="ai-results">
//             <div class="result-item">
//                 <h4>Ảnh Gốc</h4>
//                 <img src="${data.original}" class="result-img">
//             </div>
//             <div class="result-item">
//                 <h4>Vùng Phân Vùng</h4>
//                 <img src="${data.mask}" class="result-img">
//             </div>
//             <div class="result-item">
//                 <h4>Kết Quả Phân Tích</h4>
//                 <img src="${data.overlay}" class="result-img">
//             </div>
//         </div>
//     `;
//     displayDicomInfo(data.metadata);
// }

// // Hiển thị metadata
// function displayDicomInfo(metadata) {
//     const metaContainer = document.getElementById('dicomMetadata');
//     metaContainer.innerHTML = `
//         <p><strong>Tên Bệnh Nhân:</strong> ${metadata.patient_name}</p>
//         <p><strong>ID Bệnh Nhân:</strong> ${metadata.patient_id}</p>
//         <p><strong>Ngày Chụp:</strong> ${metadata.study_date}</p>
//         <p><strong>Loại Hình Ảnh:</strong> ${metadata.modality}</p>
//     `;
// }

function displayAIResults(data) {
    const resultContainer = document.getElementById('resultImages');
    resultContainer.innerHTML = `
        <div class="ai-results">
            <div class="result-item">
                <h4>Ảnh Gốc</h4>
                <img src="${data.original}" class="result-img" data-type="original">
            </div>
            <div class="result-item">
                <h4>Vùng Phân Vùng</h4>
                <img src="${data.mask}" class="result-img" data-type="mask">
            </div>
            <div class="result-item">
                <h4>Kết Quả Phân Tích</h4>
                <img src="${data.overlay}" class="result-img" data-type="overlay">
            </div>
        </div>
    `;
    displayDicomInfo(data.metadata);

    // Gắn sự kiện nháy đúp để đổi ảnh chính
    const resultImages = document.querySelectorAll('.result-img');
    resultImages.forEach(img => {
        img.addEventListener('dblclick', () => {
            displayOriginalImage(img.src);
        });
    });
}



// Xử lý upload DICOM
document.getElementById('dicomInput').addEventListener('change', async function(e) {
    const file = e.target.files[0];
    if (!file) return;

    dicomElement.innerHTML = '<p>Đang tải ảnh...</p>';
    document.getElementById('dicomMetadata').innerHTML = '';
    document.getElementById('resultImages').innerHTML = '';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/process-dicom', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(await response.text());
        }

        const data = await response.json();
        if (data.error) {
            throw new Error(data.error);
        }

        displayOriginalImage(data.original);
        displayAIResults(data);

    } catch (error) {
        console.error('Lỗi:', error);
        dicomElement.innerHTML = `<p style="color:red">Lỗi: ${error.message}</p>`;
    }
});

// Các công cụ xem ảnh
function adjustBrightness(value) {
    brightness += value;
    updateImageDisplay();
}

function zoomImage(value) {
    scale = Math.max(0.1, scale + value);
    updateImageDisplay();
}

function rotateImage() {
    rotation = (rotation + 90) % 360;
    updateImageDisplay();
}

function flipHorizontalImage() {
    flipHorizontal = !flipHorizontal;
    updateImageDisplay();
}

function flipVerticalImage() {
    flipVertical = !flipVertical;
    updateImageDisplay();
}

function displayDicomInfo(metadata) {
    const metaContainer = document.getElementById('dicomMetadata');
    metaContainer.innerHTML = `
        <p><strong>Tên Bệnh Nhân:</strong> ${metadata.patient_name}</p>
        <p><strong>ID Bệnh Nhân:</strong> ${metadata.patient_id}</p>
        <p><strong>Ngày Chụp:</strong> ${metadata.study_date}</p>
        <p><strong>Loại Hình Ảnh:</strong> ${metadata.modality}</p>
    `;
}
