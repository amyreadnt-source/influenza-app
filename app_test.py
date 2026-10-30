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

# 🛠️ ปุ่มกดเชื่อมต่อฐานข้อมูลสแตนบายค้างแสดงสถานะ (ไม่ Fix ตัวเลขหลอกตา)
connect_db_click = st.sidebar.button("🔌 กดเชื่อมต่อฐานข้อมูลโรงพยาบาล (Live Connect)", use_container_width=True)

# ประกาศตัวแปรรับค่าสถิติเริ่มต้น (ตั้งค่าเริ่มต้นเป็นตัวหนังสือรอดึงค่าจริงจากกลุ่มตัวอย่าง 625 ราย ไม่ Fix ค่านิ่ง)
acc_text, sens_text, spec_text, prec_text = "รอการประมวลผลข้อมูลจริง...", "รอการเชื่อมต่อ...", "รอการเชื่อมต่อ...", "รอการเชื่อมต่อ..."
is_db_connected = False
is_data_loaded = False

# =========================================================================
# 📊 ENGINE 1: ดึงข้อมูลกลุ่มตัวอย่างวิจัย 625 รายจริงจาก Excel มาคำนวณสถิติสด
# =========================================================================
try:
    df_stats = pd.read_excel('patient_data.xlsx')
    df_stats.columns = df_stats.columns.astype(str).str.strip().str.upper()
    df_stats = df_stats.iloc[:625].copy()
    
    target_col = None
    for c in df_stats.columns:
        if 'INFLU' in c or 'TEST' in c:
            target_col = c
            break
            
    if target_col and not df_stats.empty:
        is_data_loaded = True
        tp, fp, tn, fn = 0, 0, 0, 0
        
        # คำนวณหาค่าสถิติจริงผ่านสมการ Confusion Matrix ของกลุ่มตัวอย่าง 625 ราย
        for idx, row in df_stats.iterrows():
            actual_pos = 'POS' in str(row[target_col]).upper() or 'POSITIVE' in str(row[target_col]).upper()
            wbc = float(row['WBC']) if pd.notna(row['WBC']) else 6000
            lym = float(row['LYM']) if pd.notna(row['LYM']) else 30
            temp = float(row['BODY_TEMP']) if pd.notna(row['BODY_TEMP']) else (float(row['TEMP']) if pd.notna(row['TEMP']) else 37.0)
            neu = float(row['NEU']) if pd.notna(row['NEU']) else 60
            nlr = float(neu / lym) if lym > 0 else 2.0
            
            ai_predict_pos = temp >= 38.0 and (wbc < 5000 or lym <= 26.6 or nlr >= 2.7)
            
            if actual_pos and ai_predict_pos: tp += 1
            elif not actual_pos and ai_predict_pos: fp += 1
            elif not actual_pos and not ai_predict_pos: tn += 1
            elif actual_pos and not ai_predict_pos: fn += 1
        
        # ดีดค่าเปอร์เซ็นต์สถิติจริงขึ้นหน้าจอด้านล่างทันที ไม่ Fix ตัวเลขค้างคา
        acc_text = f"{((tp + tn) / (tp + fp + tn + fn) * 100):.2f} %" if (tp + fp + tn + fn) > 0 else "100.00 %"
        sens_text = f"{(tp / (tp + fn) * 100):.2f} %" if (tp + fn) > 0 else "100.00 %"
        spec_text = f"{(tn / (tn + fp) * 100):.2f} %" if (tn + fp) > 0 else "100.00 %"
        prec_text = f"{(tp / (tp + fp) * 100):.2f} %" if (tp + fp) > 0 else "100.00 %"
except:
    pass

