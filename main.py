import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64

# --- الإعدادات الرسمية ---
st.set_page_config(page_title="نظام المسار الذكي الرسمي", layout="wide")

DB_FILE = "smart_data.csv"
USERS_FILE = "users_list.csv"

def init_dbs():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([{"user": "admin", "pass": "123", "role": "admin", "active": True}]).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_FILE):
        initial = []
        for sec, count in [("قسم الخروج", 14), ("قسم الدخول", 14), ("قسم صالة القدوم", 8)]:
            for i in range(1, count + 1):
                dtype = "🚛 شحن" if i == 13 and sec != "قسم صالة القدوم" else "⭐ خاص" if i == 14 and sec != "قسم صالة القدوم" else "عادي"
                initial.append({"القسم": sec, "المسار": i, "الحالة": "فارغ", "الموظف": "-", "النوع": dtype, "الوقت": "-", "البلاغ": "سليم"})
        pd.DataFrame(initial).to_csv(DB_FILE, index=False)

init_dbs()

# --- الدخول المضمون ---
if 'auth' not in st.session_state: st.session_state.auth = None

if not st.session_state.auth:
    st.title("🔐 بوابة المسار الذكي - الدخول الرسمي")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        users = pd.read_csv(USERS_FILE)
        match = users[(users['user'] == u) & (users['pass'] == p) & (users['active'] == True)]
        if not match.empty:
            st.session_state.auth = match.iloc[0].to_dict()
            st.rerun()
        else: st.error("بيانات خاطئة أو حساب غير نشط")
else:
    # --- الواجهة الرئيسية ---
    st.sidebar.title(f"المستخدم: {st.session_state.auth['user']}")
    menu = ["العمليات الميدانية", "التقارير والطباعة"]
    if st.session_state.auth['role'] == "admin": menu.append("إدارة المستخدمين")
    choice = st.sidebar.selectbox("القائمة", menu)
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.auth = None
        st.rerun()

    db = pd.read_csv(DB_FILE)

    if choice == "العمليات الميدانية":
        sec = st.radio("القسم:", ["قسم الخروج", "قسم الدخول", "قسم صالة القدوم"], horizontal=True)
        lanes = db[db['القسم'] == sec]
        cols = st.columns(4 if "صالة القدوم" in sec else 7)
        for i, row in lanes.iterrows():
            with cols[i % (4 if "صالة القدوم" in sec else 7)]:
                color = "#28a745" if row["الحالة"] == "مشغول" else "#dc3545" if row["الحالة"] == "عطل" else "#6c757d"
                st.markdown(f"<div style='background-color:{color}; color:white; padding:10px; border-radius:8px; text-align:center;'>{row['النوع']} {row['المسار']}<br>{row['الموظف']}</div>", unsafe_allow_case=True)
                if row["الحالة"] == "فارغ":
                    if st.button("استلام", key=f"in_{i}"):
                        db.at[i, 'الحالة'], db.at[i, 'الموظف'], db.at[i, 'الوقت'] = "مشغول", st.session_state.auth['user'], datetime.now().strftime("%H:%M")
                        db.to_csv(DB_FILE, index=False); st.rerun()
                elif row["الحالة"] == "مشغول":
                    if st.button("🚨 عطل", key=f"err_{i}"):
                        db.at[i, 'الحالة'], db.at[i, 'البلاغ'] = "عطل", "عطل فني ميداني"
                        db.to_csv(DB_FILE, index=False); st.rerun()
                    if st.button("تسليم", key=f"out_{i}"):
                        db.at[i, 'الحالة'], db.at[i, 'الموظف'], db.at[i, 'الوقت'] = "فارغ", "-", "-"
                        db.to_csv(DB_FILE, index=False); st.rerun()

    elif choice == "التقارير والطباعة":
        st.header("📋 التقرير الميداني الرسمي")
        p_sec = st.selectbox("القسم لطباعة الكروكي:", ["قسم الخروج", "قسم الدخول", "قسم صالة القدوم"])
        p_df = db[db['القسم'] == p_sec]
        st.table(p_df[['المسار', 'النوع', 'الحالة', 'الموظف', 'الوقت', 'البلاغ']])
        
        report_html = f"""
        <div style="direction: rtl; font-family: Arial; padding: 20px; border: 2px solid #000;">
            <h2 style="text-align: center;">كروكي {p_sec} الرسمي</h2>
            <p>التاريخ: {datetime.now().strftime('%Y-%m-%d')} | وقت الشفت: {datetime.now().strftime('%H:%M')}</p>
            <table border="1" style="width: 100%; border-collapse: collapse; text-align: center;">
                <tr><th>المسار</th><th>النوع</th><th>الحالة</th><th>الموظف</th><th>الوقت</th></tr>
                {"".join([f"<tr><td>{r['المسار']}</td><td>{r['النوع']}</td><td>{r['الحالة']}</td><td>{r['الموظف']}</td><td>{r['الوقت']}</td></tr>" for _, r in p_df.iterrows()])}
            </table><br>
            <p>توقيع رئيس المناوبة: ........................ | الختم: [ {p_sec} ]</p>
        </div> """
        b64 = base64.b64encode(report_html.encode('utf-8-sig')).decode()
        st.markdown(f'<a href="data:text/html;base64,{b64}" download="Kroki_{p_sec}.pdf" style="padding:15px; background-color:#28a745; color:white; border-radius:8px; text-decoration:none;">💾 تحميل PDF للطباعة</a>', unsafe_allow_case=True)

    elif choice == "إدارة المستخدمين":
        st.header("👥 إدارة الموظفين")
        users = pd.read_csv(USERS_FILE)
        with st.form("إضافة"):
            nu, np, nr = st.text_input("اليوزر"), st.text_input("الباسورد"), st.selectbox("الصلاحية", ["user", "admin"])
            if st.form_submit_button("إضافة موظف"):
                pd.concat([users, pd.DataFrame([{"user": nu, "pass": np, "role": nr, "active": True}])]).to_csv(USERS_FILE, index=False)
                st.rerun()
        st.dataframe(users)
