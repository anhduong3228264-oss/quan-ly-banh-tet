import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CẤU HÌNH & BẢNG ĐỊNH MỨC THỜI GIAN (Bạn sửa số phút ở đây)
st.set_page_config(page_title="Quản Lý Sản Xuất Bánh", layout="wide")

# Đây là nơi bạn quy định 1 cái bánh làm mất bao nhiêu phút
# Lưu ý: Tên trong này phải khớp với cách ghép "Loại bánh" + " " + "Loại nhân"
DINH_MUC_THOI_GIAN = {
    'Chưng Mặn': 60,  # 60 phút/cái
    'Chưng Chay': 50,
    'Tét Mặn': 45,
    'Tét Chay': 40,
    'Chưng Ngọt': 55, # Ví dụ thêm
    # Thêm các loại khác vào đây...
}

st.title("🏭 Hệ Thống Tối Ưu Sản Xuất Bánh Tét/Chưng")

# 2. LOAD DỮ LIỆU TỪ GOOGLE SHEET CỦA BẠN
# Link CSV Google Sheet (Hãy thay link của bạn vào đây)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-...../pub?output=csv" 

@st.cache_data(ttl=60)
def load_and_process_data(url):
    try:
        # Đọc dữ liệu
        df_raw = pd.read_csv(url)
        
        # BƯỚC XỬ LÝ 1: Lọc bỏ đơn đã xong
        # Chỉ lấy những dòng KHÔNG PHẢI là "Đã xong!"
        df_working = df_raw[df_raw['Trang_thai'] != 'Đã xong!'].copy()
        
        # BƯỚC XỬ LÝ 2: Tạo tên sản phẩm đầy đủ
        # Ghép cột "Loai_banh" và "Loại nhân"
        df_working['Ten_SP_Full'] = df_working['Loai_banh'] + " " + df_working['Loại nhân']
        
        # BƯỚC XỬ LÝ 3: Gom nhóm (Group by)
        # Cộng tổng số lượng theo từng loại bánh
        df_final = df_working.groupby('Ten_SP_Full')['So_luong'].sum().reset_index()
        df_final.columns = ['Sản phẩm', 'SL hiện tại'] # Đổi tên cho đẹp
        
        # BƯỚC XỬ LÝ 4: Ghép với định mức thời gian
        # Tạo cột TG sản xuất dựa vào từ điển DINH_MUC_THOI_GIAN khai báo ở đầu
        df_final['TG sản xuất'] = df_final['Sản phẩm'].map(DINH_MUC_THOI_GIAN)
        
        # Nếu có loại bánh mới chưa khai báo thời gian, mặc định là 60 phút
        df_final['TG sản xuất'] = df_final['TG sản xuất'].fillna(60)
        
        return df_final
        
    except Exception as e:
        st.error(f"Lỗi đọc dữ liệu: {e}")
        return pd.DataFrame()

# 3. GIAO DIỆN & TÍNH TOÁN
st.sidebar.header("⚙️ Năng lực xưởng")
so_nguoi = st.sidebar.number_input("Số nhân công gói bánh", value=0)
gio_lam = st.sidebar.number_input("Giờ làm/ngày", value=0)
ngay_con_lai = st.sidebar.number_input("Số ngày đến hạn giao", value=0)

tong_nang_luc = so_nguoi * gio_lam * ngay_con_lai * 60 # Đổi ra phút
st.sidebar.info(f"Tổng quỹ thời gian: **{tong_nang_luc:,.0f}** phút")

# Tải dữ liệu
df = load_and_process_data("https://docs.google.com/spreadsheets/d/e/2PACX-1vSnGZeeW-FDnPbJA3QVmydsIbYSzHfqtgOcjbG60KzxU3EfqHJNTM5jkzyTIhWEqE-jaXPLQWQHnAuJ/pub?gid=1716572663&single=true&output=csv")

if not df.empty:
    # --- PHẦN MÔ PHỎNG ĐƠN MỚI ---
    st.subheader("1. Mô phỏng nhận đơn hàng mới")
    col_input1, col_input2, col_input3 = st.columns(3)
    
    # Lấy danh sách loại bánh có trong định mức để chọn
    ds_banh = list(DINH_MUC_THOI_GIAN.keys())
    loai_sp_moi = col_input1.selectbox("Loại bánh khách đặt", ds_banh)
    so_luong_moi = col_input2.number_input("Số lượng", value=0, min_value=0)
    
    # Tính toán mô phỏng
    df['SL dự kiến'] = df['SL hiện tại']
    
    # Kiểm tra xem bánh mới có trong danh sách hiện tại chưa
    if loai_sp_moi in df['Sản phẩm'].values:
        idx = df[df['Sản phẩm'] == loai_sp_moi].index[0]
        df.at[idx, 'SL dự kiến'] += so_luong_moi
    else:
        # Nếu là bánh mới tinh chưa có đơn nào, thêm dòng mới
        new_row = pd.DataFrame({
            'Sản phẩm': [loai_sp_moi], 
            'SL hiện tại': [0],
            'SL dự kiến': [so_luong_moi],
            'TG sản xuất': [DINH_MUC_THOI_GIAN.get(loai_sp_moi, 60)]
        })
        df = pd.concat([df, new_row], ignore_index=True)

    # Tính tổng thời gian cần
    df['Tổng thời gian'] = df['TG sản xuất'] * df['SL dự kiến']
    tong_thoi_gian_can = df['Tổng thời gian'].sum()
    
    ty_le_tai = (tong_thoi_gian_can / tong_nang_luc) * 100 if tong_nang_luc > 0 else 0

    # --- HIỂN THỊ KẾT QUẢ ---
    st.divider()
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("Kết quả phân tích")
        st.metric("Tổng phút cần làm", f"{tong_thoi_gian_can:,.0f}")
        st.metric("Công suất sử dụng", f"{ty_le_tai:.1f}%", delta_color="inverse")
        
        if ty_le_tai <= 100:
            st.success("✅ ĐỦ SỨC NHẬN ĐƠN")
        else:
            st.error(f"❌ QUÁ TẢI: Cần thêm {(tong_thoi_gian_can - tong_nang_luc)/60:.1f} giờ làm việc.")

    with c2:
        st.subheader("Biểu đồ tải trọng sản xuất")
        fig = px.bar(df, x='Sản phẩm', y='Tổng thời gian', 
                     text='SL dự kiến',
                     title="Thời gian (phút) dành cho từng loại bánh",
                     color='Sản phẩm')
        st.plotly_chart(fig, use_container_width=True)
        
    # Xem chi tiết dữ liệu
    with st.expander("Xem bảng dữ liệu chi tiết"):
        st.dataframe(df)

else:

    st.warning("Chưa tải được dữ liệu. Vui lòng kiểm tra lại Link Google Sheet.")

