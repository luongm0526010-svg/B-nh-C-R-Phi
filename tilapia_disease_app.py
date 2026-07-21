import base64
import io
import requests
import streamlit as st
from PIL import Image, ImageDraw

# ==========================================
# 1. CẤU HÌNH THÔNG TIN MÔ HÌNH ROBOFLOW
# ==========================================
ROBOFLOW_API_KEY = "ZgSNc4xdkTcvj8g4NG1x"
WORKSPACE_NAME = "luong-ngoc"
MODEL_ID = "tilapia-skine-disease-e2qh3"
VERSION = "1"

# Đặt confidence=50 trực tiếp ở API URL để đồng bộ hoàn toàn với Roboflow Web
URL = f"https://detect.roboflow.com/{MODEL_ID}/{VERSION}?api_key={ROBOFLOW_API_KEY}&confidence=50"

# ==========================================
# 2. GIAO DIỆN PHẦN MỀM STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Hệ thống Chẩn đoán Sức khỏe Cá Rô Phi",
    page_icon="🐟",
    layout="centered",
)

st.title("🐟 Ứng Dụng AI Phát Hiện Bệnh Trên Da Cá Rô Phi")
st.write(
    "Hệ thống thị giác máy tính hỗ trợ người nuôi thủy sản quét bề mặt, "
    "phát hiện sớm các dấu hiệu tổn thương, loét da hoặc xuất huyết trên cá rô phi."
)

st.divider()

# Tải ảnh từ người dùng
uploaded_file = st.file_uploader(
    "Tải lên hình ảnh cá rô phi cần kiểm tra bệnh lý...",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(
        image,
        caption="Hình ảnh cá rô phi mẫu đang được xử lý",
        use_container_width=True,
    )

    if st.button("Kích hoạt quét bề mặt da cá", type="primary"):
        with st.spinner("Hệ thống trí tuệ nhân tạo đang phân tích..."):
            try:
                # 1. Chuyển ảnh sang dạng Base64 gửi lên API
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format="JPEG")
                img_bytes = img_byte_arr.getvalue()
                image_base64 = base64.b64encode(img_bytes).decode("utf-8")

                # 2. Gọi API Roboflow
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
                    st.error(f"Lỗi API: {result['error']}")
                    st.stop()

                # 3. Xử lý kết quả trả về
                st.divider()
                st.subheader("📊 Báo cáo kiểm định lâm sàng:")

                predictions = result.get("predictions", [])

                # Lọc kết quả có độ tin cậy >= 50%
                valid_predictions = [
                    p for p in predictions if p.get("confidence", 0) >= 0.5
                ]

                if len(valid_predictions) > 0:
                    annotated_image = image.copy()
                    draw = ImageDraw.Draw(annotated_image)
                    has_disease = False

                    for box in valid_predictions:
                        class_name = box.get("class", "Unknown")
                        confidence = box.get("confidence", 0) * 100

                        # Tính toán tọa độ Bounding Box
                        x_center, y_center = box.get("x"), box.get("y")
                        w, h = box.get("width"), box.get("height")
                        left = x_center - (w / 2)
                        top = y_center - (h / 2)
                        right = x_center + (w / 2)
                        bottom = y_center + (h / 2)

                        # Tự động chọn Màu và Nhãn theo Class thực tế
                        if class_name.lower() in [
                            "healthy-fish",
                            "healthy",
                            "ka_khoe",
                        ]:
                            border_color = "#00FF00"  # Xanh lá cho cá khỏe
                            label_text = f"Cá Khỏe Mạnh ({confidence:.1f}%)"
                        else:
                            border_color = "#FF0000"  # Đỏ cho cá bệnh
                            label_text = (
                                f"Bệnh: {class_name} ({confidence:.1f}%)"
                            )
                            has_disease = True

                        # Vẽ khung và nhãn tên class
                        draw.rectangle(
                            [left, top, right, bottom],
                            outline=border_color,
                            width=4,
                        )
                        draw.text(
                            (left + 5, top + 5), label_text, fill=border_color
                        )

                    # Đưa ra thông báo phù hợp thực tế
                    if has_disease:
                        st.error(
                            "🚨 CẢNH BÁO: Phát hiện dấu hiệu tổn thương hoặc nốt loét bệnh trên da cá!"
                        )
                        st.warning(
                            "💡 Khuyến nghị kỹ thuật: Cần lập tức cách ly các cá thể bệnh và khử trùng môi trường nước."
                        )
                    else:
                        st.success(
                            "🎉 KẾT QUẢ TỐT: Cá khỏe mạnh, không phát hiện thấy bất kỳ dấu hiệu bệnh lý nguy hiểm nào."
                        )

                    st.image(
                        annotated_image,
                        caption="Kết quả phân tích từ AI",
                        use_container_width=True,
                    )

                else:
                    st.info(
                        "ℹ️ Không phát hiện đối tượng nào với độ tin cậy > 50%."
                    )

            except Exception as error_msg:
                st.error(f"Lỗi hệ thống: {error_msg}")

            except Exception as error_msg:
                st.error(f"Lỗi hệ thống: {error_msg}")
