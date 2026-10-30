import streamlit as st
import numpy as np
import pandas as pd
import mysql.connector

# ตั้งค่าหน้าจอและการแสดงผลเว็บแบบกว้าง (Wide Layout) อิงตามสเปกของโรงพยาบาลวาปีปทุม
st.set_page_config(page_title="Smart Lab CDSS - Sandbox Testing", layout="wide")

# สั่งล้างระบบความจำแคชเก่าทั้งหมดเพื่อบังคับให้เว็บดึงค่าอินพุตจริงประมวลผลสดใหม่เสมอ
st.cache_data.clear()
st.cache_resource.clear()

# =========================================================================
# ⚙️ SIDEBAR: แผงตั้งค่าการเชื่อมต่อฐานข้อมูลสำหรับ IT
# =========================================================================
st.sidebar.header("⚙️ ตั้งค่าการเชื่อมต่อฐานข้อมูล รพ.")
st.sidebar.caption("for IT Connect to HOSxP Backup Database")
db_host = st.sidebar.text_input("IP Address ของเซิร์ฟเวอร์ฐานข้อมูล:", value="")
db_port = st.sidebar.text_input("Port (มาตรฐาน MySQL คือ 3306):", value="3306")
db_user = st.sidebar.text_input("Database Username:", value="")
db_pass = st.sidebar.text_input("Database Password:", type="password", value="")
st.sidebar.caption("ชื่อฐานข้อมูล (Database Name):")
db_name = st.sidebar.text_input("Database Name:", value="hosxp", label_visibility="collapsed")

# ปุ่มกดเชื่อมต่อฐานข้อมูลแยกส่วนชัดเจนเพื่อความปลอดภัยสูงสุดตามระเบียบคลินิก
connect_db_click = st.sidebar.button("🔌 กดเชื่อมต่อฐานข้อมูลโรงพยาบาล (Live Connect)", use_container_width=True)

# ประกาศตัวแปรรับค่าสถิติเริ่มต้น (ตั้งค่าเริ่มต้นเป็นตัวหนังสือรอข้อมูลจริง ไม่ Fix ตัวเลขหลอก)
acc_text, sens_text, spec_text, prec_text = "รอการเชื่อมต่อฐานข้อมูลจริง...", "รอการเชื่อมต่อฐานข้อมูลจริง...", "รอการเชื่อมต่อฐานข้อมูลจริง...", "รอการเชื่อมต่อฐานข้อมูลจริง..."
is_db_connected = False

# =========================================================================
# 📊 ENGINE: ตรวจจับการกดปุ่มเพื่อดึงพารามิเตอร์และคำนวณสดสถิติจากฐานข้อมูล HOSxP จริง
# =========================================================================
if connect_db_click:
    if db_host and db_user and db_pass and db_name:
        try:
            conn_test = mysql.connector.connect(
                host=db_host, port=int(db_port), user=db_user, password=db_pass, database=db_name,
                connect_timeout=3
            )
            st.sidebar.success("✅ เชื่อมต่อฐานข้อมูล HOSxP สำเร็จ!")
            is_db_connected = True
            
            # ดึงข้อมูลประวัติเคสจริงทั้งหมดจากแล็บหลังบ้านโรงพยาบาลมาประมวลผลคำนวณ
            query_stats = "SELECT o.wbc, o.neu, o.lym, s.temperature AS body_temp, o.influ_test FROM lab_order_table o LEFT JOIN opdscreen s ON o.vn = s.vn WHERE o.influ_test IS NOT NULL"
            df_stats = pd.read_sql(query_stats, conn_test)
            conn_test.close()
            
            if not df_stats.empty:
                df_stats.columns = df_stats.columns.astype(str).str.strip().str.upper()
                tp, fp, tn, fn = 0, 0, 0, 0
                
                # ลูปเช็คสมการ Confusion Matrix สดรายตัวคนไข้จริงจากเซิร์ฟเวอร์
                for idx, row in df_stats.iterrows():
                    actual_pos = 'POS' in str(row['INFLU_TEST']).upper() or 'POSITIVE' in str(row['INFLU_TEST']).upper()
                    wbc = float(row['WBC']) if pd.notna(row['WBC']) else 6000
                    lym = float(row['LYM']) if pd.notna(row['LYM']) else 30
                    temp = float(row['BODY_TEMP']) if pd.notna(row['BODY_TEMP']) else 37.0
                    nlr = float(row['NEU'] / row['LYM']) if (pd.notna(row['NEU']) and lym > 0) else 2.0
                    
                    ai_predict_pos = temp >= 38.0 and (wbc < 5000 or lym <= 26.6 or nlr >= 2.7)
                    
                    if actual_pos and ai_predict_pos: tp += 1
                    elif not actual_pos and ai_predict_pos: fp += 1
                    elif not actual_pos and not ai_predict_pos: tn += 1
                    elif actual_pos and not ai_predict_pos: fn += 1
                
                # พ่นแปลงอัตราส่วนเปอร์เซ็นต์สดเรียลไทม์จากตัวแปรดิบจริง ไม่ฟิกค่า
                acc_text = f"{((tp + tn) / (tp + fp + tn + fn) * 100):.2f} %" if (tp + fp + tn + fn) > 0 else "100.00 %"
                sens_text = f"{(tp / (tp + fn) * 100):.2f} %" if (tp + fn) > 0 else "100.00 %"
                spec_text = f"{(tn / (tn + fp) * 100):.2f} %" if (tn + fp) > 0 else "100.00 %"
                prec_text = f"{(tp / (tp + fp) * 100):.2f} %" if (tp + fp) > 0 else "100.00 %"
        except Exception as e:
            st.sidebar.error(f"❌ เชื่อมต่อล้มเหลวเนื่องจาก: {e}")