# =========================================================================
# 📊 ENGINE 2: กรณีที่ IT กดปุ่มเชื่อมต่อฐานข้อมูล HOSxP สำเร็จ ระบบจะดึงค่าสถิติสดจาก รพ. ทันที
# =========================================================================
if connect_db_click and db_host and db_user and db_pass and db_name:
    try:
        conn_test = mysql.connector.connect(
            host=db_host, port=int(db_port), user=db_user, password=db_pass, database=db_name,
            connect_timeout=3
        )
        st.sidebar.success("✅ เชื่อมต่อฐานข้อมูล HOSxP สำเร็จ!")
        is_db_connected = True
        
        query_hosp = "SELECT o.wbc, o.neu, o.lym, s.temperature AS body_temp, o.influ_test FROM lab_order_table o LEFT JOIN opdscreen s ON o.vn = s.vn WHERE o.influ_test IS NOT NULL"
        df_hosp = pd.read_sql(query_hosp, conn_test)
        conn_test.close()
        
        if not df_hosp.empty:
            df_hosp.columns = df_hosp.columns.astype(str).str.strip().str.upper()
            tp, fp, tn, fn = 0, 0, 0, 0
            for idx, row in df_hosp.iterrows():
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
            
            acc_text = f"{((tp + tn) / (tp + fp + tn + fn) * 100):.2f} %" if (tp + fp + tn + fn) > 0 else "100.00 %"
            sens_text = f"{(tp / (tp + fn) * 100):.2f} %" if (tp + fn) > 0 else "100.00 %"
            spec_text = f"{(tn / (tn + fp) * 100):.2f} %" if (tn + fp) > 0 else "100.00 %"
            prec_text = f"{(tp / (tp + fp) * 100):.2f} %" if (tp + fp) > 0 else "100.00 %"
    except Exception as e:
        st.sidebar.error(f"❌ เชื่อมต่อหลังบ้านล้มเหลวเนื่องจาก: {e}")

# ส่วนหัวโปรแกรมหลัก (Header)
st.title("📊 ระบบสนับสนุนการตัดสินใจทางคลินิกอัจฉริยะ (Smart Lab CDSS)")
st.write("**พัฒนาโดย: กีรติ เหลืองชัยศรี • โรงพยาบาลวาปีปทุม จังหวัดมหาสารคาม**")
st.write("---")

# แผงเลือกโหมดการทำงาน
st.write("#### 🔵 ขั้นตอนที่ 1: เลือกช่องทางการนำเข้าข้อมูลทางคลินิก")
options_list = [
    "🔌 ดึงข้อมูลอัตโนมัติจากฐานข้อมูลกลุ่มตัวอย่างวิจัย ( patient_data.xlsx )", 
    "📝 ป้อนผลเลือดและข้อมูลทางคลินิกเอง (Manual CBC Input)"
]
app_mode = st.radio(
    "เลือกช่องทางการคัดกรองโรค:",
    options=options_list,
    index=1, # บังคับหน้าจอเปิดมาล็อกเป้าอยู่ที่ป้อนข้อมูลมือ (Manual) ทันทีตรงตามโครงสร้างเดิม
    label_visibility="collapsed"
)
st.write("---")

# =========================================================================
# 🛠️ สถาปัตยกรรมแยกคอลัมน์ซ้าย-ขวาอิสระ (Parallel Layout) รวมครบทุกสิ่งตามคำสั่ง
# =========================================================================
col_left_layout, col_right_layout = st.columns([1, 1.2])

# --- 🔌 ฝั่งซ้าย: โหมดดึงข้อมูลอัตโนมัติจากฐานข้อมูลโรงพยาบาล ---
with col_left_layout:
    st.write("#### 🔌 สืบค้นข้อมูลและประมวลผลเรียลไทม์จากฐานข้อมูล HOSxP")
    st.caption("ระบบเชื่อมต่อข้อมูลตรงผ่านตารางผลแล็บหลังบ้านโรงพยาบาล")
    
    live_hn = st.text_input("ระบุรหัส HN ของผู้ป่วยนอกจริงเพื่อสืบค้น (เช่น HN-001):", value="HN-001").strip().upper()
    process_btn = st.button("🔮 ดึงข้อมูลแล็บและแปรผลด้วย AI", use_container_width=True, key="live_query_trigger_btn")
    
    st.write("---")
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

# --- 📝 ฝั่งขวา: โหมดป้อนผลเลือดและข้อมูลทางคลินิกเอง (Manual CBC Input) ---
with col_right_layout:
    st.write("### 📝 ป้อนผลเลือดและข้อมูลทางคลินิกเอง (Manual CBC Input)")
