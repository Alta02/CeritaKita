# app.py - CeritaKita without formal authentication

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random
from pymongo import MongoClient
from bson.objectid import ObjectId
import traceback

# Aktifkan mode debug
debug_mode = False

# Set page config di awal
st.set_page_config(
    page_title="CeritaKita",
    page_icon="💜",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Debug info
if debug_mode:
    st.info("Mode debug aktif")
    st.write("Python packages:")
    st.write(f"- Streamlit: {st.__version__}")
    st.write(f"- Pandas: {pd.__version__}")
    st.write(f"- Plotly: {px.__version__}")

# MongoDB setup - memeriksa apakah dalam produksi atau pengembangan
try:
    # Coba gunakan Streamlit secrets (production)
    mongodb_uri = st.secrets["mongodb"]["uri"]
    if debug_mode:
        st.success("Berhasil membaca secrets MongoDB")
except Exception as e:
    # Fallback untuk pengembangan lokal - bisa gunakan dotenv jika dibutuhkan
    error_msg = f"Gagal memuat secrets: {e}. Pastikan file .streamlit/secrets.toml dibuat dengan benar."
    st.error(error_msg)
    if debug_mode:
        st.error(traceback.format_exc())
    # Hentikan eksekusi jika tidak ada koneksi database
    st.stop()

# Coba sambungkan ke database
try:
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    # Verifikasi koneksi dengan ping
    client.admin.command('ping')
    db = client.love_message
    if debug_mode:
        st.success("Berhasil terhubung ke MongoDB")
except Exception as e:
    error_msg = f"Gagal terhubung ke MongoDB: {e}"
    st.error(error_msg)
    if debug_mode:
        st.error(traceback.format_exc())
    st.stop()

# Helper functions for MongoDB
def object_id_to_str(data):
    """Convert ObjectId to string in MongoDB documents"""
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, ObjectId):
                data[k] = str(v)
            elif isinstance(v, (dict, list)):
                data[k] = object_id_to_str(v)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            if isinstance(v, ObjectId):
                data[i] = str(v)
            elif isinstance(v, (dict, list)):
                data[i] = object_id_to_str(v)
    return data

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'theme_mode' not in st.session_state:
    st.session_state.theme_mode = 'light'  # Default theme is light

# Function to toggle theme
def toggle_theme():
    if st.session_state.theme_mode == 'light':
        st.session_state.theme_mode = 'dark'
    else:
        st.session_state.theme_mode = 'light'

