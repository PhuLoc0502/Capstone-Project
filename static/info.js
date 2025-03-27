// Cấu hình Cornerstone
cornerstoneWADOImageLoader.external.cornerstone = cornerstone;
cornerstoneWADOImageLoader.configure({
    beforeSend: function(xhr) {
        xhr.setRequestHeader('Accept', 'application/dicom');
    }
});

let currentImage = null;
let viewport = null;
let isDrawing = false;
let canvas = document.getElementById("overlayCanvas");
let ctx = canvas.getContext("2d");

// Hiển thị ảnh DICOM gốc
function displayOriginalImage(imageData, originalWidth, originalHeight) {
    const viewer = document.getElementById('dicomViewer');
    viewer.innerHTML = '';
    
    const img = new Image();
    img.onload = function() {
        const container = viewer.parentElement;
        const containerWidth = container.clientWidth;
        const containerHeight = container.clientHeight;
        
        // Tính tỷ lệ scale
        const scale = Math.min(
            containerWidth / originalWidth,
            containerHeight / originalHeight
        );
        
        const displayWidth = originalWidth * scale;
        const displayHeight = originalHeight * scale;
        
        // Tạo canvas
        const canvas = document.createElement('canvas');
        canvas.width = originalWidth;
        canvas.height = originalHeight;
        
        // Đặt style hiển thị
        canvas.style.width = `${displayWidth}px`;
        canvas.style.height = `${displayHeight}px`;
        
        // Vẽ ảnh
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, originalWidth, originalHeight);
        
        viewer.appendChild(canvas);
        setupCanvasOverlay(canvas);
    };
    img.src = imageData;
}

function setupCanvasOverlay(dicomCanvas) {
    const canvas = document.getElementById('overlayCanvas');
    const container = dicomCanvas.parentElement.parentElement;
    
    // Đặt kích thước overlay bằng với canvas DICOM
    canvas.width = dicomCanvas.width;
    canvas.height = dicomCanvas.height;
    
    // Đặt vị trí và kích thước hiển thị
    canvas.style.width = dicomCanvas.style.width;
    canvas.style.height = dicomCanvas.style.height;
    canvas.style.position = 'absolute';
    canvas.style.top = '50%';
    canvas.style.left = '50%';
    canvas.style.transform = 'translate(-50%, -50%)';
    
    // Xử lý sự kiện vẽ
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
}
// Hiển thị kết quả AI
function displayAIResults(data) {
    const resultContainer = document.getElementById('resultImages');
    resultContainer.innerHTML = `
        <div class="ai-results">
            <div class="result-item">
                <h4>Ảnh Gốc</h4>
                <img src="${data.original}" class="result-img">
            </div>
            <div class="result-item">
                <h4>Vùng Phân Vùng</h4>
                <img src="${data.mask}" class="result-img">
            </div>
            <div class="result-item">
                <h4>Kết Quả Phân Tích</h4>
                <img src="${data.overlay}" class="result-img">
            </div>
        </div>
    `;
    
    // Hiển thị metadata
    displayDicomInfo(data.metadata);
}

// Hiển thị metadata
function displayDicomInfo(metadata) {
    const metaContainer = document.getElementById('dicomMetadata');
    metaContainer.innerHTML = `
        <p><strong>Tên Bệnh Nhân:</strong> ${metadata.patient_name}</p>
        <p><strong>ID Bệnh Nhân:</strong> ${metadata.patient_id}</p>
        <p><strong>Ngày Chụp:</strong> ${metadata.study_date}</p>
        <p><strong>Loại Hình Ảnh:</strong> ${metadata.modality}</p>
    `;
}

// Xử lý upload DICOM
document.getElementById('dicomInput').addEventListener('change', async function(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Hiển thị trạng thái loading
    document.getElementById('dicomViewer').innerHTML = '<p>Đang tải ảnh...</p>';
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

        // Hiển thị ảnh gốc
        displayOriginalImage(data.original, data.width, data.height);
        
        // Hiển thị kết quả AI
        displayAIResults(data);
        
    } catch (error) {
        console.error('Lỗi:', error);
        document.getElementById('dicomViewer').innerHTML = 
            `<p style="color:red">Lỗi: ${error.message}</p>`;
    }
});

// Các hàm vẽ/tẩy (giữ nguyên)
function toggleDrawMode() {
    isDrawing = !isDrawing;
    document.getElementById('drawButton').classList.toggle('active', isDrawing);
    
    if (isDrawing) {
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 5;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.globalCompositeOperation = 'source-over';
    }
}

function startDrawing(e) {
    if (!isDrawing) return;
    ctx.beginPath();
    ctx.moveTo(e.offsetX, e.offsetY);
}

function draw(e) {
    if (!isDrawing) return;
    ctx.lineTo(e.offsetX, e.offsetY);
    ctx.stroke();
}

function stopDrawing() {
    ctx.closePath();
}

// Các công cụ xem ảnh (giữ nguyên)
function adjustBrightness(value) {
    const element = document.getElementById('dicomViewer');
    if (!currentImage || !viewport) return;
    
    viewport.voi.windowCenter += value;
    cornerstone.setViewport(element, viewport);
    cornerstone.updateImage(element);
}

function zoomImage(value) {
    const element = document.getElementById('dicomViewer');
    if (!currentImage || !viewport) return;
    
    viewport.scale += value;
    cornerstone.setViewport(element, viewport);
    cornerstone.updateImage(element);
}

function rotateImage() {
    const element = document.getElementById('dicomViewer');
    if (!currentImage || !viewport) return;
    
    viewport.rotation += 90;
    cornerstone.setViewport(element, viewport);
    cornerstone.updateImage(element);
}

function saveSegmentation() {
    const element = document.getElementById('dicomViewer');
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = canvas.width;
    tempCanvas.height = canvas.height;
    
    const tempCtx = tempCanvas.getContext('2d');
    
    // Vẽ ảnh DICOM
    const dicomImage = document.querySelector('#dicomViewer canvas');
    tempCtx.drawImage(dicomImage, 0, 0);
    
    // Vẽ overlay
    tempCtx.drawImage(canvas, 0, 0);
    
    // Tạo link download
    const link = document.createElement('a');
    link.download = `dicom_result_${Date.now()}.png`;
    link.href = tempCanvas.toDataURL('image/png');
    link.click();
}

// Khởi tạo Cornerstone
cornerstone.enable(document.getElementById('dicomViewer'));