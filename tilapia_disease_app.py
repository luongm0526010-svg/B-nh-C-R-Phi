import base64
import io
import requests
import streamlit as st
from PIL import Image, ImageDraw

# 1. CẤU HÌNH THÔNG TIN MÔ HÌNH NHẬN DIỆN BỆNH CÁ RÔ PHI (TILAPIA SKIN DISEASE)
ROBOFLOW_API_KEY = "ZgSNc4xdkTcvj8g4NG1x"  # Khóa API cá nhân của bạn
WORKSPACE_NAME = "luong-ngoc"
MODEL_ID = "tilapia-skine-disease-e2qh3"  # ID mô hình từ Roboflow
VERSION = "1"  # Phiên bản mô hình

# Đường dẫn URL API để gọi mô hình nhận diện bệnh cá (Lọc lấy độ tự tin từ 20% trở lên)
URL = f"https://detect.roboflow.com/{MODEL_ID}/{VERSION}?api_key={ROBOFLOW_API_KEY}&confidence=20"

# 2. GIAO DIỆN TRANG WEB STREAMLIT
st.set_page_config(
    page_title="Hệ thống Chẩn đoán Sức khỏe Cá Rô Phi",
    page_icon="🐟",
    layout="centered",
)

# Thanh tiêu đề chính và mô tả ngắn gọn
st.title("🐟 Ứng Dụng AI Phát Hiện Bệnh Trên Da Cá Rô Phi")
st.write(
    "Hệ thống thị giác máy tính hỗ trợ người nuôi thủy sản quét bề mặt, "
    "phát hiện sớm các dấu hiệu tổn thương, loét da hoặc xuất huyết trên cá rô phi."
)

st.divider()

# Khung chức năng tải hình ảnh cá lên
uploaded_file = st.file_uploader(
    "Tải lên hình ảnh cá rô phi cần kiểm tra bệnh lý...",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is not None:
    # Mở và chuẩn hóa định dạng ảnh đầu vào sang RGB
    image = Image.open(uploaded_file).convert("RGB")
    st.image(
        image,
        caption="Hình ảnh cá rô phi mẫu đang được xử lý",
        use_container_width=True,
    )

    # Nút bấm kích hoạt quét
    if st.button("Kích hoạt quét bề mặt da cá", type="primary"):
        with st.spinner(
            "Hệ thống trí tuệ nhân tạo đang phân tích vùng bệnh..."
        ):
            try:
                # Chuyển đổi ảnh sang dạng nhị phân (bytes)
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format="JPEG")
                img_bytes = img_byte_arr.getvalue()

                # Mã hóa Base64 gửi qua API
                image_base64 = base64.b64encode(img_bytes).decode("utf-8")

                # Gửi request tới Roboflow API
                response = requests.post(
                    URL,
                    data=image_base64,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                )
                response.raise_for_status()

                result = response.json()

                if "error" in result:
                    st.error(result["error"])
                    st.stop()

                st.divider()
                st.subheader("📊 Báo cáo kiểm định lâm sàng:")

                predictions = result.get("predictions", [])

                # Lọc riêng danh sách vết bệnh (loại bỏ nhãn cá khỏe nếu mô hình nhận diện được)
                disease_predictions = [
                    p
                    for p in predictions
                    if p.get("class", "").lower()
                    not in ["healthy-fish", "healthy", "ka_khoe"]
                ]

                # ========================================================
                # TRƯỜNG HỢP 1: PHÁT HIỆN VẾT BỆNH -> KHOANH MÀU ĐỎ CẢNH BÁO
                # ========================================================
                if len(disease_predictions) > 0:
                    st.error(
                        f"🚨 CẢNH BÁO: Phát hiện {len(disease_predictions)} vị trí xuất hiện tổn thương hoặc nốt loét bệnh trên da cá!"
                    )

                    annotated_image = image.copy()
                    draw = ImageDraw.Draw(annotated_image)

                    for box in disease_predictions:
                        x_center = box.get("x")
                        y_center = box.get("y")
                        width = box.get("width")
                        height = box.get("height")
                        confidence = box.get("confidence", 0) * 100
                        class_name = box.get("class", "TonThuong")

                        left = x_center - (width / 2)
                        top = y_center - (height / 2)
                        right = x_center + (width / 2)
                        bottom = y_center + (height / 2)

                        border_color = "#E60000"  # Viền Đỏ

                        draw.rectangle(
                            [left, top, right, bottom],
                            outline=border_color,
                            width=4,
                        )

                        label_text = f"Bệnh: {class_name} ({confidence:.1f}%)"
                        draw.text(
                            (left + 5, top + 5), label_text, fill=border_color
                        )

                    st.image(
                        annotated_image,
                        caption="Bản đồ định vị tổn thương: Các ô ĐỎ thể hiện vết bệnh đã phát hiện",
                        use_container_width=True,
                    )
                    st.warning(
                        "💡 Khuyến nghị kỹ thuật: Đàn cá có tỷ lệ nhiễm khuẩn hoặc xuất huyết cao. Cần lập tức cách ly các cá thể bệnh và khử trùng môi trường nước nuôi."
                    )

                # ========================================================
                # TRƯỜNG HỢP 2: KHÔNG CÓ VẾT BỆNH -> CÁ KHỎE MANH (THÔNG BÁO XANH)
                # ========================================================
                else:
                    st.success(
                        "🎉 KẾT QUẢ TỐT: Bề mặt da mịn màng, cá khỏe mạnh và không phát hiện bất kỳ dấu hiệu bệnh lý nguy hiểm nào."
                    )
                    st.image(
                        image,
                        caption="Cá khỏe mạnh bình thường, không phát hiện vết thương hở",
                        use_container_width=True,
                    )

            except Exception as error_msg:
                st.error(
                    f"Lỗi hệ thống trong quá trình kết nối API hoặc dựng ảnh đồ họa: {error_msg}"
                )

            except Exception as error_msg:
                st.error(f"Lỗi hệ thống: {error_msg}")