# Custom CSS
def apply_custom_css():
    theme_mode = st.session_state.theme_mode
    
    if theme_mode == 'light':
        bg_color = "#F8F0FC"
        text_color = "#333333"
        card_bg_color = "white"
        card_shadow = "0 4px 6px rgba(0, 0, 0, 0.05)"
        quote_bg = "#EBDFFC"
    else:  # dark mode
        bg_color = "#121212"
        text_color = "#F0F0F0"
        card_bg_color = "#1E1E1E"
        card_shadow = "0 4px 6px rgba(0, 0, 0, 0.2)"
        quote_bg = "#2D2D2D"
    
    st.markdown(f"""
    <style>
    :root {{
        --primary-color: #BFA2DB;
        --bg-color: {bg_color};
        --text-color: {text_color};
        --accent-color: #9A73C7;
        --card-bg-color: {card_bg_color};
        --card-shadow: {card_shadow};
        --quote-bg: {quote_bg};
    }}
    
    .stApp {{
        background-color: var(--bg-color);
        color: var(--text-color);
        font-family: 'Quicksand', sans-serif;
    }}
    
    .main-header {{
        color: var(--primary-color);
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
    }}
    
    .sub-header {{
        color: var(--accent-color);
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 2rem;
    }}
    
    .card {{
        background-color: var(--card-bg-color);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: var(--card-shadow);
        margin: 1rem 0;
    }}
    
    .mood-emoji {{
        font-size: 2rem;
    }}
    
    .stButton > button {{
        background-color: var(--primary-color);
        color: white;
        border-radius: 20px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }}
    
    .stButton > button:hover {{
        background-color: var(--accent-color);
    }}
    
    /* Login form submit button styling */
    .stButton button[kind="formSubmit"] {{
        background-color: var(--primary-color);
        color: white;
        width: 100%;
        border-radius: 20px;
        padding: 0.6rem 0;
        margin-top: 1rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
    }}
    
    .stButton button[kind="formSubmit"]:hover {{
        background-color: var(--accent-color);
        transform: translateY(-2px);
    }}
    
    .quote-box {{
        background-color: var(--quote-bg);
        border-radius: 10px;
        padding: 1rem;
        font-style: italic;
        text-align: center;
    }}
    
    div.stTextInput > div > div > input {{
        border-radius: 10px;
        border: 1px solid var(--primary-color);
    }}
    
    .sidebar-header {{
        text-align: center;
        margin-bottom: 1.5rem;
    }}
    
    .theme-toggle {{
        position: absolute;
        top: 10px;
        right: 10px;
        z-index: 1000;
    }}
    </style>
    
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

apply_custom_css()

# Simple couple authentication
def couple_login(couple_code, name):
    if not couple_code or not name:
        return False, "Harap isi couple code dan nama Anda"
    
    try:
        # Check if couple exists
        couple = db.couples.find_one({"couple_code": couple_code})
        
        if couple:
            # Couple exists, check if user is part of it
            couple = object_id_to_str(couple)
            if couple['person1_name'] == name:
                st.session_state.user_id = "person1"
                st.session_state.user_name = name
                st.session_state.partner_name = couple['person2_name']
                st.session_state.couple_id = str(couple['_id'])
                st.session_state.couple_code = couple_code
                return True, "Login berhasil sebagai Person 1!"
            
            elif couple['person2_name'] == name:
                st.session_state.user_id = "person2"
                st.session_state.user_name = name
                st.session_state.partner_name = couple['person1_name']
                st.session_state.couple_id = str(couple['_id'])
                st.session_state.couple_code = couple_code
                return True, "Login berhasil sebagai Person 2!"
            
            elif not couple['person2_name']:
                # Person 2 doesn't exist yet, register as person 2
                db.couples.update_one({"_id": couple['_id']}, {"$set": {"person2_name": name}})
                
                st.session_state.user_id = "person2"
                st.session_state.user_name = name
                st.session_state.partner_name = couple['person1_name']
                st.session_state.couple_id = str(couple['_id'])
                st.session_state.couple_code = couple_code
                return True, "Selamat datang! Kamu berhasil bergabung sebagai Person 2!"
            
            else:
                return False, "Nama tidak cocok dengan couple code ini atau pasangan sudah penuh"
        
        else:
            # Couple doesn't exist, create new
            new_couple = db.couples.insert_one({
                "couple_code": couple_code,
                "person1_name": name,
                "person2_name": None,
                "created_at": datetime.now().isoformat()
            })
            
            if new_couple.inserted_id:
                st.session_state.user_id = "person1"
                st.session_state.user_name = name
                st.session_state.partner_name = None
                st.session_state.couple_id = str(new_couple.inserted_id)
                st.session_state.couple_code = couple_code
                return True, "Kamu telah membuat couple baru! Bagikan couple code ini dengan pasanganmu."
            else:
                return False, "Gagal membuat couple baru"
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.authenticated = False
    return True, "Berhasil logout!"

# Login page
def render_login_page():
    # Theme toggle
    theme_icon = "🌙" if st.session_state.theme_mode == "light" else "☀️"
    if st.button(f"{theme_icon} Ganti Tema", key="theme_toggle_login"):
        toggle_theme()
        st.rerun()
        
    st.markdown("<h1 class='main-header'>💜 CeritaKita</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Cerita cinta kita berdua dalam aplikasi yang manis</p>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    with st.form("login_form"):
        st.subheader("Masuk ke CeritaKita")
        name = st.text_input("Nama Kamu")
        couple_code = st.text_input("Couple Code", 
                                   help="Kode unik untuk menghubungkan kamu dengan pasanganmu")
        
        if not couple_code:
            suggested_code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
            st.info(f"Suggested Couple Code: {suggested_code} (you can change it)")
        
        submit_button = st.form_submit_button("Masuk")
        
        if submit_button:
            success, message = couple_login(couple_code, name)
            if success:
                st.session_state.authenticated = True
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    st.markdown("</div>", unsafe_allow_html=True)

# Dashboard page
def render_dashboard():
    st.markdown(f"<h1 class='main-header'>CeritaKita</h1>", unsafe_allow_html=True)
    
    # Get user data
    user_id = st.session_state.user_id
    user_name = st.session_state.user_name
    partner_name = st.session_state.get('partner_name', 'pasanganmu')
    couple_id = st.session_state.couple_id
    
    # Welcome message
    st.markdown(f"<div class='card'><h3>Halo, {user_name}! 👋</h3>", unsafe_allow_html=True)
    
    # Remove relationship days counter
    st.markdown(f"<p>Selamat datang kembali di CeritaKita!</p>", unsafe_allow_html=True)
    
    # Latest moods
    col1, col2 = st.columns(2)
    
    # Get latest moods
    try:
        my_mood = db.moods.find_one({"couple_id": str(couple_id), "user_id": user_id}, sort=[("created_at", -1)])
        if my_mood:
            my_mood = object_id_to_str(my_mood)
        
        partner_id = "person1" if user_id == "person2" else "person2"
        partner_moods = None
        if partner_name:
            partner_moods = db.moods.find_one({"couple_id": str(couple_id), "user_id": partner_id}, sort=[("created_at", -1)])
            if partner_moods:
                partner_moods = object_id_to_str(partner_moods)
        
        with col1:
            st.markdown("<p><b>Mood Kamu:</b></p>", unsafe_allow_html=True)
            if my_mood:
                mood_emoji = my_mood['mood_emoji'] 
                mood_note = my_mood['mood_note']
                st.markdown(f"<p class='mood-emoji'>{mood_emoji}</p>", unsafe_allow_html=True)
                st.markdown(f"<p><i>\"{mood_note}\"</i></p>", unsafe_allow_html=True)
            else:
                st.markdown("<p>Belum ada mood hari ini</p>", unsafe_allow_html=True)
                if st.button("Update Mood Sekarang"):
                    st.session_state.current_page = "mood_tracker"
                    st.rerun()
        
        with col2:
            st.markdown(f"<p><b>Mood {partner_name}:</b></p>", unsafe_allow_html=True)
            if partner_moods:
                mood_emoji = partner_moods['mood_emoji']
                mood_note = partner_moods['mood_note']
                st.markdown(f"<p class='mood-emoji'>{mood_emoji}</p>", unsafe_allow_html=True)
                st.markdown(f"<p><i>\"{mood_note}\"</i></p>", unsafe_allow_html=True)
            else:
                st.markdown("<p>Belum ada update mood</p>", unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Error fetching moods: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Quote of the day
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3 class='sub-header'>Quote Hari Ini</h3>", unsafe_allow_html=True)
    
    # Get a random quote from the database
    try:
        quotes = list(db.replies.find({"couple_id": str(couple_id)}))
        quotes = object_id_to_str(quotes)
        if quotes:
            quote = random.choice(quotes)
            st.markdown(f"<div class='quote-box'>\"{quote['quote_text']}\"</div>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: right; font-style: italic;'>— {quote['author']}</p>", unsafe_allow_html=True)
        else:
            # Default quotes
            default_quotes = [
                {"text": "Cinta tidak pernah meminta, ia selalu memberi.", "author": "Kahlil Gibran"},
                {"text": "Aku mencintaimu bukan karena siapa dirimu, melainkan karena siapa diriku saat bersamamu.", "author": "Roy Croft"},
                {"text": "Mencintai bukan hanya tentang siapa yang membuatmu tertawa, tetapi siapa yang membuatmu bahagia.", "author": "Anonymous"},
                {"text": "Cinta sejati tidak pernah berakhir. Cinta sejati adalah api abadi.", "author": "Bruce Lee"}
            ]
            random_quote = random.choice(default_quotes)
            st.markdown(f"<div class='quote-box'>\"{random_quote['text']}\"</div>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: right; font-style: italic;'>— {random_quote['author']}</p>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error fetching quotes: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Mood Tracker page
def render_mood_tracker():
    st.markdown("<h1 class='main-header'>Mood Tracker</h1>", unsafe_allow_html=True)
    
    # Mood input card
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3>Bagaimana perasaanmu hari ini?</h3>", unsafe_allow_html=True)
    
    # Emoji mood selector
    mood_options = {
        "😍": "Sangat Bahagia",
        "😊": "Senang",
        "😐": "Biasa saja", 
        "😔": "Sedih",
        "😢": "Sangat Sedih"
    }
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    selected_mood = None
    with col1:
        if st.button("😍", use_container_width=True):
            selected_mood = "😍"
    with col2:
        if st.button("😊", use_container_width=True):
            selected_mood = "😊"
    with col3:
        if st.button("😐", use_container_width=True):
            selected_mood = "😐"
    with col4:
        if st.button("😔", use_container_width=True):
            selected_mood = "😔"
    with col5:
        if st.button("😢", use_container_width=True):
            selected_mood = "😢"
    
    if selected_mood:
        st.session_state.selected_mood = selected_mood
        st.success(f"Mood dipilih: {selected_mood} ({mood_options[selected_mood]})")
    
    # Mood note
    mood_note = st.text_area("Catatan perasaan (opsional):", 
                             placeholder="Ceritakan lebih detail tentang perasaanmu...")
    
    # Save mood
    if st.button("Simpan Mood"):
        if 'selected_mood' in st.session_state:
            try:
                db.moods.insert_one({
                    "couple_id": str(st.session_state.couple_id),
                    "user_id": st.session_state.user_id,
                    "mood_emoji": st.session_state.selected_mood,
                    "mood_note": mood_note if mood_note else "",
                    "created_at": datetime.now().isoformat()
                })
                st.success("Mood berhasil disimpan!")
                # Clear the selection
                if 'selected_mood' in st.session_state:
                    del st.session_state.selected_mood
            except Exception as e:
                st.error(f"Error saving mood: {str(e)}")
        else:
            st.warning("Pilih mood terlebih dahulu!")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Mood history
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3>Riwayat Mood</h3>", unsafe_allow_html=True)
    
    # Get mood history
    try:
        moods_cursor = db.moods.find({"couple_id": str(st.session_state.couple_id), "user_id": st.session_state.user_id}).sort("created_at", -1)
        moods = list(moods_cursor)
        moods = object_id_to_str(moods)
        
        if moods:
            # Convert to DataFrame
            df = pd.DataFrame(moods)
            df['date'] = pd.to_datetime(df['created_at']).dt.date
            
            # Plot mood history
            fig = px.line(
                df, 
                x='date', 
                y=[1 if e == "😍" else 2 if e == "😊" else 3 if e == "😐" else 4 if e == "😔" else 5 for e in df['mood_emoji']],
                labels={'y': 'Mood', 'date': 'Tanggal'},
                markers=True,
                color_discrete_sequence=['#BFA2DB']
            )
            
            # Customize y-axis
            fig.update_layout(
                yaxis=dict(
                    tickvals=[1, 2, 3, 4, 5],
                    ticktext=["😍", "😊", "😐", "😔", "😢"],
                    autorange="reversed"
                ),
                height=300,
                margin=dict(l=10, r=10, t=10, b=10)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show mood entries
            st.markdown("<h4>Catatan Mood</h4>", unsafe_allow_html=True)
            for idx, mood in enumerate(moods[:5]):  # Show only 5 latest entries
                date_str = datetime.fromisoformat(mood['created_at']).strftime("%d %b %Y, %H:%M")
                st.markdown(f"<p><b>{date_str}</b> - {mood['mood_emoji']} {mood['mood_note']}</p>", unsafe_allow_html=True)
            
            if len(moods) > 5:
                st.write(f"... dan {len(moods) - 5} entri lainnya")
        else:
            st.info("Belum ada riwayat mood. Mulai catat mood harian kamu sekarang!")
    except Exception as e:
        st.error(f"Error fetching mood history: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Quote collection page
def render_quotes():
    st.markdown("<h1 class='main-header'>Quotes of Love</h1>", unsafe_allow_html=True)
    
    # Add new quote card
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3>Tambah Quote Baru</h3>", unsafe_allow_html=True)
    
    with st.form("add_quote_form"):
        quote_text = st.text_area("Quote", placeholder="Tuliskan quote cinta yang ingin kamu simpan...")
        author = st.text_input("Penulis/Sumber", placeholder="Nama penulis atau sumber quote")
        
        submit_button = st.form_submit_button("Simpan Quote")
        
        if submit_button:
            if not quote_text:
                st.error("Quote tidak boleh kosong")
            else:
                try:
                    db.replies.insert_one({
                        "couple_id": str(st.session_state.couple_id),
                        "quote_text": quote_text,
                        "author": author if author else "Unknown",
                        "added_by": st.session_state.user_id,
                        "created_at": datetime.now().isoformat()
                    })
                    st.success("Quote berhasil disimpan!")
                except Exception as e:
                    st.error(f"Error saving quote: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Quote collection
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3>Koleksi Quote</h3>", unsafe_allow_html=True)
    
    # Get quotes
    try:
        quotes_cursor = db.replies.find({"couple_id": str(st.session_state.couple_id)}).sort("created_at", -1)
        quotes = list(quotes_cursor)
        quotes = object_id_to_str(quotes)
        
        if quotes:
            # Display quotes
            for idx, quote in enumerate(quotes):
                with st.container():
                    st.markdown(f"<div class='quote-box'>\"{quote['quote_text']}\"</div>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: right; font-style: italic;'>— {quote['author']}</p>", unsafe_allow_html=True)
                    
                    # Show who added the quote
                    added_by_name = st.session_state.user_name if quote['added_by'] == st.session_state.user_id else st.session_state.partner_name
                    if added_by_name:
                        st.markdown(f"<p style='text-align: right; font-size: 0.8rem;'>Ditambahkan oleh {added_by_name}</p>", unsafe_allow_html=True)
                    
                    st.markdown("<hr>", unsafe_allow_html=True)
        else:
            st.info("Belum ada quotes. Tambahkan quote pertama kamu!")
    except Exception as e:
        st.error(f"Error fetching quotes: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Profile settings page
def render_profile_settings():
    st.markdown("<h1 class='main-header'>Pengaturan Profil</h1>", unsafe_allow_html=True)
    
    # Get couple data
    try:
        couple = db.couples.find_one({"_id": ObjectId(st.session_state.couple_id)})
        if couple:
            couple = object_id_to_str(couple)
            
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            
            with st.form("profile_settings_form"):
                st.subheader("Informasi Profil")
                
                # Determine which person this is
                if st.session_state.user_id == "person1":
                    name = st.text_input("Nama Kamu", value=couple.get('person1_name', ''))
                    partner_name = st.text_input("Nama Pasangan", value=couple.get('person2_name', ''), disabled=True)
                else:
                    name = st.text_input("Nama Kamu", value=couple.get('person2_name', ''))
                    partner_name = st.text_input("Nama Pasangan", value=couple.get('person1_name', ''), disabled=True)
                
                couple_code = st.text_input("Couple Code", value=couple.get('couple_code', ''), disabled=True)
                
                submit_button = st.form_submit_button("Simpan Perubahan")
                
                if submit_button:
                    try:
                        # Prepare update data
                        update_data = {
                            "updated_at": datetime.now().isoformat()
                        }
                        
                        if st.session_state.user_id == "person1":
                            update_data["person1_name"] = name
                        else:
                            update_data["person2_name"] = name
                        
                        # Update database
                        db.couples.update_one({"_id": ObjectId(st.session_state.couple_id)}, {"$set": update_data})
                        
                        # Update session state
                        st.session_state.user_name = name
                        
                        st.success("Profil berhasil diperbarui!")
                    except Exception as e:
                        st.error(f"Error updating profile: {str(e)}")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Account settings
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("Pengaturan Akun")
            
            st.write(f"Couple Code kamu adalah: **{couple.get('couple_code')}**")
            st.write("Bagikan kode ini dengan pasanganmu agar dapat login ke akun yang sama.")
            
            if st.button("Logout"):
                success, message = logout()
                if success:
                    st.success(message)
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error("Data couple tidak ditemukan")
    except Exception as e:
        st.error(f"Error fetching couple data: {str(e)}")

# Function to test MongoDB connection
def test_mongodb_connection():
    try:
        # Check server info to test connection
        server_info = client.server_info()
        version = server_info.get('version', 'unknown')
        return True, f"Terhubung ke MongoDB (version {version})"
    except Exception as e:
        return False, f"Gagal terhubung: {str(e)}"

# Function to mask MongoDB URI for security
def mask_mongodb_uri(uri):
    if not uri:
        return "URI tidak ditemukan"
    
    try:
        # Simple masking: show only the beginning and end parts
        if '@' in uri:
            # If URI has credentials
            prefix = uri.split('@')[0]
            suffix = uri.split('@')[1]
            
            # Mask username and password
            auth_part = prefix.split('://')
            if len(auth_part) > 1:
                protocol = auth_part[0] + '://'
                credentials = auth_part[1]
                if ':' in credentials:
                    username = credentials.split(':')[0]
                    masked_username = username[:2] + '*' * (len(username) - 2) if len(username) > 2 else '*' * len(username)
                    masked_credentials = masked_username + ':****'
                else:
                    masked_credentials = credentials[:2] + '*' * (len(credentials) - 2)
                
                # Mask host details
                if '/' in suffix:
                    host_part = suffix.split('/')[0]
                    db_part = '/' + '/'.join(suffix.split('/')[1:])
                    masked_host = host_part[:5] + '*' * (len(host_part) - 5) if len(host_part) > 5 else '*' * len(host_part)
                    masked_uri = protocol + masked_credentials + '@' + masked_host + db_part
                else:
                    masked_host = suffix[:5] + '*' * (len(suffix) - 5) if len(suffix) > 5 else '*' * len(suffix)
                    masked_uri = protocol + masked_credentials + '@' + masked_host
            else:
                masked_uri = uri[:10] + '*' * (len(uri) - 15) + uri[-5:]
        else:
            # URI without credentials
            masked_uri = uri[:10] + '*' * (len(uri) - 15) + uri[-5:]
        
        return masked_uri
    except Exception:
        # If any error occurs during masking, mask the entire string
        return uri[:10] + '*' * (len(uri) - 15) + uri[-5:] if len(uri) > 20 else '*' * len(uri)

# Main navigation
def main():
    if not st.session_state.authenticated:
        render_login_page()
    else:
        # Initialize current page if not exists
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "dashboard"
        
        # Sidebar navigation
        with st.sidebar:
            st.markdown("<div class='sidebar-header'>", unsafe_allow_html=True)
            st.markdown(f"<h2>CeritaKita</h2>", unsafe_allow_html=True)
            st.markdown(f"<p>Halo, {st.session_state.user_name}!</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Theme toggle in sidebar
            theme_icon = "🌙" if st.session_state.theme_mode == "light" else "☀️"
            theme_text = "Mode Gelap" if st.session_state.theme_mode == "light" else "Mode Terang"
            if st.button(f"{theme_icon} {theme_text}", key="theme_toggle_sidebar"):
                toggle_theme()
                st.rerun()
                
            st.markdown("---")
            
            if st.button("📊 Dashboard", use_container_width=True):
                st.session_state.current_page = "dashboard"
                st.rerun()
            
            if st.button("😊 Mood Tracker", use_container_width=True):
                st.session_state.current_page = "mood_tracker"
                st.rerun()
            
            if st.button("💬 Quotes of Love", use_container_width=True):
                st.session_state.current_page = "quotes"
                st.rerun()
            
            if st.button("⚙️ Pengaturan Profil", use_container_width=True):
                st.session_state.current_page = "profile"
                st.rerun()
            
            # MongoDB connection status
            st.markdown("---")
            st.markdown("<p style='font-size:0.9rem;'>Status Database:</p>", unsafe_allow_html=True)
            
            # Display masked MongoDB URI
            masked_uri = mask_mongodb_uri(mongodb_uri)
            st.markdown(f"<p style='font-size:0.8rem; word-break: break-all;'><b>URI:</b> {masked_uri}</p>", unsafe_allow_html=True)
            
            if st.button("🔄 Test Koneksi", key="test_db_connection"):
                success, message = test_mongodb_connection()
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        # Render selected page
        if st.session_state.current_page == "dashboard":
            render_dashboard()
        elif st.session_state.current_page == "mood_tracker":
            render_mood_tracker()
        elif st.session_state.current_page == "quotes":
            render_quotes()
        elif st.session_state.current_page == "profile":
            render_profile_settings()

if __name__ == "__main__":
    main()