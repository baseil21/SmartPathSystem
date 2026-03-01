import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64

# --- إعدادات النظام الرسمية ---
st.set_page_config(page_title="نظام المسار الذكي الرسمي", layout="wide")

# --- إدارة قاعدة البيانات ---
DB_FILE = "smart_path_db.csv"

# وظيفة تهيئة البيانات (تحديد المسارات الخاصة والشحن)
def init_db():
    if not os.path.exists(DB_FILE):
        initial = []
        for sec, count in [("قسم الخروج", 14), ("قسم الدخول", 14), ("قسم صالة القدوم", 8)]:
            for i in range(1, count + 1):
                # تحديد النوع (شحن للمسار 13، خاص للمسار 14، عادي للباقي)
                dtype = "🚛 شحن" if i == 13 and sec != "قسم صالة القدوم" else "⭐ خاص" if i == 14 and sec != "قسم صالة القدوم" else "عادي"
                initial.append({
                    "القسم": sec, "المسار": i, "الحالة": "فارغ", 
                    "الموظف": "-", "النوع": dtype, "وقت_الاستلام": "-", "البلاغات": "سليم"
                })
        pd.DataFrame(initial).to_csv(DB_FILE, index=False)

init_db()

# --- واجهة الدخول المضمونة ---
if 'auth' not in st.session_state: st.session_state.auth = None

if not st.session_state.auth:
    st.title("🔐 بوابة نظام المسار الذكي - الدخول الرسمي")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        # بيانات دخول ثابتة ومضمونة لتجاوز خطأ "الحساب غير نشط"
        valid_users = {"admin": "123", "user1": "111", "user2": "222"}
        if u in valid_users and p == valid_users[u]:
            st.session_state.auth = {"user": u, "role": "admin" if u == "admin" else "user"}
            st.rerun()
        else: st.error("بيانات الدخول غير صحيحة")
else:
    # --- القائمة الجانبية ---
    st.sidebar.markdown(f"### المستخدم الحالي: **{st.session_state.auth['user']}**")
    menu = ["العمليات الميدانية", "التقارير والطباعة"]
    if st.session_state.auth['role'] == "admin": menu.append("إدارة النظام")
    choice = st.sidebar.selectbox("الانتقال إلى:", menu)
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.auth = None
        st.rerun()

    db = pd.read_csv(DB_FILE)

    # --- 1. العمليات الميدانية (مع بلاغات الأعطال) ---
    if choice == "العمليات الميدانية":
        sec = st.radio("القسم الحالي:", ["قسم الخروج", "قسم الدخول", "قسم صالة القدوم"], horizontal=True)
        lanes = db[db['القسم'] == sec]
        cols = st.columns(4 if "صالة القدوم" in sec else 7)
        
        for i, row in lanes.iterrows():
            with cols[i % (4 if "صالة القدوم" in sec else 7)]:
                # تحديد اللون (أخضر للمشغول، أحمر للعطل، رمادي للفارغ)
                color = "#28a745" if row["الحالة"] == "مشغول" else "#dc3545" if row["الحالة"] == "عطل" else "#6c757d"
                st.markdown(f"<div style='background-color:{color}; color:white; padding:10px; border-radius:8px; text-align:center; min-height:80px;'><b>{row['النوع']} {row['المسار']}</b><br>{row['الموظف']}</div>", unsafe_allow_case=True)
                
                if row["الحالة"] == "فارغ":
                    if st.button("استلام", key=f"in_{i}"):
                        db.at[i, 'الحالة'] = "مشغول"
                        db.at[i, 'الموظف'] = st.session_state.auth['user']
                        db.at[i, 'وقت_الاستلام'] = datetime.now().strftime("%H:%M")
                        db.to_csv(DB_FILE, index=False); st.rerun()
                elif row["الحالة"] == "مشغول":
                    if st.button("🚨 عطل", key=f"err_{i}"):
                        db.at[i, 'الحالة'] = "عطل"
                        db.at[i, 'البلاغات'] = "عطل فني"
                        db.to_csv(DB_FILE, index=False); st.rerun()
                    if st.button("تسليم", key=f"out_{i}"):
                        db.at[i, 'الحالة'] = "فارغ"
                        db.at[i, 'الموظف'] = "-"
                        db.to_csv(DB_FILE, index=False); st.rerun()
                elif row["الحالة"] == "عطل":
                    if st.button("✅ إصلاح", key=f"fix_{i}"):
                        db.at[i, 'الحالة'] = "فارغ"
                        db.at[i, 'البلاغات'] = "سليم"
                        db.to_csv(DB_FILE, index=False); st.rerun()

    # --- 2. التقارير والطباعة (PDF الرسمي) ---
    elif choice == "التقارير والطباعة":
        st.header("📋 التقرير الميداني الرسمي")
        p_sec = st.selectbox("اختر القسم لطباعة الكروكي:", ["قسم الخروج", "قسم الدخول", "قسم صالة القدوم"])
        p_df = db[db['القسم'] == p_sec]
        st.table(p_df[['المسار', 'النوع', 'الحالة', 'الموظف', 'وقت_الاستلام', 'البلاغات']])
        
        # قالب HTML للطباعة يشمل التواقيع والأختام
        report_html = f"""
        <div style="direction: rtl; font-family: Arial; padding: 25px; border: 3px solid #000; background: white;">
            <h2 style="text-align: center; color: #333;">كروكي {p_sec} الرسمي</h2>
            <p style="text-align: center;">بتاريخ: {datetime.now().strftime('%Y-%m-%d')} | وقت الشفت: {datetime.now().strftime('%H:%M')}</p>
            <table border="1" style="width: 100%; border-collapse: collapse; text-align: center;">
                <tr style="background-color: #f2f2f2;">
                    <th>المسار</th><th>النوع</th><th>الحالة</th><th>الموظف</th><th>وقت الاستلام</th><th>ملاحظات</th>
                </tr>
                {"".join([f"<tr><td>{r['المسار']}</td><td>{r['النوع']}</td><td>{r['الحالة']}</td><td>{r['الموظف']}</td><td>{r['وقت_الاستلام']}</td><td>{r['البلاغات']}</td></tr>" for _, r in p_df.iterrows()])}
            </table>
            <br><br>
            <table style="width: 100%; border: none;">
                <tr>
                    <td style="text-align: right;">توقيع رئيس المناوبة: ........................</td>
                    <td style="text-align: left;">الختم الرسمي للقسم: [ {p_sec} ]</td>
                </tr>
            </table>
        </div>
        """
        b64 = base64.b64encode(report_html.encode('utf-8-sig')).decode()
        st.markdown(f'<a href="data:text/html;base64,{b64}" download="Kroki_{p_sec}.html" style="display: block; width: 250px; text-align: center; padding: 15px; background-color: #28a745; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">💾 تحميل الكروكي الرسمي للطباعة</a>', unsafe_allow_case=True)

    # --- 3. إدارة النظام (تصفير البيانات) ---
    elif choice == "إدارة النظام":
        st.header("⚙️ لوحة التحكم الإدارية")
        if st.button("⚠️ تصفير كافة بيانات المسارات (Reset)"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            init_db(); st.success("تم تصفير المسارات بنجاح"); st.rerun()

