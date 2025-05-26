import os
from datetime import datetime
import urllib.request
import pandas as pd


# NOAA ID -> український ID
province_id_map = {
    24: 1, 25: 2, 5: 3, 4: 25, 6: 4, 27: 5, 23: 6, 26: 7, 7: 8,
    11: 9, 13: 10, 14: 11, 15: 12, 16: 13, 17: 14, 18: 15, 19: 16,
    21: 17, 22: 18, 8: 19, 9: 20, 10: 21, 1: 22, 2: 23, 3: 24
}

# NOAA ID -> назва області
province_name_map = {
    24: "Вінницька", 25: "Волинська", 5: "Дніпропетровська", 4: "Республіка Крим",
    6: "Донецька", 27: "Житомирська", 23: "Закарпатська", 26: "Запорізька",
    7: "Івано-Франківська", 11: "Київська", 13: "Кіровоградська", 14: "Луганська",
    15: "Львівська", 16: "Миколаївська", 17: "Одеська", 18: "Полтавська",
    19: "Рівненська", 21: "Сумська", 22: "Тернопільська", 8: "Харківська",
    9: "Херсонська", 10: "Хмельницька", 1: "Черкаська", 2: "Чернівецька",
    3: "Чернігівська"
}

# Для виведення інформації без обрізання
# pd.set_option('display.max_rows', None)

# Шлях до директорії для збереження CSV-файлів
data_dir = 'lab2/data'
os.makedirs(data_dir, exist_ok=True)

# Завантаження VHI-даних
def download_vhi():
    if os.path.exists(data_dir) and any(f.endswith('.csv') for f in os.listdir(data_dir)):
        print("[INFO] Дані вже існують. Завантаження пропущено.")
        return

    for noaa_id in province_id_map.keys():
        now = datetime.now()
        date_and_time_time = now.strftime("%d%m%Y%H%M%S")
        url = f"https://www.star.nesdis.noaa.gov/smcd/emb/vci/VH/get_TS_admin.php?country=UKR&provinceID={noaa_id}&year1=1981&year2=2024&type=Mean"
        filename = f"NOAA_ID{noaa_id}_{date_and_time_time}.csv"
        filepath = os.path.join(data_dir, filename)

        try:
            with urllib.request.urlopen(url) as response, open(filepath, 'wb') as out_file:
                out_file.write(response.read())
            print(f"[ІНФО] Завантажено: {filename}")
        except Exception as e:
            print(f"[ПОМИЛКА] Не вдалося завантажити дані для {noaa_id}: {e}")

download_vhi()

# Зчитування і обробка всіх CSV-файлів
def read_all_vhi_files(directory):
    df_list = []
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            path = os.path.join(directory, filename)
            try:
                df = pd.read_csv(path, index_col=False, header=1)
                df.columns = ['Year', 'Week', 'SMN', 'SMT', 'VCI', 'TCI', 'VHI']

                noaa_id_str = filename.split('_')[1]
                noaa_id = int(noaa_id_str.replace('ID', ''))

                ua_province_id = province_id_map.get(noaa_id)
                province_name = province_name_map.get(noaa_id)

                if ua_province_id is None or province_name is None:
                    print(f"[ПОМИЛКА] Не знайдено інформацію для NOAA ID: {noaa_id} у файлі {filename}")
                    continue

                df['Province_id'] = ua_province_id
                df['Province_name'] = province_name
                df_list.append(df)
            except Exception as e:
                print(f"[ПОМИЛКА] Не вдалося зчитати {filename}: {e}")
    return pd.concat(df_list, ignore_index=True)

# Зчитуємо всі файли у єдиний DataFrame
vhi_df = read_all_vhi_files(data_dir)

# Очистка та підготовка даних
vhi_df.replace(-1, pd.NA, inplace=True)
cols_to_convert = ['Year', 'Week', 'SMN', 'SMT', 'VCI', 'TCI', 'VHI', 'Province_id']
vhi_df[cols_to_convert] = vhi_df[cols_to_convert].apply(pd.to_numeric, errors='coerce')
vhi_df = vhi_df.dropna()
vhi_df = vhi_df.astype({'Year': int, 'Week': int, 'Province_id': int})

# Ряд VHI для області за вказаний рік
def vhi_by_year_province(df, province_id, year):
    province_name = next((name for k, v in province_id_map.items() if v == province_id for key, name in province_name_map.items() if key == k), "Невідома область")
    print(f"\n[VHI] Область {province_id} ({province_name}), Рік {year}:")
    print(df[(df['Province_id'] == province_id) & (df['Year'] == year)][['Week', 'VHI']])

# Пошук екстремумів (min та max) для вказаних областей та років, середнього, медіани
def vhi_extremums(df, province_ids, years):
    for pid in province_ids:
        province_name = next((name for k, v in province_id_map.items() if v == pid for key, name in province_name_map.items() if key == k), "Невідома область")
        for y in years:
            subset = df[(df['Province_id'] == pid) & (df['Year'] == y)]
            if not subset.empty:
                vhi_vals = subset['VHI']
                print(f"\n[ЕКСТРЕМУМ] Область {pid} ({province_name}), Рік {y}:")
                print(f"  Мінімум: {vhi_vals.min()}, Максимум: {vhi_vals.max()}, Середнє: {vhi_vals.mean():.2f}, Медіана: {vhi_vals.median():.2f}")

# Виводить VHI для діапазону років та списку областей
def vhi_range(df, province_ids, year_from, year_to):
    names = []
    for pid in province_ids:
        name = next((n for k, v in province_id_map.items() if v == pid for key, n in province_name_map.items() if key == k), "Невідома область")
        names.append(f"{pid} ({name})")
    print(f"\n[ДІАПАЗОН] Області {names}, Роки {year_from}-{year_to}")
    print(df[(df['Province_id'].isin(province_ids)) & (df['Year'].between(year_from, year_to))][['Province_name', 'Year', 'Week', 'VHI']])

# Визначає роки з екстремальною посухою (VHI нижче порогу в кількох областях)
def detect_extreme_droughts(df, threshold=15, province_count=5):
    droughts = df[df['VHI'] < threshold]
    grouped = droughts.groupby(['Year', 'Province_id']).size().reset_index(name='count')
    counts = grouped.groupby('Year').size()
    critical_years = counts[counts >= province_count]
    print(f"\n[ПОСУХИ] Роки з ≥{province_count} областями з VHI < {threshold}:")
    for year in critical_years.index:
        provinces = grouped[grouped['Year'] == year]['Province_id'].tolist()
        provinces_names = []
        for pid in provinces:
            name = next((n for k, v in province_id_map.items() if v == pid for key, n in province_name_map.items() if key == k), "Невідома область")
            provinces_names.append(name)
        values = df[(df['Year'] == year) & (df['Province_id'].isin(provinces)) & (df['VHI'] < threshold)][['Province_name', 'Week', 'VHI']]
        print(f"  Рік: {year}, Області: {[f'{r} ({n})' for r,n in zip(provinces, provinces_names)]}")
        print(values)

# Приклади виклику
if __name__ == "__main__":
    vhi_by_year_province(vhi_df, 14, 2002)
    vhi_extremums(vhi_df, [1, 2, 3], [2000, 2010])
    vhi_range(vhi_df, [4, 5], 2005, 2007)
    detect_extreme_droughts(vhi_df)
