import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CẤU HÌNH & ĐỊNH MỨC (Bạn cài đặt các thông số chuẩn ở đây) ---
st.set_page_config(page_title="Bánh Tết Bính Ngọ", layout="wide")
st.title("Hệ Thống Mô Phỏng")

# ĐỊNH MỨC CHUẨN (Bạn tự cài đặt tại đây để máy tính toán mốc so sánh)
# Thời gian lý thuyết để làm 1 cái bánh (phút)
DINH_MUC_CHUAN = {
    'Chưng Mặn': 2.2,  
    'Chưng Chay': 2,
    'Tét Mặn': 3,
    'Tét Chay': 2.8,
    # Thêm các loại khác nếu cần...
}

# --- 2. THUẬT TOÁN ĐÁNH GIÁ (Logic của bạn) ---
def thuat_toan_moi(tg_tb_input, tg_tb_chuan, tong_tg_input, tong_tg_chuan, gio_noi_dung, gio_noi_co):
    # KPI1: So sánh Thời gian trung bình thực tế vs Chuẩn
    if tg_tb_input > tg_tb_chuan:
        kpi1_tang = ((tg_tb_input - tg_tb_chuan) / tg_tb_chuan) * 100
    else:
        kpi1_tang = 0
    
    # KPI2: So sánh Tổng thời gian thực tế vs Tổng giờ sẵn có (Capacity)
    # Lưu ý: Logic này dựa trên file Thuat_toan.py bạn cung cấp
    if tong_tg_input < tong_tg_chuan:
        kpi2_tang = ((tong_tg_chuan - tong_tg_input) / tong_tg_chuan) * 100
    else:
        kpi2_tang = 0
        
    # KPI3: Tỷ lệ sử dụng nồi (Giờ dùng / Giờ có)
    if gio_noi_dung < gio_noi_co:
        kpi3_ty_le = (gio_noi_dung / gio_noi_co) * 100
    else:
        kpi3_ty_le = 100

    # Logic xét duyệt
    ket_luan = "ĐƯỢC"
    mau_sac = "success"

    # Ưu tiên kiểm tra QUÁ TẢI
    if ((kpi1_tang >= 15) and (kpi2_tang >= 25)) or (kpi3_ty_le >= 90):
        ket_luan = "QUÁ TẢI!!!"
        mau_sac = "error"
    # Kiểm tra CẦN THEO DÕI
    elif ((kpi1_tang >= 10) and (kpi2_tang >= 20)) or (kpi3_ty_le >= 80):
        ket_luan = "CẦN THEO DÕI"
        mau_sac = "warning"
        
    return ket_luan, mau_sac, kpi1_tang, kpi2_tang, kpi3_ty_le

# --- 3. HÀM TẢI DỮ LIỆU ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        df = pd.read_csv(url)
        if 'Trang_thai' in df.columns:
            df = df[df['Trang_thai'] != 'Đã xong!'].copy()
        
        # Ghép tên bánh
        if 'Loai_banh' in df.columns and 'Loại nhân' in df.columns:
            df['Ten_SP_Full'] = df['Loai_banh'] + " " + df['Loại nhân']
        
        # Gom nhóm
        df_final = df.groupby('Ten_SP_Full')['So_luong'].sum().reset_index()
        df_final.columns = ['Sản phẩm', 'SL hiện tại']
        
        # Lấy định mức chuẩn để tính toán ngầm
        df_final['TG Chuẩn/Cái'] = df_final['Sản phẩm'].map(DINH_MUC_CHUAN).fillna(60)
        
        return df_final
    except:
        return pd.DataFrame()

# --- 4. GIAO DIỆN CHÍNH ---

# Tải dữ liệu từ Google Sheet
my_link = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSnGZeeW-FDnPbJA3QVmydsIbYSzHfqtgOcjbG60KzxU3EfqHJNTM5jkzyTIhWEqE-jaXPLQWQHnAuJ/pub?gid=1716572663&single=true&output=csv"
df = load_data(my_link)

if not df.empty:
    st.subheader("Thông tin đơn hàng")
    
    # Cho phép nhập đơn mới giả lập
    c1, c2 = st.columns(2)
    sp_moi = c1.selectbox("Chọn sản phẩm nhận thêm", list(DINH_MUC_CHUAN.keys()))
    sl_moi = c2.number_input("Số lượng nhận thêm", value=0, min_value=0)
    
    # Cập nhật số liệu tính toán
    df['SL dự kiến'] = df['SL hiện tại']
    if sp_moi in df['Sản phẩm'].values:
        idx = df[df['Sản phẩm'] == sp_moi].index[0]
        df.at[idx, 'SL dự kiến'] += sl_moi
    else:
        new_row = pd.DataFrame({'Sản phẩm': [sp_moi], 'SL hiện tại': [0], 'SL dự kiến': [sl_moi], 'TG Chuẩn/Cái': [DINH_MUC_CHUAN.get(sp_moi, 60)]})
        df = pd.concat([df, new_row], ignore_index=True)
        
    # Tính toán con số CHUẨN (Lý thuyết) để làm mốc so sánh
    df['Tổng TG Chuẩn'] = df['SL dự kiến'] * df['TG Chuẩn/Cái']
    tong_tg_ly_thuyet = df['Tổng TG Chuẩn'].sum() # Tổng phút theo định mức
    tong_sl_banh = df['SL dự kiến'].sum()
    
    # Tính TB Chuẩn (Phút/cái)
    tg_tb_chuan_calc = tong_tg_ly_thuyet / tong_sl_banh if tong_sl_banh > 0 else 0

    st.info(f"📊 Tổng số bánh dự kiến: **{tong_sl_banh} cái**. (Định mức chuẩn: {tg_tb_chuan_calc:.1f} phút/cái)")
