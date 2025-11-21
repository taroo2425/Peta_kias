
import sqlite3
import matplotlib
import math

matplotlib.use('Agg')  # Menginstal backend Matplotlib untuk menyimpan file dalam memori tanpa menampilkan jendela
import matplotlib.pyplot as plt
import cartopy.crs as ccrs  # Mengimpor modul yang akan memungkinkan kita bekerja dengan proyeksi peta

class DB_Map():
    def __init__(self, database):
        self.database = database  # Menginisiasi jalur database

    def create_user_table(self):
        conn = sqlite3.connect(self.database)  # Menghubungkan ke database
        with conn:
            # Membuat tabel, jika tidak ada, untuk menyimpan kota pengguna
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                user_id INTEGER,
                                city_id TEXT,
                                FOREIGN KEY(city_id) REFERENCES cities(id)
                            )''')
            conn.commit()  # Menyimpan perubahan

    def add_city(self, user_id, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            # Mencari kota dalam database berdasarkan nama
            cursor.execute("SELECT id FROM cities WHERE city=?", (city_name,))
            city_data = cursor.fetchone()
            if city_data:
                city_id = city_data[0]
                # Menambahkan kota ke daftar kota pengguna
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_id))
                conn.commit()
                return 1  # Menunjukkan bahwa operasi berhasil
            else:
                return 0  # Menunjukkan bahwa kota tidak ditemukan

    def select_cities(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            # Memilih semua kota pengguna
            cursor.execute('''SELECT cities.city 
                            FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))
            cities = [row[0] for row in cursor.fetchall()]
            return cities  # Mengembalikan daftar kota pengguna

    def get_coordinates(self, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            # Mendapatkan koordinat kota berdasarkan nama
            cursor.execute('''SELECT lat, lng
                            FROM cities  
                            WHERE city = ?''', (city_name,))
            coordinates = cursor.fetchone()
            return coordinates  # Mengembalikan koordinat kota

    def create_graph(self, path, cities):
        """
        Menggambar peta dengan titik untuk setiap kota di list `cities`
        dan menyimpannya ke `path`.
        return:
            True  -> jika minimal satu kota berhasil digambar
            False -> jika tidak ada kota valid
        """
        # Ambil koordinat semua kota
        coords = []
        for city in cities:
            data = self.get_coordinates(city)
            if data:
                lat, lng = data
                coords.append((city, lat, lng))

        if not coords:
            # Tidak ada kota dengan koordinat valid
            return False

        # Membuat figure dan axis dengan proyeksi peta
        fig = plt.figure(figsize=(10, 5))
        ax = plt.axes(projection=ccrs.PlateCarree())

        # Menampilkan dunia
        ax.stock_img()
        ax.coastlines()

        # Jika mau fokus ke area tertentu, bisa pakai ax.set_extent
        # Di sini kita set global saja
        ax.set_global()

        # Plot semua kota
        for city, lat, lng in coords:
            # lng = longitude (x), lat = latitude (y)
            ax.plot(lng, lat, marker='o', markersize=5, transform=ccrs.PlateCarree())
            ax.text(
                lng + 1, lat + 1, city,
                transform=ccrs.PlateCarree(),
                fontsize=8
            )

        plt.title("Peta Kota Pengguna")

        # Simpan ke file
        plt.savefig(path, bbox_inches='tight')
        plt.close(fig)

        return True

    def draw_distance(self, city1, city2):
        """
        Menggambar peta dengan dua kota dan garis di antaranya
        untuk menampilkan jarak kira-kira.
        return:
            (path, distance_km) jika sukses,
            (None, None) jika salah satu kota tidak ditemukan.
        """
        coords1 = self.get_coordinates(city1)
        coords2 = self.get_coordinates(city2)

        if not coords1 or not coords2:
            return None, None

        lat1, lng1 = coords1
        lat2, lng2 = coords2

        # Hitung jarak great-circle (haversine) dalam kilometer
        distance_km = self._haversine(lng1, lat1, lng2, lat2)

        path = f"distance_{city1}_{city2}.png"

        fig = plt.figure(figsize=(10, 5))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.stock_img()
        ax.coastlines()
        ax.set_global()

        # Plot kota
        ax.plot(lng1, lat1, marker='o', markersize=6, transform=ccrs.PlateCarree())
        ax.text(lng1 + 1, lat1 + 1, city1, transform=ccrs.PlateCarree(), fontsize=9)

        ax.plot(lng2, lat2, marker='o', markersize=6, transform=ccrs.PlateCarree())
        ax.text(lng2 + 1, lat2 + 1, city2, transform=ccrs.PlateCarree(), fontsize=9)

        # Garis penghubung
        ax.plot(
            [lng1, lng2],
            [lat1, lat2],
            linestyle='--',
            transform=ccrs.PlateCarree()
        )

        plt.title(f"Jarak {city1} - {city2}: {distance_km:.1f} km")
        plt.savefig(path, bbox_inches='tight')
        plt.close(fig)

        return path, distance_km

    @staticmethod
    def _haversine(lon1, lat1, lon2, lat2):
        """
        Menghitung jarak antara dua titik di permukaan bumi (km)
        menggunakan rumus haversine.
        """
        R = 6371.0  # radius bumi (km)

        # Konversi ke radian
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return distance


if __name__ == "__main__":
    m = DB_Map("database.db")  # Membuat objek yang akan berinteraksi dengan database
    m.create_user_table()   # Membuat tabel dengan kota pengguna, jika tidak sudah ada