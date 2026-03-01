import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64

# --- 1. المعمارية الأساسية للنظام ---
class SmartPathSystem:
    def __init__(self):
        self.db_file = "official_storage.csv"
        self.users_file = "official_users.csv"
        self._initialize_infrastructure()

    def _initialize_infrastructure(self):
        # تهيئة قاعدة البيانات الرسمية
        if not os.path.exists(self.db_file):
            data = []
            sections = {"قسم الخروج": 14, "قسم الدخول": 14, "قسم صالة القدوم": 8}
            for sec, count in sections.items():
                for i in range(1, count + 1):
                    # تخصيص المسارات (شحن، خاص، عادي)
                    dtype = "🚛 شحن" if i == 13 and sec != "قسم صالة القدوم" else "⭐ خاص" if i == 14 and sec != "قسم صالة القدوم" else "عادي"
                    data.append({
                        "القسم": sec, "المسار": i, "الحالة": "فارغ", 
                        "الموظف": "-", "النوع": dtype, "وقت_الاستلام": "-", "البلاغ": "سليم"
                    })
            pd.DataFrame(data).to_csv(self.db_file, index=False)
        
        # تهيئة نظام المستخدمين
        if not os.path.exists(self.users_file):
            pd.DataFrame([{"user": "admin", "pass": "123", "role": "admin", "active": True}]).to_csv(self.users_file, index=False)

    def load_db(self): return pd.read_csv(self.db_file)
    def save_db(self, df): df.to_csv(self.db_file, index=False)
    def load_users(self): return pd.read_csv(self.users_file)
    def save_users(self, df): df.to_csv(self.users_file, index=False)

# تفعيل النظام
system = SmartPathSystem()

# --- 2. الواجهة الرسومية والأمان ---
st.set_page_config(page_title="نظام المسار الذكي المطور", layout="wide", initial_sidebar_state="expanded")

if 'session_auth' not in st.session_state: st.session_state.session_auth = None

if not st.session_state.session_auth:
    st.markdown("<h1 style='text-align:center;'>🔐 نظام المسار الذكي - بوابة الدخول الموحدة</h1>", unsafe_allow_case=True)
    with st.container():
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.button("دخول للنظام", use_container_width=True):
            users = system.load_users()
            user_data = users[(users['user'] == u) & (users['pass'] == str(p)) & (users['active'] == True)]
            if not user_data.empty:
                st.session_state.session_auth = user_data.iloc[0].to_dict()
                st.rerun()
            else: st.error("عذراً، بيانات الدخول غير صحيحة أو الحساب معلق.")
