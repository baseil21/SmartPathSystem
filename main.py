import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64

# --- إعدادات النظام الرسمية ---
st.set_page_config(page_title="نظام المسار الذكي الرسمي", layout="wide")

# --- إدارة قواعد البيانات ---
DB_FILE = "smart_path_db.csv"
USERS_FILE = "users_db.csv"

def init_dbs():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([{"user": "admin", "pass": "123", "role": "admin", "active": True}]).to_csv(USERS_FILE, index=False)
    if not os.path.exists(DB_FILE):
        initial = []
        for sec, count in [("قسم الخروج", 14), ("قسم الدخول", 14), ("قسم صالة القدوم", 8)]:
            for i in range(1, count + 1):
                dtype = "🚛 شحن" if i == 13 and sec != "قسم صالة القدوم" else "⭐ خاص" if i == 14 and sec != "قسم صالة القدوم" else "عادي"
                initial.append({"القسم": sec, "المسار": i, "الحالة": "فارغ", "الموظف": "-", "النوع": dtype, "وقت_الاستلام": "-", "البلاغات": "سليم"})
        pd.DataFrame(initial).to_csv(DB_FILE, index=False)

init_dbs()

# وظائف المساعدة
def get_db(file): return pd.read_csv(file)
def save_db(df, file): df.to_csv(file, index=False)

# --- واجهة الدخول ---
if 'auth' not in st.session_state: st.session_state.auth = None

if not st.session_state.auth:
    st.title("🔐 بوابة نظام المسار الذكي - الدخول الرسمي")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        users = get_db(USERS_FILE)
        user_row = users[(users['user'] == u) & (users['pass'] == p) & (users['active'] == True)]
        if not user_row.empty:
            st.session_state.auth = user_row.iloc[0].to_dict()
            st.rerun()
        else: st.error("بيانات غير صحيحة أو الحساب غير نشط")
else:
    # --- القائمة الجانبية ولوحة الإدارة ---
    st.sidebar.title(f"مرحباً: {st.session_state.auth['user']}")
    menu = ["العمليات الميدانية", "التقارير والطباعة"]
    if st.session_state.auth['role'] == 'admin': menu.append("إدارة المستخدمين")
    choice = st.sidebar.selectbox("القائمة العامة", menu)
    
    if st.sidebar.button("تسجيل خروج"):
        st.session_state.auth = None
        st.rerun()

    db = get_db(DB_FILE)

    # --- 1. العمليات الميدانية ---
    if choice == "العمليات الميدانية":
        sec = st.radio("اختر القسم العملياتي:", ["قسم الخروج", "قسم الدخول", "قسم صالة القدوم"], horizontal=True)
        lanes = db[db['القسم'] == sec]
        cols = st.columns(4 if "صالة القدوم" in sec else 7)
        
        for i, row in lanes.iterrows():
            idx = i
            with cols[i % (4 if "صالة القدوم" in sec else 7)]:
                color = "#28a745" if row["الحالة"] == "مشغول" else "#dc3545" if row["الحالة"] == "عطل" else "#6c757d"
                st.markdown(f"<div style='background-color:{color}; color:white; padding:10px; border-radius:8px; text-align:center;'>{row['النوع']} {row['المسار']}<br>{row['الموظف']}</div>", unsafe_allow_case=True)
                
                if row["الحالة"] == "فارغ":
                    if st.button("استلام", key=f"in_{idx}"):
                        db.at[idx, 'الحالة'] = "مشغول"
                        db.at[idx, 'الموظف'] = st.session_state.auth['user']
                        db.at[idx, 'وقت_الاستلام'] = datetime.now().strftime("%H:%M")
                        save_db(db, DB_FILE); st.rerun()
                elif row["الحالة"] == "مشغول":
                    if st.button("🚨 عطل", key=f"err_{idx}"):
                        db.at[idx, 'الحالة'] = "عطل"
                        db.at[idx, 'البلاغات'] = "عطل فني"
                        save_db(db, DB_FILE); st.rerun()
                    if st.button("تسليم", key=f"out_{idx}"):
                        db.at[idx, 'الحالة'] = "فارغ"
                        db.at[idx, 'الموظف'] = "-"
                        db.at[idx, 'وقت_الاستلام'] = "-"
                        save_db(db, DB_FILE); st.rerun()

    # --- 2. التقارير والطباعة (PDF) ---
    elif choice == "التقارير والطباعة":
        st.header("📋 التقرير اليومي الرسمي")
        p_sec = st.selectbox("القسم:", ["قسم الخروج", "قسم الدخول", "قسم صالة القدوم"])
        p_df = db[db['الالقسم'] == p_sec]
        st.table(p_df[['المسار', 'النوع', 'الحالة', 'الموظف', 'وقت_الاستلام', 'البلاغات']])
        
        # إنشاء PDF بسيط (HTML-based)
        report_html = f"""
        <div style="direction: rtl; font-family: Arial; padding: 20px; border: 2px solid #000;">
            <h1 style="text-align: center;">كروكي {p_sec} الرسمي</h1>
            <p>التاريخ: {datetime.now().strftime('%Y-%m-%d')} | وقت الشفت: {datetime.now().strftime('%H:%M')}</p>
            <table border="1" style="width: 100%; border-collapse: collapse; text-align: center;">
                <tr style="background-color: #f2f2f2;">
                    <th>المسار</th><th>النوع</th><th>الحالة</th><th>الموظف</th><th>وقت الاستلام</th>
                </tr>
                {"".join([f"<tr><td>{r['المسار']}</td><td>{r['النوع']}</td><td>{r['الحالة']}</td><td>{r['الموظف']}</td><td>{r['وقت_الاستلام']}</td></tr>" for _, r in p_df.iterrows()])}
            </table>
            <br><br>
            <div style="display: flex; justify-content: space-between;">
                <p>توقيع رئيس المناوبة: ........................</p>
                <p>الختم الرسمي للمركز: [ {p_sec} ]</p>
            </div>
        </div>
        """
        b64 = base64.b64encode(report_html.encode('utf-8-sig')).decode()
        st.markdown(f'<a href="data:text/html;base64,{b64}" download="Report_{p_sec}.pdf" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">💾 تحميل التقرير بصيغة PDF للطباعة</a>', unsafe_allow_case=True)

    # --- 3. إدارة المستخدمين (Admin Only) ---
    elif choice == "إدارة المستخدمين":
        st.header("👥 لوحة تحكم الإدارة")
        users = get_db(USERS_FILE)
        
        with st.form("إضافة مستخدم"):
            new_u = st.text_input("اسم المستخدم الجديد")
            new_p = st.text_input("كلمة السر")
            new_r = st.selectbox("الصلاحية", ["user", "admin"])
            if st.form_submit_button("إضافة"):
                new_entry = pd.DataFrame([{"user": new_u, "pass": new_p, "role": new_r, "active": True}])
                save_db(pd.concat([users, new_entry]), USERS_FILE)
                st.success("تمت الإضافة")
                st.rerun()
        
        st.subheader("قائمة المستخدمين الحالية")
        st.dataframe(users[['user', 'role', 'active']])
