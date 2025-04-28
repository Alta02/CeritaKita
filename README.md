# CeritaKita

Aplikasi mood tracker pasangan yang memungkinkan pasangan berbagi mood dan cerita mereka.

## Setup

1. Instal dependencies
```
pip install streamlit pandas plotly pymongo dnspython
```

2. Buat file `.streamlit/secrets.toml` di root folder dengan isi:
```toml
[mongodb]
uri = "mongodb+srv://username:password@cluster.mongodb.net/ceritakita?retryWrites=true&w=majority"
```

Ganti `username`, `password`, dan `cluster.mongodb.net` dengan detail MongoDB Anda.

## Struktur Database MongoDB

Database `love_message` menggunakan 3 koleksi utama:
- `couples`: Informasi tentang pasangan
- `moods`: Rekaman mood harian pengguna
- `replies`: Kumpulan quotes atau kata-kata yang ingin disampaikan

## Menjalankan Aplikasi

```
streamlit run main.py
```

## Fitur

- Login dan registrasi pasangan dengan couple code
- Mood tracker harian dengan emoji dan catatan
- Visualisasi mood dari waktu ke waktu
- Koleksi quotes pasangan
- Pengaturan profil