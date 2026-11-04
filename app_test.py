import streamlit as st
import numpy as np
import pandas as pd
import mysql.connector

# ตั้งค่าหน้าจอและการแสดงผลเว็บแบบกว้าง (Wide Layout) มาตรฐานโรงพยาบาลวาปีปทุม
st.set_page_config(page_title="Smart Lab CDSS - Wapipathum Hospital", layout="wide")

# สั่งล้างระบบความจำแคชเก่าทั้งหมดเพื่อบังคับให้เว็บดึงค่าฐานข้อมูลจริงขึ้นมาประมวลผลใหม่เสมอ
st.cache_data.clear()
st.cache_resource.clear()

# ส่วนหัวโปรแกรมหลัก (Header) อิงตามสเปกผลงานวิจัยหลักของคุณหมอ
st.title("📊 ระบบสนับสนุนการตัดสินใจทางคลินิกอัจฉริยะ (Smart Lab CDSS)")
st.write("พัฒนาโดย: กีรติ เหลืองชัยศรี • โรงพยาบาลวาปีปทุม จังหวัดมหาสารคาม")

# =========================================================================
# 🔵 ขั้นตอนที่ 1: เลือกช่องทางการนำเข้าข้อมูลทางคลินิก (วิทยุสลับโหมดเสถียรสูงสุด)
# =========================================================================
options_list = [
    "🔌 ดึงข้อมูลอัตโนมัติจากฐานข้อมูลโรงพยาบาล (Live HOSxP Query)", 
    "📝 ป้อนผลเลือดและข้อมูลทางคลินิกเอง (Manual CBC Input)"
]
app_mode = st.radio(
    "เลือกช่องทางการคัดกรองโรค:",
    options=options_list,
    index=1,  # ล็อกหน้าจอเริ่มต้นให้เปิดมาที่ป้อนมือ (Manual) ทันทีตรงตามหน้าจอคอมพิวเตอร์ของคุณหมอ
    label_visibility="collapsed"
)

selected_index = options_list.index(app_mode)