else:
    # --- 3. لوحة التحكم الميدانية ---
    st.sidebar.success(f"المستخدم: {st.session_state.session_auth['user']}")
    nav = ["📡 العمليات الميدانية", "📋 التقارير والطباعة الرسمية", "⚙️ إدارة النظام"]
    if st.session_state.session_auth['role'] != 'admin': nav.remove("⚙️ إدارة النظام")
    choice = st.sidebar.radio("القائمة الرئيسية", nav)
    
    if st.sidebar.button("تسجيل الخروج الآمن"):
        st.session_state.session_auth = None
        st.rerun()

    db = system.load_db()

    if "العمليات الميدانية" in choice:
        sec = st.segmented_control("اختر القسم العملياتي:", ["قسم الخروج", "قسم الدخول", "قسم صالة القدوم"], default="قسم الخروج")
        lanes = db[db['القسم'] == sec]
        cols = st.columns(4 if "صالة القدوم" in sec else 7)
        
        for i, (idx, row) in enumerate(lanes.iterrows()):
            with cols[i % (4 if "صالة القدوم" in sec else 7)]:
                # هندسة الألوان والحالات
                bg = "#1e7e34" if row["الحالة"] == "مشغول" else "#bd2130" if row["الحالة"] == "عطل" else "#495057"
                st.markdown(f"""<div style='background-color:{bg}; color:white; padding:15px; border-radius:10px; text-align:center; border: 1px solid #ffffff33;'>
                    <span style='font-size:12px;'>{row['النوع']}</span><br><b style='font-size:18px;'>{row['المسار']}</b><br><hr style='margin:5px;'>
                    <span style='font-size:12px;'>{row['الموظف']}</span></div>""", unsafe_allow_case=True)
                
                c1, c2 = st.columns(2)
                if row["الحالة"] == "فارغ":
                    if c1.button("استلام", key=f"rec_{idx}"):
                        db.at[idx, 'الحالة'], db.at[idx, 'الموظف'], db.at[idx, 'وقت_الاستلام'] = "مشغول", st.session_state.session_auth['user'], datetime.now().strftime("%H:%M:%S")
                        system.save_db(db); st.rerun()
                elif row["الحالة"] == "مشغول":
                    if c1.button("تسليم", key=f"rel_{idx}"):
                        db.at[idx, 'الحالة'], db.at[idx, 'الموظف'], db.at[idx, 'وقت_الاستلام'] = "فارغ", "-", "-"
                        system.save_db(db); st.rerun()
                    if c2.button("🚨 عطل", key=f"brk_{idx}"):
                        db.at[idx, 'الحالة'], db.at[idx, 'البلاغ'] = "عطل", f"بلاغ من {st.session_state.session_auth['user']}"
                        system.save_db(db); st.rerun()
                elif row["الحالة"] == "عطل":
                    if st.button("🛠️ تم الإصلاح", key=f"fix_{idx}", use_container_width=True):
                        db.at[idx, 'الحالة'], db.at[idx, 'البلاغ'] = "فارغ", "سليم"
                        system.save_db(db); st.rerun()

    elif "التقارير" in choice:
        st.header("📋 محرك التقارير والكروكي الرسمي")
        p_sec = st.selectbox("القسم المستهدف:", ["قسم الخروج", "قسم الدخول", "قسم صالة القدوم"])
        p_df = db[db['القسم'] == p_sec]
        st.dataframe(p_df, use_container_width=True)
        
        # إنشاء مستند الطباعة (HTML المتقدم للتحويل لـ PDF)
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        html_report = f"""<div style="direction:rtl; font-family:sans-serif; border:5px double #333; padding:30px;">
            <h1 style="text-align:center;">كروكي المسارات الرسمي - {p_sec}</h1>
            <p style="text-align:center;">صدر بتاريخ: {report_date}</p>
            <table style="width:100%; border-collapse:collapse; margin:20px 0;" border="1">
                <tr style="background:#eee;"><th>المسار</th><th>النوع</th><th>الحالة</th><th>الموظف</th><th>وقت الاستلام</th><th>البلاغات</th></tr>
                {"".join([f"<tr><td>{r['المسار']}</td><td>{r['النوع']}</td><td>{r['الحالة']}</td><td>{r['الموظف']}</td><td>{r['وقت_الاستلام']}</td><td>{r['البلاغ']}</td></tr>" for _, r in p_df.iterrows()])}
            </table>
            <div style="margin-top:50px; display:flex; justify-content:space-between;">
                <div>توقيع رئيس المناوبة: .............................</div>
                <div style="text-align:center; border:2px solid #000; padding:10px;">الختم الرسمي للمركز</div>
            </div>
        </div>"""
        b64 = base64.b64encode(html_report.encode('utf-8-sig')).decode()
        st.markdown(f'<a href="data:text/html;base64,{b64}" download="Official_Report.html" style="text-decoration:none; background:#007bff; color:white; padding:15px; border-radius:5px; font-weight:bold;">💾 تحميل كروكي الطباعة الرسمي (PDF)</a>', unsafe_allow_case=True)

    elif "إدارة النظام" in choice:
        st.header("⚙️ لوحة التحكم الإدارية")
        users = system.load_users()
        
        t1, t2 = st.tabs(["إدارة المستخدمين", "تطهير البيانات"])
        with t1:
            with st.form("إضافة موظف جديد"):
                nu, np, nr = st.text_input("اسم المستخدم"), st.text_input("كلمة المرور"), st.selectbox("الصلاحية", ["user", "admin"])
                if st.form_submit_button("اعتماد الموظف"):
                    new_user = pd.DataFrame([{"user": nu, "pass": np, "role": nr, "active": True}])
                    system.save_users(pd.concat([users, new_user]))
                    st.success("تم تفعيل الحساب الجديد"); st.rerun()
            st.dataframe(users)
        with t2:
            if st.button("⚠️ إعادة ضبط كافة المسارات (Factory Reset)"):
                if os.path.exists(system.db_file): os.remove(system.db_file)
                st.rerun()
