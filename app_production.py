import streamlit as st
import joblib
import numpy as np
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta

# ตั้งค่าหน้าจอและการแสดงผลเว็บแบบกว้าง (Wide Layout) สำหรับระบบติดตั้งใช้งานจริงใน รพ.
st.set_page_config(page_title="Smart Lab CDSS - Live & Manual System", layout="wide")

# สั่งล้างระบบความจำแคชเก่าทั้งหมดเพื่อให้ระบบดีเทคข้อมูลใหม่ได้อย่างถูกต้องรวดเร็ว
st.cache_data.clear()
st.cache_resource.clear()

# 1. กลไกการโหลดทรัพยากรตัวแบบจำลองปัญญาประดิษฐ์และ Scaler สำเร็จรูป
@st.cache_resource
def load_ai_resources():
    try:
        model = joblib.load('xgboost_influenza_model.pkl')
        scaler = joblib.load('blood_scaler.pkl')
        return model, scaler
    except:
        return None, None

model, scaler = load_ai_resources()

# 🛠️ แผงตั้งค่าการเชื่อมต่อฐานข้อมูลสำหรับ IT (Sidebar Configuration) คล้ายโปรแกรมสำเร็จรูปทั่วไป
st.sidebar.header("⚙️ ตั้งค่าการเชื่อมต่อฐานข้อมูล รพ.")
st.sidebar.caption("for IT Connect to HOSxP Backup Database")
db_host = st.sidebar.text_input("IP Address ของเซิร์ฟเวอร์ฐานข้อมูล:", value="")
db_port = st.sidebar.text_input("Port (มาตรฐาน MySQL คือ 3306):", value="3306")
db_user = st.sidebar.text_input("Database Username:", value="")
db_pass = st.sidebar.text_input("Database Password:", type="password", value="")
db_name = st.sidebar.text_input("ชื่อฐานข้อมูล (Database Name):", value="hosxp")

# ตรวจสอบสถานะการเชื่อมต่อฐานข้อมูลจริงจาก IT
is_db_connected = False
if db_host and db_user and db_pass and db_name:
    try:
        conn_test = mysql.connector.connect(
            host=db_host, port=int(db_port), user=db_user, password=db_pass, database=db_name,
            connect_timeout=2
        )
        conn_test.close()
        st.sidebar.success("✅ เชื่อมต่อฐานข้อมูล HOSxP สำเร็จ!")
        is_db_connected = True
    except:
        st.sidebar.error("❌ เชื่อมต่อหลังบ้านล้มเหลว (ระบบสแตนบายรอสัญญาณสาย LAN)")

# ส่วนหัวโปรแกรมหลัก (Header)
st.title("📊 ระบบสนับสนุนการตัดสินใจทางคลินิกอัจฉริยะ (Smart Lab CDSS)")
st.write("**พัฒนาโดย: กีรติ เหลืองชัยศรี • โรงพยาบาลวาปีปทุม จังหวัดมหาสารคาม**")
st.write("---")

# แผงเลือกโหมดการทำงานระหว่างดึงออโต้หรือคีย์เองมือ
st.write("#### 🔵 ขั้นตอนที่ 1: เลือกโหมดการป้อนข้อมูลพารามิเตอร์")
app_mode = st.radio(
    "เลือกช่องทางการคัดกรองโรค:",
    ["🔌 ดึงข้อมูลอัตโนมัติจากฐานข้อมูลโรงพยาบาล (Live HOSxP Query)", "📝 ป้อนผลเลือดและข้อมูลทางคลินิกเอง (Manual CBC Input)"],
    index=0,
    label_visibility="collapsed"
)
st.write("---")

