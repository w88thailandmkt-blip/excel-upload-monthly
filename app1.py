import streamlit as st
import pandas as pd
import msoffcrypto
import io
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime 

# --- ฟังก์ชันตรวจสอบรหัสผ่านเข้าเว็บ ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔑 กรุณาใส่รหัสผ่านเพื่อเข้าใช้งาน", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("🔑 กรุณาใส่รหัสผ่านเพื่อเข้าใช้งาน", type="password", on_change=password_entered, key="password")
        st.error("❌ รหัสผ่านไม่ถูกต้อง")
        return False
    return True

# --- เริ่มต้นหน้าเว็บ ---
st.title("ระบบอัพโหลดข้อมูลอัตโนมัติ (รายเดือน) 🚀")

if check_password():
    # 1. เปลี่ยนจากปฏิทินเป็น Dropdown เลือกเดือน
    month_options = [
        "Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026", 
        "May 2026", "Jun 2026", "Jul 2026", "Aug 2026", 
        "Sep 2026", "Oct 2026", "Nov 2026", "Dec 2026"
    ]
    selected_month = st.selectbox("📅 เลือกเดือนของข้อมูล (Month of Data)", month_options)

    # 2. ช่องกรอกชื่อผู้อัพโหลด
    uploader_name = st.text_input("👤 ชื่อผู้อัพโหลด (เช่น: แอดมิน A)")
    
    uploaded_file = st.file_uploader("เลือกไฟล์ Excel ของคุณ", type=["xlsx"])

    if uploaded_file is not None:
        # บังคับให้ต้องกรอกชื่อก่อน ถึงจะกดอัพโหลดได้
        if not uploader_name:
            st.warning("⚠️ กรุณากรอกชื่อผู้อัพโหลดก่อนกดประมวลผล")
        else:
            if st.button("ประมวลผลและส่งขึ้น Sheet"):
                try:
                    # ปลดล็อครหัสผ่าน Excel
                    decrypted_file = io.BytesIO()
                    office_file = msoffcrypto.OfficeFile(uploaded_file)
                    office_file.load_key(password="12345")
                    office_file.decrypt(decrypted_file)

                    # อ่านข้อมูล
                    df = pd.read_excel(decrypted_file)
                    df_filtered = df[['Date', 'Affiliate ID', 'No Of Click', 'NewSignUp', 'FTD']].copy()
                    df_filtered['Date'] = df_filtered['Date'].astype(str)
                    
                    # 3. นำเดือนที่เลือกมาใส่เป็นคอลัมน์ใหม่
                    df_filtered['Month of Data'] = selected_month
                    df_filtered['Uploader'] = uploader_name
                    df_filtered['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # เชื่อมต่อ Google Sheets
                    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
                    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
                    client = gspread.authorize(creds)
                    
                    # ระบุ Sheet ปลายทาง
                    sheet = client.open_by_key("1fIU5UJ7AI3k4Csxa_HJ_fj3vP6uiL48E23eOB08CrvU").worksheet("Raw Data M")
                    sheet.append_rows(df_filtered.values.tolist())
                    
                    st.success(f"อัพเดทข้อมูลประจำเดือน {selected_month} สำเร็จ! (โดย: {uploader_name}) 🎉")

                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")