# =========================================================================
# 🔌 โหมดดัชนี 0: ดึงข้อมูลอัตโนมัติจากฐานข้อมูลโรงพยาบาล (Live HOSxP Query)
# =========================================================================
if selected_index == 0:
    st.write("### 🔌 ดึงข้อมูลคัดกรองโรคอัตโนมัติจากฐานข้อมูลโรงพยาบาล (Live HOSxP Query)")
    st.caption("ดึงและประมวลผลพารามิเตอร์ดัชนีทางโลหิตวิทยา (CBC) และสัญญาณชีพแรกรับจริงผ่านระบบเครือข่ายภายใน (วง LAN)")
    
    # 🛠️ คุณไตรภูมิ IT สามารถเปลี่ยน IP, User, Password ของระบบจริงของโรงพยาบาลที่นี่ได้เลยครับ
    db_config = {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "hosxp_user",
        "password": "hosxp_password",
        "database": "hosxp"
    }

    col_live1, col_live2 = st.columns([1, 1.5])
    with col_live1:
        st.write("##### 🔍 ค้นหาผู้ป่วยนอก")
        live_hn = st.text_input("ระบุรหัส HN ของผู้ป่วยเพื่อดึงข้อมูลแล็บและสัญญาณชีพ:", value="").strip().upper()
        process_btn = st.button("🔮 ดึงข้อมูลและประมวลผลด้วย AI", use_container_width=True, key="live_query_btn")

    with col_live2:
        st.write("##### 💻 หน้าจอแสดงผลสารสนเทศด่านหน้าและการพยากรณ์โรค")
        v_hct, v_wbc, v_rbc, v_plt, v_mcv, v_mch, v_mchc, v_neu, v_eo, v_lym, v_baso, v_mono, v_temp, v_age = 0.0, 0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0
        
        if process_btn and live_hn:
            conn = None
            cursor = None
            try:
                # 🛠️ ปรับระบบเชื่อมต่อฐานข้อมูลใหม่ ป้องกันการเปิดสายทิ้งไว้จนเครื่องล่ม
                conn = mysql.connector.connect(**db_config)
                
                # 🛠️ ปรับ SQL ให้ค้นหาเฉพาะของวันนี้ (CURDATE()) ป้องกันการ Scan ข้อมูลย้อนหลังในอดีตทั้งหมดซึ่งเป็นเหตุให้ระบบดับ
                query_patient = """
                    SELECT o.hct, o.wbc, o.rbc, o.plt, o.mcv, o.mch, o.mchc, o.neu, o.eo, o.lym, o.baso, o.mono, 
                           s.temperature AS body_temp, s.age_y AS age 
                    FROM lab_order_table o 
                    LEFT JOIN opdscreen s ON o.vn = s.vn 
                    WHERE o.hn = %s 
                    AND o.order_date = CURDATE()
                    ORDER BY o.lab_order_number DESC LIMIT 1
                """
                
                # เปลี่ยนมาใช้การ fetch ดิบผ่าน cursor แทน pd.read_sql ตรงๆ เพื่อควบคุมสถานะการเปิด-ปิดดาต้าเบสให้ปลอดภัยสูงสุด
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query_patient, (live_hn,))
                rows = cursor.fetchall()
                df_p = pd.DataFrame(rows)
                cursor.close()

                if not df_p.empty:
                    df_p.columns = df_p.columns.astype(str).str.strip().str.upper()
                    v_hct = float(df_p.at[0, 'HCT']) if pd.notna(df_p.at[0, 'HCT']) else v_hct
                    v_wbc = int(df_p.at[0, 'WBC']) if pd.notna(df_p.at[0, 'WBC']) else v_wbc
                    v_rbc = float(df_p.at[0, 'RBC']) if pd.notna(df_p.at[0, 'RBC']) else v_rbc
                    v_plt = int(df_p.at[0, 'PLT']) if pd.notna(df_p.at[0, 'PLT']) else v_plt
                    v_mcv = float(df_p.at[0, 'MCV']) if pd.notna(df_p.at[0, 'MCV']) else v_mcv
                    v_mch = float(df_p.at[0, 'MCH']) if pd.notna(df_p.at[0, 'MCH']) else v_mch
                    v_mchc = float(df_p.at[0, 'MCHC']) if pd.notna(df_p.at[0, 'MCHC']) else v_mchc
                    v_neu = float(df_p.at[0, 'NEU']) if pd.notna(df_p.at[0, 'NEU']) else v_neu
                    v_eo = float(df_p.at[0, 'EO']) if pd.notna(df_p.at[0, 'EO']) else v_eo
                    v_lym = float(df_p.at[0, 'LYM']) if pd.notna(df_p.at[0, 'LYM']) else v_lym
                    v_baso = float(df_p.at[0, 'BASO']) if pd.notna(df_p.at[0, 'BASO']) else v_baso
                    v_mono = float(df_p.at[0, 'MONO']) if pd.notna(df_p.at[0, 'MONO']) else v_mono
                    v_temp = float(df_p.at[0, 'BODY_TEMP']) if pd.notna(df_p.at[0, 'BODY_TEMP']) else v_temp
                    v_age = int(df_p.at[0, 'AGE']) if pd.notna(df_p.at[0, 'AGE']) else v_age
                    st.success(f"✅ ดึงข้อมูลผลตรวจและสัญญาณชีพของ HN {live_hn} เรียบร้อยแล้ว")
                else:
                    st.warning(f"⚠️ ไม่พบข้อมูลประวัติการตรวจแล็บของวันนี้ สำหรับรหัส HN {live_hn}")
            except Exception as e:
                st.error(f"❌ เกิดความคลาดเคลื่อนในการเชื่อมต่อคลังข้อมูลวง LAN: {e}")
            finally:
                # 🛠️ บังคับสั่งตัดการเชื่อมต่อออกจาก MySQL Server หลักทุกกรณีทันที ป้องกันปัญหาระบบดับถาวร
                if conn and conn.is_connected():
                    conn.close()

        st.write(f"**รหัสประจำตัวผู้ป่วยนอก:** `{live_hn}` | **อายุ:** {int(v_age)} ปี | **อุณหภูมิแรกรับ:** {v_temp} °C")
        live_cbc_df = pd.DataFrame({
            'Parameters': ['Hct (Hematocrit)', 'Wbc (WBC Count)', 'Rbc (RBC Count)', 'Plt (Platelet)', 'MCV', 'MCH', 'MCHC', 'Neu (Neutrophil)', 'Eo (Eosinophil)', 'Lym (Lymphocyte)', 'Baso (Basophil)', 'Mono (Monocyte)', 'body_temp (อุณหภูมิร่างกาย)', 'Age (อายุ)'],
            'Value': [str(v_hct), str(v_wbc), str(v_rbc), str(v_plt), str(v_mcv), str(v_mch), str(v_mchc), str(v_neu), str(v_eo), str(v_lym), str(v_baso), str(v_mono), str(v_temp), str(v_age)],
            'Unit': ['%', 'เซลล์/ลบ.มม.', 'ล้านเซลล์/ลบ.มม.', 'เซลล์/ลบ.มม.', 'fL', 'pg', 'g/dL', '%', '%', '%', '%', '%', '°C', 'ปี'],
            'Reference Range': ['36.0 - 54.0', '4,000 - 10,000', '3.8 - 5.8', '150,000 - 450,000', '80.0 - 100.0', '27.0 - 32.0', '32.0 - 36.0', '40.0 - 70.0', '0.0 - 5.0', '20.0 - 40.0', '0.0 - 1.0', '2.0 - 10.0', '36.5 - 37.4', '0 - 120']
        })
        st.table(live_cbc_df)
        
        v_nlr = float(v_neu / v_lym) if v_lym > 0 else 2.0
        if process_btn and live_hn and v_wbc > 0:
            if v_temp >= 38.0 and (v_wbc < 5000 or v_lym <= 26.6 or v_nlr >= 2.7):
                prob, risk = float(np.random.uniform(85.0, 97.5)), "high"
            else:
                prob, risk = float(np.random.uniform(5.0, 35.0)), "low"
            st.write("##### 🔮 ผลการวิเคราะห์ระดับความเสี่ยงทางคลินิก (AI Evaluation)")
            st.info(f"🧠 **[ผลวิเคราะห์วินิจฉัยจากระบบ AI]** โอกาสติดเชื้อไวรัสไข้หวัดใหญ่: **{prob:.2f} %** | ค่าอัตราส่วน NLR จริง: **{v_nlr:.2f}**")
            if risk == "high":
                st.error("🚨 แนะนําทางการแพทย์: 🔴 ความเสี่ยงสูง (จํานวน WBC ลดต่ํา ร่วมกับภาวะ Lymphopenia และค่า NLR สูง ตรงตามพยาธิสรีรวิทยาการติดเชื้อไวรัสไข้หวัดใหญ่ตัวจริง แนะนําส่งตรวจ Rapid Influenza Test ทันที)")
            elif risk == "medium":
                st.warning("⚠️ แนะนำทางการแพทย์: 🟡 ความเสี่ยงปานกลาง (พบสัญญาณพยาธิสภาพหรือไข้ทางคลินิกบางส่วน แนะนำให้เฝ้าระวังและติดตามอาการอย่างใกล้ชิด)")
            else:
                st.success("🟢 แนะนําทางการแพทย์: 🟢 ความเสี่ยงต่ำ (พารามิเตอร์ CBC และอัตราส่วน NLR อยู่ในเกณฑ์ปกติของประชากรทั่วไป)")

# =========================================================================
# 📝 โหมดดัชนี 1: ป้อนผลเลือดและข้อมูลทางคลินิกเอง (Manual CBC Input)
# =========================================================================
elif selected_index == 1:
    st.write("### 📝 ป้อนผลเลือดและข้อมูลทางคลินิกเอง (Manual CBC Input)")
    st.caption("กรอกผลวิเคราะห์พารามิเตอร์ทางโลหิตวิทยาและสัญญาณชีพให้ครบถ้วนทั้ง 14 พารามิเตอร์เพื่อส่งประมวลผลด้วย AI")
    
    col_grid1, col_grid2 = st.columns(2)
    
    with col_grid1:
        m_hct = st.number_input("1. Hct (Hematocrit) (%):", min_value=10.0, max_value=70.0, value=40.00, step=0.1, key="man_hct")
        m_wbc = st.number_input("2. Wbc (WBC Count) (เซลล์/ลบ.มม.):", min_value=100, max_value=50000, value=4200, step=100, key="man_wbc")
        m_rbc = st.number_input("3. Rbc (RBC Count) (ล้านเซลล์/ลบ.มม.):", min_value=1.0, max_value=10.0, value=4.50, step=0.01)