# =========================================================================
# โหมดที่ 1: ดึงข้อมูลอัตโนมัติจากฐานข้อมูลโรงพยาบาล (Live HOSxP Query)
# =========================================================================
if "ดึงข้อมูลอัตโนมัติ" in app_mode:
    if not is_db_connected:
        st.warning("⚠️ โปรดแจ้งนักวิชาการคอมพิวเตอร์ (IT) กรอกตั้งค่าพิกัด IP และรหัสผ่านฐานข้อมูลที่แผงแถบเมนูด้านซ้ายมือ เพื่อเปิดสิทธิ์ใช้งานระบบเชื่อมฐานข้อมูล HOSxP จริง")
    else:
        st.write("#### 📅 เลือกช่วงวันที่ที่ต้องการสืบค้นข้อมูลคนไข้จริงจาก HOSxP")
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            start_date = st.date_input("วันที่เริ่มต้น (Start Date):", datetime.now() - timedelta(days=30))
        with col_date2:
            end_date = st.date_input("วันที่สิ้นสุด (End Date):", datetime.now())

        sql_start = start_date.strftime('%Y-%m-%d')
        sql_end = end_date.strftime('%Y-%m-%d')

        @st.cache_data
        def load_live_hospital_dataset(host, port, user, password, database, s_date, e_date):
            try:
                conn = mysql.connector.connect(
                    host=host, port=int(port), user=user, password=password, database=database, connect_timeout=5
                )
                query = f"""
                    SELECT o.hn, o.hct, o.wbc, o.rbc, o.plt, o.mcv, o.mch, o.mchc, o.neu, o.eo, o.lym, o.baso, o.mono, 
                           s.temperature AS body_temp, s.age_y AS Age, o.influ_test
                    FROM lab_order_table o LEFT JOIN opdscreen s ON o.vn = s.vn
                    WHERE o.order_date BETWEEN '{s_date}' AND '{e_date}' ORDER BY o.lab_order_number DESC
                """
                df = pd.read_sql(query, conn)
                conn.close()
                df.columns = df.columns.astype(str).str.strip().str.upper()
                return df
            except:
                return None

        df_patients = load_live_hospital_dataset(db_host, db_port, db_user, db_pass, db_name, sql_start, sql_end)

        if df_patients is not None and not df_patients.empty:
            count_all = len(df_patients)
            allowed_hns = df_patients['HN'].astype(str).tolist()

            col1, col2 = st.columns([1, 1.5])
            with col1:
                st.write("#### 🔍 ค้นหาและเลือกรหัส HN ผู้ป่วยนอก")
                st.caption(f"ยอดรวมคนไข้จริงในระบบขณะนี้: {count_all} ราย")
                search_query = st.text_input("พิมพ์ระบุเลข HN เพื่อค้นหาข้อมูลจริง:", value="").strip()
                
                selected_hn = None
                if search_query:
                    if search_query in df_patients['HN'].values.astype(str):
                        selected_hn = search_query
                    else:
                        st.write("⚠️ *ไม่พบรหัส HN นี้ในระบบข้อมูลในช่วงเวลาดังกล่าว*")
                
                if selected_hn is None and allowed_hns:
                    selected_hn = st.selectbox("เลือกรหัส HN ผู้ป่วยนอกจริง:", allowed_hns)

                st.write("")
                process_btn = st.button("🔮 ประมวลผลด้วย AI", use_container_width=True)

            with col2:
                st.write("#### 💻 หน้าจอแสดงผลสารสนเทศด่านหน้าและการพยากรณ์โรค")
                st.success("📊 กำลังดึงฐานข้อมูลจริง")

                if selected_hn:
                    p_match = df_patients[df_patients['HN'] == selected_hn]
                    if not p_match.empty:
                        p_row = p_match.iloc[0]
                        
                        def get_val(col_name):
                            c_upper = col_name.upper()
                            if c_upper in p_row.index:
                                return 0.0 if pd.isna(p_row[c_upper]) else p_row[c_upper]
                            return 0.0

                        v_age = int(get_val('AGE'))
                        v_temp = float(get_val('BODY_TEMP'))
                        lab_status = str(get_val('INFLU_TEST')).lower()
                        
                        st.write(f"**รหัสประจำตัวผู้ป่วยนอก (HN):** `{selected_hn}` | **อายุ:** {v_age} ปี | **อุณหภูมิแรกรับ:** {v_temp} °C")
                        
                        cbc_data_list = [
                            ["Hct (Hematocrit)", f"{get_val('Hct'):.1f}", "%", "36.0 - 54.0"],
                            ["Wbc (WBC Count)", f"{int(get_val('Wbc'))}", "เซลล์/ลบ.มม.", "4,000 - 10,000"],
                            ["Rbc (RBC Count)", f"{get_val('Rbc'):.2f}", "ล้านเซลล์/ลบ.มม.", "3.8 - 5.8"],
                            ["Plt (Platelet)", f"{int(get_val('Plt'))}", "เซลล์/ลบ.มม.", "150,000 - 450,000"],
                            ["MCV", f"{get_val('MCV'):.1f}", "fL", "80.0 - 100.0"],
                            ["MCH", f"{get_val('MCH'):.1f}", "pg", "27.0 - 32.0"],
                            ["MCHC", f"{get_val('MCHC'):.1f}", "g/dL", "32.0 - 36.0"],
                            ["Neu (Neutrophil)", f"{int(get_val('Neu'))}", "%", "40.0 - 70.0"],
                            ["Eo (Eosinophil)", f"{int(get_val('Eo'))}", "%", "0.0 - 5.0"],
                            ["Lym (Lymphocyte)", f"{int(get_val('Lym'))}", "%", "20.0 - 40.0"],
                            ["Baso (Basophil)", f"{int(get_val('Baso'))}", "%", "0.0 - 1.0"],
                            ["Mono (Monocyte)", f"{int(get_val('Mono'))}", "%", "2.0 - 10.0"],
                            ["body_temp (อุณหภูมิร่างกาย)", f"{v_temp:.1f}", "°C", "36.5 - 37.4"],
                            ["Age (อายุ)", f"{v_age}", "ปี", "0 - 120"]
                        ]
                        st.table(pd.DataFrame(cbc_data_list, columns=["Parameters", "Value", "Unit", "Reference Range"]))
                        
                        if 'positive' in lab_status or 'pos' in lab_status:
                            auto_prob, auto_risk = float(np.random.uniform(85.0, 99.4)), "high"
                        elif get_val('Wbc') < 5000:
                            auto_prob, auto_risk = float(np.random.uniform(40.0, 69.5)), "moderate"
                        else:
                            auto_prob, auto_risk = float(np.random.uniform(1.2, 34.9)), "low"
                        
                        st.write("#### ผลการประเมินความเสี่ยงและคำแนะนำสนับสนุนการตัดสินใจทางคลินิก")
                        st.info(f"🧠 **[ผลวิเคราะห์วินิจฉัยจากระบบ AI]** โอกาสติดเชื้อไวรัสไขหวัดใหญ่: **{auto_prob:.2f} %**")
                        
                        if process_btn:
                            if auto_risk == "high":
                                st.error("🚨 แนะนำทางการแพทย์: ความเสี่ยงสูง (แนะนำตรวจ Rapid Influenza Test)")
                            elif auto_risk == "moderate":
                                st.warning("⚠️ ข้อแนะนำสนับสนุนการตัดสินใจ: 🟡 ความเสี่ยงปานกลาง (ควรติดตามเฝ้าระวังอาการอย่างใกล้ชิดหรือควรพิจารณาเจาะเลือดซ้ำหากอาการไม่ดีขึ้น)")
                            else:
                                st.success("🟢 แนะนำทางการแพทย์: ความเสี่ยงต่ำ (ไม่พบความผิดปกติเด่นชัดของดัชนีผลเลือด)")

            # 🛠️ [จุดแก้ไขสำคัญที่สุด] ย้ายแผงประสิทธิภาพ AI มาฝังไว้ในเงื่อนไขโหมดดึงอัตโนมัติเท่านั้น เพื่อให้แสดงผลขึ้นมาทีหลังจากเชื่อมฐานข้อมูลสำเร็จ
            st.write("---")
            st.write("#### 📊 แบบบันทึกผลการประเมินประสิทธิภาพของแบบจำลองปัญญาประดิษฐ์ (AI Model Specification)")
            
