import streamlit as st
import requests
from PIL import Image, ImageDraw
import io
import base64

# 1. CẤU HÌNH THÔNG TIN MÔ HÌNH NHẬN DIỆN BỆNH CÁ RÔ PHI (TILAPIA SKIN DISEASE)
ROBOFLOW_API_KEY = "ZgSNc4xdkTcvj8g4NG1x"  # Khóa API cá nhân của bạn
WORKSPACE_NAME = "lam-thi-ngoc-luong-m0526010"
MODEL_ID = "tilapia-skine-disease-e2qh3"      # ID mô hình mới từ ảnh của bạn
VERSION = "1"                                 # Phiên bản v2 sau khi bạn đã tối ưu hóa học máy

# Đường dẫn URL API để gọi mô hình nhận diện bệnh cá (Lọc lấy độ tự tin cao từ 25% trở lên)
URL = f"https://detect.roboflow.com/{MODEL_ID}/{VERSION}?api_key={ROBOFLOW_API_KEY}&confidence=25"

# 2. GIAO DIỆN TRANG WEB STREAMLIT CẬP NHẬT
st.set_page_config(
    page_title="Hệ thống Chẩn đoán Sức khỏe Cá Rô Phi", 
    page_icon="🐟", 
    layout="centered"
)

# Thanh tiêu đề chính và mô tả ngắn gọn về sản phẩm
st.title("🐟 Ứng Dụng AI Phát Hiện Bệnh Trên Da Cá Rô Phi")
st.write(
    "Hệ thống thị giác máy tính hỗ trợ người nuôi thủy sản quét bề mặt, "
    "phát hiện sớm các dấu hiệu tổn thương, loét da hoặc xuất huyết trên cá rô phi."
)

st.divider()

# Khung chức năng cho phép tải hình ảnh cá lên từ thiết bị
uploaded_file = st.file_uploader(
    "Tải lên hình ảnh cá rô phi cần kiểm tra bệnh lý...", 
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    # Mở và chuẩn hóa định dạng ảnh đầu vào sang RGB
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Hình ảnh cá rô phi mẫu đang được xử lý", use_container_width=True)
    
    # Tạo nút bấm chạy suy luận kiểm tra vết bệnh
    if st.button("Kích hoạt quét bề mặt da cá", type="primary"):
        with st.spinner("Hệ thống trí tuệ nhân tạo đang phân tích vùng bệnh..."):
            try:
                # Chuyển đổi ma trận ảnh sang luồng dữ liệu nhị phân (bytes)
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='JPEG')
                img_bytes = img_byte_arr.getvalue()
                
                # Mã hóa chuỗi Base64 truyền tải an toàn qua môi trường web API
                image_base64 = base64.b64encode(img_bytes).decode('utf-8')
                
                # Thực hiện gửi yêu cầu POST request đến cụm server của Roboflow
                response = requests.post(
                    URL, 
                    data=image_base64, 
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                result = response.json()
                
                st.divider()
                st.subheader("📊 Báo cáo kiểm định lâm sàng:")
                
                # Trích xuất tập hợp các vùng nghi nhiễm bệnh từ JSON trả về
                predictions = result.get("predictions", [])
                
                if len(predictions) > 0:
                    st.error(f"🚨 CẢNH BÁO: Phát hiện {len(predictions)} vị trí xuất hiện tổn thương hoặc nốt loét bệnh trên da cá!")
                    
                    # Chuẩn bị ảnh đích để vẽ bản đồ bounding box
                    annotated_image = image.copy()
                    draw = ImageDraw.Draw(annotated_image)
                    
                    for box in predictions:
                        # Lấy các thông số hình học tâm (x, y) cùng độ rộng/cao từ Roboflow
                        x_center = box.get("x")
                        y_center = box.get("y")
                        width = box.get("width")
                        height = box.get("height")
                        confidence = box.get("confidence", 0) * 100
                        
                        # Quy đổi công thức tọa độ về dạng chuẩn Top-Left và Bottom-Right
                        left = x_center - (width / 2)
                        top = y_center - (height / 2)
                        right = x_center + (width / 2)
                        bottom = y_center + (height / 2)
                        
                        # Sử dụng viền màu đỏ đậm nhằm khoanh vùng cảnh báo khẩn cấp
                        border_color = "#E60000"
                        
                        # Tiến hành vẽ hình chữ nhật bao quanh nốt bệnh (nét vẽ đậm = 4)
                        draw.rectangle([left, top, right, bottom], outline=border_color, width=4)
                        
                        # Thiết lập nhãn tiếng Việt đính kèm mức độ chính xác
                        label_text = f"Vết Nhiễm Bệnh ({confidence:.1f}%)"
                        draw.text((left + 5, top + 5), label_text, fill=border_color)
                    
                    # Trả kết quả ảnh trực quan đã khoanh vùng nốt loét lên ứng dụng web
                    st.image(
                        annotated_image, 
                        caption="Bản đồ định vị tổn thương: Các ô ĐỎ thể hiện vết bệnh đã phát hiện", 
                        use_container_width=True
                    )
                    st.warning("💡 Khuyến nghị kỹ thuật: Đàn cá có tỷ lệ nhiễm khuẩn hoặc xuất huyết cao. Cần lập tức cách ly các cá thể bệnh và khử trùng môi trường nước nuôi.")
                else:
                    st.success("🎉 KẾT QUẢ TỐT: Bề mặt da mịn màng, không phát hiện thấy bất kỳ dấu hiệu bệnh lý nguy hiểm nào.")
                    st.image(image, caption="Cá khỏe mạnh bình thường, không có vết thương hở", use_container_width=True)
                    
            except Exception as error_msg:
                st.error(f"Lỗi hệ thống trong quá trình kết nối API hoặc dựng ảnh đồ họa: {error_msg}")