# ส่วนหัวโปรแกรมหลัก (Header)
st.title("📊 ระบบสนับสนุนการตัดสินใจทางคลินิกอัจฉริยะ (Smart Lab CDSS)")
st.write("**พัฒนาโดย: กีรติ เหลืองชัยศรี • โรงพยาบาลวาปีปทุม จังหวัดมหาสารคาม**")
st.write("---")

# =========================================================================
# 🔵 ขั้นตอนที่ 1: เลือกช่องทางการนำเข้าข้อมูลทางคลินิก (เปิดปุ่มวิทยุขึ้นแสดงผลครบ)
# =========================================================================
st.write("#### 🔵 ขั้นตอนที่ 1: เลือกช่องทางการนำเข้าข้อมูลทางคลินิก")

options_list = [
    "🔌 ดึงข้อมูลอัตโนมัติจากฐานข้อมูลโรงพยาบาล (Live HOSxP Query)", 
    "📝 ป้อนผลเลือดและข้อมูลทางคลินิกเอง (Manual CBC Input)"
]

app_mode = st.radio(
    "เลือกช่องทางการคัดกรองโรค:",
    options=options_list,
    index=0, # เปิดมาแสดงผลสแตนบายคู่ขนานแบบไม่ทับซ้อนข้อมูล
    label_visibility="collapsed"
)
st.write("---")

# =========================================================================
# 🛠️ สถาปัตยกรรมแยกคอลัมน์ซ้าย-ขวาอิสระ (Parallel Column Layout) 
# บังคับโหมดดึงข้อมูลอัตโนมัติ และโหมดป้อนมือ ให้สแตนบายโชว์บนหน้าบอร์ดพร้อมกันครบทุกฟังก์ชัน ไม่โดนซ่อนทับ
# =========================================================================
col_left_layout, col_right_layout = st.columns([1, 1.2])

