import streamlit as st
import requests

# FastAPI Backend URL
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Insurance Predictor",
    page_icon="🏥",
    layout="centered"
)

st.title("🏥 Insurance Premium Category Predictor")

# -------------------------------------------------------------------
# 1. SESSION STATE SETUP (Token Ko Memory Mein Store Karne Ke Liye)
# -------------------------------------------------------------------
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None


# -------------------------------------------------------------------
# 2. SIDEBAR USER STATUS & LOGOUT
# -------------------------------------------------------------------
st.sidebar.title("👤 Account Status")
if st.session_state["token"]:
    st.sidebar.success(f"Logged in as:\n**{st.session_state['user_email']}**")
    if st.sidebar.button("Logout"):
        st.session_state["token"] = None
        st.session_state["user_email"] = None
        st.success("Logged out successfully!")
        st.rerun()
else:
    st.sidebar.info("🔒 Not Logged In")


# -------------------------------------------------------------------
# 3. NAVIGATION TABS (Signup, Login, Predict)
# -------------------------------------------------------------------
tab_login, tab_signup, tab_predict = st.tabs(["🔑 Login", "📝 Signup", "📊 Predict Premium"])


# ===================================================================
# TAB 1: LOGIN SCREEN
# ===================================================================
with tab_login:
    st.header("Login to Your Account")
    login_email = st.text_input("Email Address", key="login_email").strip()
    login_password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        if not login_email or not login_password:
            st.warning("⚠️ Please enter both Email and Password!")
        else:
            try:
                res = requests.post(
                    f"{API_URL}/login",
                    json={"email": login_email, "password": login_password}
                )
                
                if res.status_code == 200:
                    data = res.json()
                    st.session_state["token"] = data["access_token"]
                    st.session_state["user_email"] = login_email
                    st.success("✅ Login Successful! Go to 'Predict Premium' tab now.")
                    st.rerun()
                else:
                    st.error(f"❌ Login Failed: {res.json().get('detail', 'Invalid Credentials')}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to FastAPI. Make sure FastAPI server is running on port 8000!")


# ===================================================================
# TAB 2: SIGNUP SCREEN
# ===================================================================
with tab_signup:
    st.header("Create a New Account")
    signup_name = st.text_input("Full Name", key="signup_name").strip()
    signup_email = st.text_input("Email Address", key="signup_email").strip()
    signup_password = st.text_input("Password", type="password", key="signup_password")
    
    st.caption("🔒 Password Rule: Min 8 chars, 1 Uppercase, 1 Lowercase, 1 Number, 1 Special Char.")

    if st.button("Sign Up"):
        if not signup_name or not signup_email or not signup_password:
            st.warning("⚠️ Please fill in all fields!")
        else:
            try:
                res = requests.post(
                    f"{API_URL}/signup",
                    json={
                        "name": signup_name,
                        "email": signup_email,
                        "password": signup_password
                    }
                )
                
                if res.status_code in [200, 201]:
                    st.success("🎉 Account Created Successfully! Please switch to the 'Login' tab to sign in.")
                else:
                    error_detail = res.json().get("detail", "Signup failed")
                    if isinstance(error_detail, list):
                        error_detail = error_detail[0].get("msg", "Validation Error")
                    st.error(f"❌ Signup Failed: {error_detail}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to FastAPI server.")


# ===================================================================
# TAB 3: PREDICT SCREEN (PROTECTED ROUTE FEATURE)
# ===================================================================
with tab_predict:
    st.header("Insurance Premium Category Prediction")

    if not st.session_state["token"]:
        st.warning("🔒 **Protected Feature!** Please **Login** or **Signup** first to use the predictor.")
    else:
        st.write(f"Logged in as: **{st.session_state['user_email']}**")
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", min_value=1, max_value=119, value=30)
            weight = st.number_input("Weight (kg)", min_value=1.0, value=65.0)
            height = st.number_input("Height (m)", min_value=0.5, max_value=2.5, value=1.7)
            income_lpa = st.number_input("Annual Income (LPA)", min_value=0.1, value=10.0)
        
        with col2:
            smoker = st.selectbox("Are you a smoker?", options=[True, False])
            city = st.text_input("City", value="Mumbai")
            occupation = st.selectbox(
                "Occupation",
                ['retired', 'freelancer', 'student', 'government_job', 'business_owner', 'unemployed', 'private_job']
            )

        if st.button("Predict Premium Category"):
            input_data = {
                "age": int(age),
                "weight": float(weight),
                "height": float(height),
                "income_lpa": float(income_lpa),
                "smoker": bool(smoker),
                "city": str(city),
                "occupation": str(occupation)
            }

            headers = {
                "Authorization": f"Bearer {st.session_state['token']}"
            }

            try:
                res = requests.post(f"{API_URL}/predict", json=input_data, headers=headers)

                if res.status_code == 200:
                    result = res.json()
                    st.balloons()
                    st.success(f"🎉 Predicted Insurance Premium Category: **{result['predicted_category']}**")
                
                elif res.status_code == 401:
                    st.error("❌ Session Expired / Unauthorized! Please login again.")
                    st.session_state["token"] = None
                    st.session_state["user_email"] = None
                
                else:
                    try:
                        error_msg = res.json().get("detail", res.text)
                    except Exception:
                        error_msg = res.text
                        
                    st.error(f"❌ Backend Error (Status {res.status_code}): {error_msg}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to FastAPI server. Make sure Uvicorn is running on port 8000!")