# --- PHẦN MỚI THÊM: BẢNG DỮ LIỆU ---
    # Dùng expander để có thể ẩn/hiện tùy ý
    with st.expander("📂 Bấm vào đây để xem Bảng dữ liệu chi tiết", expanded=True):
        st.dataframe(df, use_container_width=True)
    # -----------------------------------
    st.divider()
    
    # --- PHẦN NHẬP LIỆU CỦA BẠN ---
    st.subheader("Nhập thông số thực tế để đánh giá")
    st.caption("Hãy nhập các con số thực tế bạn dự tính vào bên dưới:")
    
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        # Input 1: Thời gian trung bình
        input_tg_tb = st.number_input("1. Thời gian trung bình thực tế (phút/cái)", 
                                      value=float(tg_tb_chuan_calc), 
                                      help="Thời gian để hoàn thành 1 chiếc bánh trên thực tế")
        
        # Input 3: Tổng giờ nồi
        input_gio_noi_dung = st.number_input("3. Tổng giờ sử dụng nồi (giờ)", 
                                             value=0,
                                             help="Tổng thời gian cần để nấu hết số bánh")

    with col_input2:
        # Input 2: Tổng thời gian (Input)
        input_tong_tg = st.number_input("2. Tổng thời gian hoàn thành (giờ)", 
                                        value=0, 
                                        help="Thời gian từ lúc bắt đầu gói cho tới lúc giao")
        
        # Input 4: Tổng giờ sẵn có (Capacity)
        input_gio_co = st.number_input("4. Tổng giờ sẵn có (giờ)", 
                                       value=0, 
                                       help="Thời gian từ lúc xét cho tới deadline giao hàng")

    # --- CHẠY THUẬT TOÁN & KẾT QUẢ ---
    # Chuyển đổi đơn vị: Input 2 và 4 bạn nhập Giờ, nhưng thuật toán có thể cần đồng nhất.
    # Trong code này tôi giữ nguyên con số bạn nhập để đưa vào thuật toán.
    
    kq_text, kq_color, k1, k2, k3 = thuat_toan_moi(
        tg_tb_input=input_tg_tb, 
        tg_tb_chuan=tg_tb_chuan_calc,       # So sánh với định mức tính từ Sheet
        tong_tg_input=input_tong_tg,        # Input 2
        tong_tg_chuan=input_gio_co,         # Input 4 (Dùng làm mốc so sánh cho KPI2)
        gio_noi_dung=input_gio_noi_dung,    # Input 3
        gio_noi_co=input_gio_co             # Input 4 (Dùng làm mốc so sánh cho KPI3)
    )

    st.divider()
    
    # Hiển thị kết quả to rõ
    col_res1, col_res2 = st.columns([2, 1])
    with col_res1:
        if kq_color == "error":
            st.error(f"### 🛑 KẾT LUẬN: {kq_text}")
        elif kq_color == "warning":
            st.warning(f"### ⚠️ KẾT LUẬN: {kq_text}")
        else:
            st.success(f"### ✅ KẾT LUẬN: {kq_text}")
            
        st.write("---")
        # Hiển thị chi tiết 3 KPI
        k_c1, k_c2, k_c3 = st.columns(3)
        k_c1.metric("KPI1 (Tốc độ)", f"{k1:.1f}%", help=f"Input: {input_tg_tb} vs Chuẩn: {tg_tb_chuan_calc:.1f}")
        k_c2.metric("KPI2 (Thời gian)", f"{k2:.1f}%", help=f"Input: {input_tong_tg}h vs Sẵn có: {input_gio_co}h")
        k_c3.metric("KPI3 (Nồi)", f"{k3:.1f}%", help=f"Dùng: {input_gio_noi_dung}h / Có: {input_gio_co}h")

    with col_res2:
        # Biểu đồ phân bổ loại bánh
        fig = px.pie(df, values='SL dự kiến', names='Sản phẩm', title='Cơ cấu đơn hàng')
        fig.update_layout(height=250, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Đang tải dữ liệu...")