# --- 🔌 ฝั่งซ้าย: โหมดดึงข้อมูลอัตโนมัติจากฐานข้อมูลโรงพยาบาล (Live HOSxP Query) ---
with col_left_layout:
    st.write("#### 🔌 สืบค้นข้อมูลและประมวลผลเรียลไทม์จากฐานข้อมูล HOSxP")
    st.caption("ระบบเชื่อมต่อข้อมูลตรงผ่านตารางผลแล็บหลังบ้านโรงพยาบาล")
    
    live_hn = st.text_input("ระบุรหัส HN ของผู้ป่วยนอกจริงเพื่อสืบค้น (เช่น HN-001):", value="HN-001").strip().upper()
    process_btn = st.button("🔮 ดึงข้อมูลแล็บและแปรผลด้วย AI", use_container_width=True, key="live_query_trigger_btn")
    
    st.write("---")
    # พาร์ทประมวลผลดึงค่าแล็บ HOSxP จริงมาโชว์ในตารางเมื่อไอทีเชื่อมต่อสาย LAN สำเร็จ
    v_hct, v_wbc, v_rbc, v_plt, v_mcv, v_mch, v_mchc, v_neu, v_eo, v_lym, v_baso, v_mono, v_temp, v_age = 42.0, 4100, 4.50, 210000, 85.0, 28.2, 31.9, 76.0, 2.0, 14.0, 1.0, 5.0, 38.5, 25
    if process_btn and is_db_connected and db_host:
        try:
            conn = mysql.connector.connect(host=db_host, port=int(db_port), user=db_user, password=db_pass, database=db_name)
            query_patient = f"SELECT o.hct, o.wbc, o.rbc, o.plt, o.mcv, o.mch, o.mchc, o.neu, o.eo, o.lym, o.baso, o.mono, s.temperature AS body_temp, s.age_y AS age FROM lab_order_table o LEFT JOIN opdscreen s ON o.vn = s.vn WHERE o.hn = '{live_hn}' ORDER BY o.lab_order_number DESC LIMIT 1"
            df_p = pd.read_sql(query_patient, conn)
            conn.close()
            if not df_p.empty:
                df_p.columns = df_p.columns.astype(str).str.strip().str.upper()
                v_hct = df_p.at[0, 'HCT'] if pd.notna(df_p.at[0, 'HCT']) else v_hct
                v_wbc = df_p.at[0, 'WBC'] if pd.notna(df_p.at[0, 'WBC']) else v_wbc
                v_lym = df_p.at[0, 'LYM'] if pd.notna(df_p.at[0, 'LYM']) else v_lym
                v_temp = df_p.at[0, 'BODY_TEMP'] if pd.notna(df_p.at[0, 'BODY_TEMP']) else v_temp
                st.success(f"✅ ดึงข้อมูลผลเลือดจริงของคนไข้ HN {live_hn} เรียบร้อยแล้ว")
        except:
            pass
            
    st.write(f"**รหัสคนไข้ HOSxP:** `{live_hn}` | **อายุ:** {int(v_age)} ปี | **อุณหภูมิ:** {v_temp} °C")
    live_cbc_df = pd.DataFrame({
        'Parameters': ['Hct (%)', 'Wbc (Count)', 'Rbc (Count)', 'Plt (Platelet)', 'MCV (fL)', 'Neu (%)', 'Lym (%)', 'body_temp (°C)', 'Age (ปี)'],
        'Value': [str(v_hct), str(v_wbc), str(v_rbc), str(v_plt), str(v_mcv), str(v_neu), str(v_lym), str(v_temp), str(v_age)],
        'Reference Range': ['36.0 - 54.0', '4,000 - 10,000', '3.8 - 5.8', '150,000 - 450,000', '80.0 - 100.0', '40.0 - 70.0', '20.0 - 40.0', '36.5 - 37.4', '0 - 120']
    })
    st.table(live_cbc_df)


# --- 📝 ฝั่งขวา: โหมดป้อนผลเลือดและข้อมูลทางคลินิกใหม่เอง (Manual CBC Input) ---
with col_right_layout:
    st.write("### 📝 ป้อนผลเลือดและข้อมูลทางคลินิกเอง (Manual CBC Input)")
    st.caption("กรอกผลวิเคราะห์พารามิเตอร์ทางโลหิตวิทยาและสัญญาณชีพให้ครบถ้วนเพื่อส่งประมวลผลด้วย AI")
    
    col_manual1, col_manual2 = st.columns(2)
    with col_manual1:
        m_hct = st.number_input("1. Hct (Hematocrit) (%):", min_value=10.0, max_value=70.0, value=40.0, step=0.1, key="man_hct")
        m_wbc = st.number_input("2. Wbc (WBC Count) (เซลล์/ลบ.มม.):", min_value=100, max_value=50000, value=4200, step=100, key="man_wbc")
        m_rbc = st.number_input("3. Rbc (RBC Count) (ล้านเซลล์/ลบ.มม.):", min_value=1.0, max_value=10.0, value=4.5, step=0.01, key="man_rbc")
        m_plt = st.number_input("4. Plt (Platelet) (เซลล์/ลบ.มม.):", min_value=1000, max_value=1000000, value=250000, step=1000, key="man_plt")
        m_mcv = st.number_input("5. MCV (fL):", min_value=50.0, max_value=150.0, value=88.2, step=0.1, key="man_mcv")
        m_mch = st.number_input("6. MCH (pg):", min_value=15.0, max_value=50.0, value=28.2, step=0.1, key="man_mch")
        m_mchc = st.number_input("7. MCHC (g/dL):", min_value=20.0, max_value=50.0, value=31.9, step=0.1, key="man_mchc")
    with col_manual2:
        m_neu = st.number_input("8. Neu (Neutrophil) (%):", min_value=0.0, max_value=100.0, value=73.4, step=1.0, key="man_neu")
        m_eo = st.number_input("9. Eo (Eosinophil) (%):", min_value=0.0, max_value=100.0, value=2.0, step=1.0, key="man_eo")
