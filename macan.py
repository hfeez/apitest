import folium
import math
import telebot
import time
import os
import re
import csv
import pandas as pd  # Import modul pandas
import telegram
import requests
import locale
import datetime
import json
import base64
import pytz
import datetime
import shutil
import os
import openpyxl
from openpyxl import Workbook, load_workbook
from telebot import types
from geopy.distance import geodesic
from datetime import datetime, timedelta
# from telegram.ext import Updater, CommandHandler
from openpyxl import load_workbook
from geopy.geocoders import Nominatim
from requests.exceptions import Timeout
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# from azure.cognitiveservices.vision.computervision import ComputerVisionClient
# from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
# from msrest.authentication import CognitiveServicesCredentials
from flask import Flask, jsonify, request

geolocator = Nominatim(user_agent="nama_user_agent_anda")
locale.setlocale(locale.LC_TIME, '')

file_mapping = {
    '510-01': ['Combain.csv', 'IM3H3I.csv', 'MLS.csv', '510new.csv', '510.csv'],
    '510-21': ['Combain.csv', 'IM3H3I.csv', 'MLS.csv', '510new.csv', '510.csv'],
    '510-11': ['Combain.csv', 'XL.csv', 'MLS.csv', '510new.csv', '510.csv'],
    '510-89': ['Combain.csv', 'MLS.csv', '510new.csv', '510.csv'],
    '510-10': ['Combain.csv', 'MLS.csv', '510new.csv', '510.csv'],
    '510-09': ['Combain.csv', 'MLS.csv', '510new.csv', '510.csv']
}

# def barcode_number_msisdn_from_caption(caption):
#     modified_caption = caption.replace("/Ccp", "").replace("/MCNcp", "").replace(" ", "")
#     caption_parts_msisdn = modified_caption
#     # .split('BAR')
#     print(len(caption_parts_msisdn))
#     if len(caption_parts_msisdn) > 1:
#         msisdn = caption_parts_msisdn[1].strip()
#         print(msisdn)
#         # Pastikan panjang MSISDN setidaknya 8 digit
#         if len(msisdn) >= 8:
#             # Sensor 4 digit di tengah
#             return msisdn[:5] + 'XXXX' + msisdn[-4:]
#         else:
#             return "628XXXXX"
#     else:
#         # Jika panjang caption_parts_msisdn kurang dari atau sama dengan 1
#         return "628XXXXX"
# #### AMBIL MSISDN

### RESERVE GEOCODING GOOGLE###
def reverse_geocode(latitude, longitude, api_key, location_type):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&location_type={location_type}&key={api_key}&language=id"
    response = requests.get(url)
    data = response.json()
    return data
### RESERVE GEOCODING GOOGLE###


### CONVERT CELLID TO ENBID
def convert_to_enb_cell_id_from_macan(cci):
    # Pastikan cci adalah nilai numerik
    if cci.isdigit():
        enb_id_from_macan = int(cci) // 256
        cell_id_from_macan = int(cci) % 256
        return enb_id_from_macan, cell_id_from_macan
    else:
        # Tindakan yang diambil jika cci bukan nilai numerik
        return None, None

def process_detected_text_macan(text):
    # Tambahkan logika atau pemrosesan tambahan di sini sesuai kebutuhan Anda
    # Misalnya, Anda dapat melakukan analisis lebih lanjut atau pemrosesan NLP

    with open("olah_macan_sparacingteam.txt", "w") as file:
        file.write(text)

    with open("olah_macan_sparacingteam.txt", 'r') as file:
        text = file.read()

    # Melakukan penggantian karakter
    text = text.replace('$', '5').replace('!', '1').replace(' ,', ',').replace(', ', ',').replace('undefined', '1').replace('null', '1').replace("NONE", "NULL")
    with open("olah_macan_sparacingteam.txt", 'w') as file:
        file.write(text)

    # Kode pengolahan dari olah_macan_sparacingteam.txt
    with open("olah_macan_sparacingteam.txt", "r") as file:
        input_text = file.read()

    lines = input_text.strip().replace("$", "5").replace("!", "1").replace(".", "").split('\n')
    output = ["", "NULL", "NULL", "NULL", "NULL", "", "https://maps.google.com/maps?q="]


    ################### CARI NOMOR HP
    match = re.search(r'PHONE\s+:\s+(\d+)', input_text)
    if match:
        phone_number = match.group(1)

        # Sensor 4 digit di tengah jika panjang nomor setidaknya 8 digit
        if len(phone_number) >= 8:
            phone_number = phone_number[:5] + 'XXXX' + phone_number[-4:]

        output[0] = phone_number

    # Periksa apakah nomor HP tidak diawali dengan "628"
    if output[0] is not None and not output[0].startswith("628"):
        output[0] = "628" + "xxx"  # Ganti nomor HP dengan "628xxx"

    ################### CARI TANGGAL DAN JAM
    match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', input_text)
    if match:
        timestamp = match.group(0)
        output[1] = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%d %b %Y %H:%M:%S')
    if not match:
        # Cari IDLE dan ambil nilai jika ada
        idle_match = re.search(r'IDLE\s+:\s+(\d+)', input_text)
        if idle_match:
            idle_value = int(idle_match.group(1))
            output[1] = str(idle_value) + " min"

    ################## CARI MCC, MNC, LAC, DAN CCI
    mcc_match = re.search(r'MCC\s+:\s+(\d+)', input_text)
    mnc_match = re.search(r'MNC\s+:\s+(\d+)', input_text)
    lac_match = re.search(r'LAC\s+:\s+(\d+)', input_text)
    cci_match = re.search(r'CCI\s+:\s+(\d+)', input_text)

    if mcc_match:
        mcc = mcc_match.group(1)
    else:
        mcc = "510"

    if mnc_match:
        mnc = mnc_match.group(1)
    else:
        mnc = "XXX"

    if lac_match:
        lac = lac_match.group(1)
    else:
        lac = "XXX"

    if cci_match:
        cci = cci_match.group(1)
        enb_id_from_macan, cell_id_from_macan = convert_to_enb_cell_id_from_macan(cci)
        lac = enb_id_from_macan
        cci = cell_id_from_macan
        #print("Service Cell:", cci)
        print("eNB ID:", enb_id_from_macan)
        print("Cell ID:", cell_id_from_macan)
    else:
        # Cari nilai CCI dari CI jika CCI tidak ditemukan
        ci_match = re.search(r'CI\s+:\s+(\d+)', input_text)
        if ci_match:
            cci = ci_match.group(1)
        else:
            cci = "1"

    output[2] = f"{mcc}-{mnc}-{lac}-{cci}"
    print(f"{output[2]}")


    ################## CARI IMSI
    imsi_match = re.search(r'IMSI\s+:\s+(\d+)', input_text)
    if imsi_match:
        output[3] = imsi_match.group(1)

    ################## CARI IMEI
    imei_match = re.search(r'IMEI\s+:\s+(\w+)', input_text)
    if imei_match:
        output[4] = imei_match.group(1)

    ################## INPUT DEVICE
    # Mendapatkan informasi perangkat dari file "IMEI.csv"
    imei_tac = output[4][:8]
    imei_tac1 = output[4][:14]

    # Periksa apakah imei_tac adalah 'Null'
    if imei_tac.lower() != 'null':
        # Jika tidak 'Null', lakukan konversi menjadi integer
        imei_tac = int(imei_tac)

        # Mendapatkan informasi perangkat dari file "IMEI.csv"
        imei_file_path = "IMEI.csv"
        imei_df = pd.read_csv(imei_file_path)
        device_info = imei_df[imei_df['TAC'] == int(imei_tac)]

        if not device_info.empty:
            brand = device_info.iloc[0]['BRAND']
            device_type = device_info.iloc[0]['TYPE']
            device_output = f"{brand.upper()} {device_type.upper()}"
            #bot.reply_to(message, device_output)  # Mengirim hasil pencarian ke pengguna
            output[5] = device_output

        else:
            # Memastikan pesan pengguna adalah angka
            nomor_kartu_user = re.sub(r'\D', '', str(imei_tac1))  # Menghapus karakter non-digit
            if nomor_kartu_user.isdigit() and len(nomor_kartu_user) >= 14:
                nomor_kartu_user = nomor_kartu_user[:14]  # Ambil 14 digit pertama

            digit_verifikasi = luhn_calc(nomor_kartu_user)

            url = "https://www.imei.info/api/checkimei"
            api_key = "387ebf21d533b7a570c64d6779550d6b895c22dce099cba17847fc21c33d734c"
            imei = f"{nomor_kartu_user}{digit_verifikasi}"

            # Membuat payload data untuk dikirim
            payload = {'key': api_key, 'imei': imei}

            try:
                # Mengirim permintaan POST ke API dengan waktu tunggu maksimum 12 detik
                response = requests.post(url, data=payload, timeout=15)

                # Memeriksa apakah response memiliki format yang diharapkan
                if 'imei' in response.json() and 'brand' in response.json() and 'model' in response.json():
                    output_imei_awal = response.json()
                    tac = output_imei_awal['imei'][:8]

                    # Menyiapkan data untuk ditulis ke dalam CSV
                    csv_data = {
                        'TAC': tac,
                        'HTML': f"https://swappa.com/imei/tac/{tac}",
                        'BRAND': output_imei_awal['brand'],
                        'TYPE': output_imei_awal['model']
                    }

                    # Membaca data dari file CSV (jika sudah ada)
                    with open("IMEI.csv", mode="r") as file:
                        reader = csv.reader(file)
                        existing_tacs = set(row[0] for row in reader)

                    if tac in existing_tacs:
                        #print(f"Data dengan TAC {tac} sudah ada dalam 'IMEI.csv'. Tidak ditambahkan.")
                        output[5] = f"{csv_data['BRAND']} {csv_data['TYPE'].upper()}"
                    else:
                        # Menyimpan ke dalam file CSV
                        with open("IMEI.csv", mode="a", newline='') as file:
                            writer = csv.writer(file)

                            # Menulis header jika file kosong
                            if file.tell() == 0:
                                writer.writerow(["TAC", "HTML", "BRAND", "TYPE"])

                            # Menulis baris data menggunakan nilai dari output dictionary
                            writer.writerow([tac, f"https://swappa.com/imei/tac/{tac}", csv_data['BRAND'], csv_data['TYPE']])

                        # Menampilkan output yang diinginkan
                        print(f"Data IMEI telah disimpan ke dalam file 'IMEI.csv'.")
                        output[5] = f"{csv_data['BRAND']} {csv_data['TYPE'].upper()}"

                else:
                    #print("UNKNOWN DEVICE")
                    #output[5] = "UNKNOWN DEVICE" #TECHWORLD #KAIZEN
                    output[5] = "NULL" #SLAX

            except Timeout:
                #print("RTO BRO - Request Timed Out")
                #output[5] = "UNDEFINED DEVICE"
                output[5] = "NULL" #SLAX

    else:
        output[5] = "NULL"
    ################## INPUT DEVICE


    ################## CARI URL MAP
    map_match = re.search(r'MAP\s+:\s+https://maps\.google\.com/maps\?q=(-?\d+\.\d+),(-?\d+\.\d+)', input_text)
    if not map_match:
        map_match = re.search(r'MAPS\s+:\s+https://maps\.google\.com/maps\?q=(-?\d+\.\d+),(-?\d+\.\d+)', input_text)

    if map_match:
        latitude = map_match.group(1)
        longitude = map_match.group(2)
        output[6] = f"https://maps.google.com/maps?q={latitude},{longitude}"
        if mnc is not None and lac is not None and cci_match is not None and str(mnc) not in ["XXX"] and str(lac) not in ["XXX"] and str(cci) not in ["XXX"] and str(map_match) not in ["https://maps.google.com/maps?q=,", "https://maps.google.com/maps?q=0,0"]:
            # Read the existing data in "Combain.csv"
            existing_data = set()
            with open("Combain.csv", mode='r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip the header row
                for row in reader:
                    mcc, mnc, lac, cid = row[1], row[2], row[3], row[4]
                    existing_data.add((mcc, mnc, lac, cid))

            # Check if the MCC, MNC, LAC, and CID combination already exists
            if (output[2].split('-')[0], output[2].split('-')[1], output[2].split('-')[2], output[2].split('-')[3]) not in existing_data:
                # Append the new data to "Combain.csv" without overwriting its previous contents
                with open("Combain.csv", mode='a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["CEKPOS", output[2].split('-')[0], output[2].split('-')[1], output[2].split('-')[2],
                                     output[2].split('-')[3], "Null", longitude, latitude, "Null"])
        else:
            print("LAC CID MAPS KOSONG")
    else:
        mcc, mnc, lac, cid = output[2].split('-')
        filenames = file_mapping.get(output[2][:6], [])
        data_found = False

        for filename in filenames:
            df = pd.read_csv(filename, delimiter=',')
            if filename == 'XL.csv':
                filtered_data = df[
                    ((df['MCC'] == int(mcc)) & (df['MNC'] == int(mnc)) & (df['ENBID'] == int(lac)) & (df['SECTORID'] == int(cid))) |
                    ((df['MCC'] == int(mcc)) & (df['MNC'] == int(mnc)) & (df['ENBID'] == int(lac)) & (df['SECTORID'].isnull()))
                ]
                if not filtered_data.empty:
                    latitude = filtered_data.iloc[0]['LATITUDE']
                    longitude = filtered_data.iloc[0]['LONGITUDE']
                    output[6] = f'https://maps.google.com/maps?q={latitude},{longitude}'
                    data_found = True
                    print('XL.csv Found')
                    break
            elif filename == 'Combain.csv':
                filtered_data = df[
                    ((df['mcc'] == int(mcc)) & (df['net'] == int(mnc)) & (df['area'] == int(lac)) & (df['cell'] == int(cid))) |
                    ((df['mcc'] == int(mcc)) & (df['net'] == int(mnc)) & (df['area'] == int(lac)) & (df['cell'].isnull()))
                ]
                if not filtered_data.empty:
                    latitude = filtered_data.iloc[0]['lat']
                    longitude = filtered_data.iloc[0]['lon']
                    output[6] = f'https://maps.google.com/maps?q={latitude},{longitude}'
                    data_found = True
                    print('Combain.csv Found')
                    break
            elif filename == 'MLS.csv':
                filtered_data = df[
                    ((df['mcc'] == int(mcc)) & (df['net'] == int(mnc)) & (df['area'] == int(lac)) & (df['cell'] == int(cid))) |
                    ((df['mcc'] == int(mcc)) & (df['net'] == int(mnc)) & (df['area'] == int(lac)) & (df['cell'].isnull()))
                ]
                if not filtered_data.empty:
                    latitude = filtered_data.iloc[0]['lat']
                    longitude = filtered_data.iloc[0]['lon']
                    output[6] = f'https://maps.google.com/maps?q={latitude},{longitude}'
                    data_found = True
                    print('MLS.csv Found')
                    break
            elif filename == 'IM3H3I.csv':
                filtered_data = df[
                    ((df['MCC_MOBILE_COUNTRY_CODE'] == int(mcc)) & (df['MNC_MOBILE_NETWORK_CODE'] == int(mnc)) & (df['ENBID'] == int(lac)) & (df['SectorID'] == int(cid))) |
                    ((df['MCC_MOBILE_COUNTRY_CODE'] == int(mcc)) & (df['MNC_MOBILE_NETWORK_CODE'] == int(mnc)) & (df['ENBID'] == int(lac)) & (df['SectorID'].isnull())) |
                    ((df['MCC_MOBILE_COUNTRY_CODE'] == int(mcc)) & (df['MNC_MOBILE_NETWORK_CODE'] == int(mnc)) & (df['TAC_4G'] == int(lac)) & (df['PCI'] == int(cid))) |
                    ((df['MCC_MOBILE_COUNTRY_CODE'] == int(mcc)) & (df['MNC_MOBILE_NETWORK_CODE'] == int(mnc)) & (df['TAC_4G'] == int(lac)) & (df['PCI'].isnull())) |
                    ((df['MCC_MOBILE_COUNTRY_CODE'] == int(mcc)) & (df['MNC_MOBILE_NETWORK_CODE'] == int(mnc)) & (df['LAC'] == int(lac)))
                ]
                if not filtered_data.empty:
                    latitude = filtered_data.iloc[0]['Y_LATITUDE']
                    longitude = filtered_data.iloc[0]['X_LONGITUDE']
                    output[6] = f'https://maps.google.com/maps?q={latitude},{longitude}'
                    data_found = True
                    print('IM3H3I.csv Found')
                    break
            elif filename == '510new.csv':
                filtered_data = df[
                    ((df['mcc'] == int(mcc)) & (df['net'] == int(mnc)) & (df['area'] == int(lac)) & (df['cell'] == int(cid))) |
                    ((df['mcc'] == int(mcc)) & (df['net'] == int(mnc)) & (df['area'] == int(lac)) & (df['cell'].isnull()))
                ]
                if not filtered_data.empty:
                    latitude = filtered_data.iloc[0]['lat']
                    longitude = filtered_data.iloc[0]['lon']
                    output[6] = f'https://maps.google.com/maps?q={latitude},{longitude}'
                    data_found = True
                    print('510new.csv Found')
                    break

        for filename in filenames:
            df = pd.read_csv(filename, delimiter=',')
            if filename == 'XL.csv':
                filtered_data = df[
                    ((df['MCC'] == int(mcc)) & (df['MNC'] == int(mnc)) & (df['ENBID'] == int(lac)))
                ]
                if not filtered_data.empty:
                    latitude = filtered_data.iloc[0]['LATITUDE']
                    longitude = filtered_data.iloc[0]['LONGITUDE']
                    output[6] = f'https://maps.google.com/maps?q={latitude},{longitude}'
                    data_found = True
                    print('XL.csv Found')
                    break
            elif filename == 'Combain.csv':
                filtered_data = df[
                    ((df['mcc'] == int(mcc)) & (df['net'] == int(mnc)) & (df['area'] == int(lac)))
                ]
                if not filtered_data.empty:
                    latitude = filtered_data.iloc[0]['lat']
                    longitude = filtered_data.iloc[0]['lon']
                    output[6] = f'https://maps.google.com/maps?q={latitude},{longitude}'
                    data_found = True
                    print('Combain.csv Found')
                    break
            elif filename == 'MLS.csv':
                filtered_data = df[
                    ((df['mcc'] == int(mcc)) & (df['net'] == int(mnc)) & (df['area'] == int(lac)))
                ]
                if not filtered_data.empty:
                    latitude = filtered_data.iloc[0]['lat']
                    longitude = filtered_data.iloc[0]['lon']
                    output[6] = f'https://maps.google.com/maps?q={latitude},{longitude}'
                    data_found = True
                    print('MLS.csv Found')
                    break
            elif filename == 'IM3H3I.csv':
                filtered_data = df[
                    ((df['MCC_MOBILE_COUNTRY_CODE'] == int(mcc)) & (df['MNC_MOBILE_NETWORK_CODE'] == int(mnc)) & (df['ENBID'] == int(lac))) |
                    ((df['MCC_MOBILE_COUNTRY_CODE'] == int(mcc)) & (df['MNC_MOBILE_NETWORK_CODE'] == int(mnc)) & (df['TAC_4G'] == int(lac))) |
                    ((df['MCC_MOBILE_COUNTRY_CODE'] == int(mcc)) & (df['MNC_MOBILE_NETWORK_CODE'] == int(mnc)) & (df['LAC'] == int(lac)))
                ]
                if not filtered_data.empty:
                    latitude = filtered_data.iloc[0]['Y_LATITUDE']
                    longitude = filtered_data.iloc[0]['X_LONGITUDE']
                    output[6] = f'https://maps.google.com/maps?q={latitude},{longitude}'
                    data_found = True
                    print('IM3H3I.csv Found')
                    break
            elif filename == '510new.csv':
                filtered_data = df[
                    ((df['mcc'] == int(mcc)) & (df['net'] == int(mnc)) & (df['area'] == int(lac)))
                ]
                if not filtered_data.empty:
                    latitude = filtered_data.iloc[0]['lat']
                    longitude = filtered_data.iloc[0]['lon']
                    output[6] = f'https://maps.google.com/maps?q={latitude},{longitude}'
                    data_found = True
                    print('510new.csv Found')
                    break

        if not data_found:
            output[6] = "https://maps.google.com/maps?q=0,0"

    #PRINT OUTPUT 0-6
    #for item in output:
        #print(item)

    ###PERINTAH NETWORK:2G ATAU NETWORK:4G
    # Menentukan jenis jaringan berdasarkan panjang cid dan nilai cid
    cid_info = output[2]

    if cid_info is not None and cid_info not in ["null-null-null-null", "null", "NULL-NULL-NULL-NULL", "NULL"]:
        cid_length = len(cid_info.split('-')[3])
        cid_value = int(cid_info.split('-')[3])

        if cid_value == 1 or cid_length > 3:
            output_network = "2G"
        else:
            output_network = "4G"
    else:
        output_network = "-"

    # Menambahkan baris "NETWORK" ke dalam output
    #output.append(f"NETWORK : {output_network}")
    ###PERINTAH NETWORK:2G ATAU NETWORK:4G



    ###PERINTAH SITENAME
    match = re.search(r'(-?\d+\.\d+),(-?\d+\.\d+)', output[6])
    # Cek apakah latitude dan longitude tidak kosong
    if match:
        latitude, longitude = match.group(1), match.group(2)
        # Coba melakukan reverse geocoding
        try:
            location_types = ["GEOMETRIC_CENTER", "ROOFTOP", "RANGE_INTERPOLATED"]
            api_key = "AIzaSyDterpgmtZdyzSCs2vJbcx1SdhwMQgA2yM"

            for location_type in location_types:
                result = reverse_geocode(latitude, longitude, api_key, location_type)

                if result['status'] == 'OK':
                    for item in result['results']:
                        kelurahan = kecamatan = kota = provinsi = ""
                        for component in item['address_components']:
                            if 'administrative_area_level_4' in component['types']:
                                kelurahan = component['long_name'].upper()
                            elif 'administrative_area_level_3' in component['types']:
                                kecamatan = component['long_name'].upper()
                            elif 'administrative_area_level_2' in component['types']:
                                kota = component['long_name'].upper()
                            elif 'administrative_area_level_1' in component['types']:
                                provinsi = component['long_name'].upper()
                        for res in result['results']:
                            if res['geometry']['location_type'] == 'GEOMETRIC_CENTER':
                                formatted_address = res['formatted_address']
                                print("Alamat ditemukan:", formatted_address)
                        # Menghilangkan kata "KOTA" dan "KECAMATAN"
                        kota = kota.replace("KOTA ", "")
                        kota = kota.replace("KABUPATEN ", "")
                        kecamatan = kecamatan.replace("KECAMATAN ", "")
                        kelurahan = kelurahan.replace("KELURAHAN ", "")
                        kelurahan = kelurahan.replace("DESA ", "")
                        situs_name = f"KEL. {kelurahan}, KEC. {kecamatan}, KAB. {kota}, PROV. {provinsi}"
                        print(situs_name)
                        print(formatted_address)
                        break  # Mengambil alamat dari hasil pertama saja
                    break  # Keluar dari loop jika berhasil mendapatkan alamat
                #else:
                    #print(f"Reverse geocoding dengan location_type {location_type} gagal.")

            if result['status'] != 'OK':
                print("Gagal melakukan reverse geocoding dengan semua location_type yang diberikan.")
                situs_name = "-"
                #formatted_address = "LOKASI TIDAK DITEMUKAN"
        except ValueError as e:
            # Tangani eksepsi, contohnya:
            situs_name = "-"
            #formatted_address = "LOKASI TIDAK DITEMUKAN"
            print(f"Error saat melakukan reverse geocoding: {e}")
            # Berikan respons yang sesuai kepada pengguna atau hentikan pemrosesan lebih lanjut


    else:
        # Output jika pasangan nilai latitude dan longitude tidak ditemukan
        situs_name = "-"
        #formatted_address = "LOKASI TIDAK DITEMUKAN"

    ###PERINTAH SITENAME


    ###PERINTAH AGE
    # Waktu sekarang
    waktu_sekarang_dong = datetime.now()

    # Meminta pengguna untuk memasukkan tanggal dan jam
    tanggal_input_str_dong = output[1]

    # Menangani input "Null"
    if tanggal_input_str_dong.lower() == "null":
        selisih_waktu_output = "NULL mins"
        phone_status_output = "OFF"
        #print("OFFLINE MORE 72 HOURS")
    else:
        tanggal_format_selisih_waktu_output = "%d %b %Y %H:%M:%S"

        try:
            # Mengonversi input pengguna ke objek datetime
            waktu_input_dong = datetime.strptime(tanggal_input_str_dong, tanggal_format_selisih_waktu_output)

            # Menghitung selisih waktu dalam menit
            selisih_waktu_dong = round((waktu_sekarang_dong - waktu_input_dong).total_seconds() / 60)

            # Menyamakan selisih waktu dengan 0 jika kurang dari 5 menit
            selisih_waktu_dong = max(selisih_waktu_dong, 5)

            if selisih_waktu_dong == 5:
                #print("Waktu sekarang hampir sama dengan waktu input.")
                selisih_waktu_output = "0 mins"
                phone_status_output = "ON"
            else:
                selisih_waktu_output = f"{selisih_waktu_dong} mins"
                phone_status_output = "OFF"
                #print(f"Waktu sekarang: {waktu_sekarang_dong}")
                #print(f"Selisih waktu antara jam sekarang dan jam input adalah {selisih_waktu_dong} menit.")
        except ValueError:
            selisih_waktu_output = "NULL mins"
            phone_status_output = "OFF"
            #print("Format tanggal yang dimasukkan tidak sesuai. Pastikan formatnya adalah DD MMM YYYY HH:mm:ss.")
    ###PERINTAH AGE



    ###LATITUDE DAN LONGITUDE
    match = re.search(r'(-?\d+\.\d+),(-?\d+\.\d+)', output[6])
    # Mengambil nilai lintang dan bujur
    if match:
        latitude_output_dong = float(match.group(1))
        longitude_output_dong = float(match.group(2))
        ####### PROVE IT WATER OR NOT #######
        url = "https://isitwater-com.p.rapidapi.com/"
        querystring = {"latitude":latitude_output_dong,"longitude":longitude_output_dong}
        headers = {
            "X-RapidAPI-Key": "d57deceb4emsh3eb35be29c98d6dp1d2cb3jsn357627033694",
            "X-RapidAPI-Host": "isitwater-com.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()
        if data['water']:
            print("WATER")

            # Koordinat yang diberikan
            lat_long_water = (latitude_output_dong, longitude_output_dong)

            # Membuat objek geolocator
            geolocator = Nominatim(user_agent="Mozilla/5.0 (Linux; Linux i553 ) Gecko/20100101 Firefox/63.0")

            # Mendapatkan lokasi daratan terdekat
            location_water = geolocator.reverse(lat_long_water)

            # Menampilkan hasil
            print("Daratan terdekat dari koordinat (-3.29695, 128.949) adalah:", location_water.address)
            print("Koordinat daratan terdekat:", location_water.latitude, location_water.longitude)

            # Koordinat dari titik awal
            latwater1, lonwater1 = math.radians(latitude_output_dong), math.radians(longitude_output_dong)

            # Koordinat dari titik tujuan (daratan terdekat)
            latwater2, lonwater2 = math.radians(location_water.latitude), math.radians(location_water.longitude)

            # Menghitung perbedaan antara longitude
            d_lon_water = lonwater2 - lonwater1

            # Menghitung sudut menggunakan rumus trigonometri
            y = math.sin(d_lon_water) * math.cos(latwater2)
            x = math.cos(latwater1) * math.sin(latwater2) - math.sin(latwater1) * math.cos(latwater2) * math.cos(d_lon_water)
            bearing = math.atan2(y, x)

            # Mengonversi sudut dari radian ke derajat
            bearing = math.degrees(bearing)

            # Memastikan sudut berada dalam rentang 0-360 derajat
            bearing = (bearing + 360) % 360

            # Mencetak sudut
            print("Sudut dari titik awal ke daratan terdekat adalah:", bearing)
            latitude_output_dong = float(location_water.latitude)
            longitude_output_dong = float(location_water.longitude)
            azimuth_water = round(bearing)  # Bulatkan azimuth ke angka bulat terdekat
        else:
            print("DARATAN BUKAN AIR")
            # Menangani kondisi daratan bukan air
            latitude_output_dong = float(match.group(1))
            longitude_output_dong = float(match.group(2))
            azimuth_water = ""

        ####### PROVE IT WATER OR NOT #######
        #print("Latitude:", latitude_output_dong)
        #print("Longitude:", longitude_output_dong)
    else:
        #print("Tidak dapat menemukan koordinat dalam URL.")
        #print("Latitude:", latitude_output_dong)
        #print("Longitude:", longitude_output_dong)
        latitude_output_dong = "NULL"
        longitude_output_dong = "NULL"
        azimuth_water = ""
    ###LATITUDE DAN LONGITUDE

    ###LAC CID
    # Dapatkan nilai MCC, MNC, LAC, dan CI dari output[2]
    mcc_out_dong, mnc_out_dong, lac_out_dong, ci_out_dong = output[2].split('-')[0], output[2].split('-')[1], output[2].split('-')[2], output[2].split('-')[3]
    ###LAC CID

    if mnc_out_dong in ["null", "Null", "NULL"]: # NULL
        azimuth = ""
    else:
        print("NO")


    ###AZIMUTH###
    if azimuth_water is not None and str(azimuth_water) not in ["null", "NULL", "Null", ""]:
        azimuth = azimuth_water
    else:
        if mnc_out_dong == "10": # TELKOMSEL
            if output_network == "4G": # TELKOMSEL 4G
                if ci_out_dong.startswith(("1", "4", "7", "0")):
                    azimuth = "0"
                elif ci_out_dong.startswith(("2", "5", "8")):
                    azimuth = "120"
                elif ci_out_dong.startswith(("3", "6", "9")):
                    azimuth = "240"
                else:
                    azimuth = "0"
            elif output_network == "2G": # TELKOMSEL 2G
                if len(ci_out_dong) > 1:
                    last_digit = ci_out_dong[-1]
                    if last_digit in ["1", "4", "7", "0"]:
                        azimuth = "0"
                    elif last_digit in ["2", "5", "8"]:
                        azimuth = "120"
                    elif last_digit in ["3", "6", "9"]:
                        azimuth = "240"
                else:
                    azimuth = "0"

        if mnc_out_dong in ["1", "01", "21", "89"]: # INDOSAT
            if "azimuth_im3_csv" in locals() or "azimuth_im3_csv" in globals():
                azimuth = f"{azimuth_im3_csv.replace('360', '0')}"
            else:
                if len(ci_out_dong) > 1:
                    last_digit = ci_out_dong[-1]
                    if last_digit in ["1", "4", "7", "0"]:
                        azimuth = "0"
                    elif last_digit in ["2", "5", "8"]:
                        azimuth = "120"
                    elif last_digit in ["3", "6", "9"]:
                        azimuth = "240"
                else:
                    azimuth = "0"

        if mnc_out_dong in ["11", "09", "9"]: # XL SMARTFREN
            if output_network == "4G": # XL SMARTFREN 4G
                last_digit = ci_out_dong[-1]
                if last_digit in ["1", "4", "7", "0"]:
                    azimuth = "0"
                elif last_digit in ["2", "5", "8"]:
                    azimuth = "120"
                elif last_digit in ["3", "6", "9"]:
                    azimuth = "240"
                else:
                    azimuth = "0"
            elif output_network == "2G":  # XL SMARTFREN 2G
                if len(ci_out_dong) > 1:
                    last_digit = ci_out_dong[-1]
                    if last_digit in ["1", "4", "7", "0"]:
                        azimuth = "0"
                    elif last_digit in ["2", "5", "8"]:
                        azimuth = "120"
                    elif last_digit in ["3", "6", "9"]:
                        azimuth = "240"
                else:
                    azimuth = "0"
        # Jika mnc_out_dong tidak ditemukan, set azimuth menjadi "0"
        if mnc_out_dong not in ["10", "1", "01", "21", "89", "11", "09", "9"]:
            azimuth = "0"
    ###AZIMUTH###


    ###PERINTAH OPERATOR TSEL, ISAT, XL, SMARTFREN, H3I
    # Menentukan awalan MSISDN
    msisdn_prefix = output[0][:5]

    # Menentukan operator berdasarkan awalan MSISDN
    if msisdn_prefix.startswith(('62811', '62812', '62813', '6282', '62851', '62852', '62853')):
        operator = "TELKOMSEL"
    elif msisdn_prefix.startswith(('62814', '62815', '62816', '62855', '62856', '62857', '62858')):
        operator = "INDOSAT"
    elif msisdn_prefix.startswith('6289'):
        operator = "H3I"
    elif msisdn_prefix.startswith(('62817', '62818', '62819', '62859', '62877', '62878', '6283')):
        operator = "XL AXIATA"
    elif msisdn_prefix.startswith('6288'):
        operator = "SMARTFREN"
    elif mnc_out_dong.startswith('10'):
        operator = "TELKOMSEL"
    elif mnc_out_dong.startswith('11'):
        operator = "XL AXIATA"
    elif mnc_out_dong.startswith(('9', '09')):
        operator = "SMARTFREN"
    elif mnc_out_dong.startswith(('1', '01', '21', '89')):
        operator = "INDOSAT H3I"
    else:
        operator = "UNKNOWN"

    # Menambahkan informasi operator ke dalam output
    #output.append(operator)
    ###PERINTAH OPERATOR TSEL, ISAT, XL, SMARTFREN, H3I

    # Menyimpan hasil olahan ke file "olah_macan_sparacingteam.txt"
    with open("olah_macan_sparacingteam.txt", "w") as file:
        for item in output:
            file.write(f"{item}\n")
######SPARACINGTEAM PILARI FORMAT######
    formatted_output = [
        #f"REQUEST: {current_datetime}\r\n",
        #f"Age: {selisih_waktu_output}",
        #f"LAC: {lac_out_dong}",
        #f"CI: {ci_out_dong}",
        #f"Long: {longitude_output_dong}",
        #f"Lat: {latitude_output_dong}",
        #f"Alamat: {situs_name}",
        #f"Perangkat : {output[5]}",
        #f"Sistem Operasi: -",
        #f"Operator : {operator}",
        #f"ONLINE : {output[1]}",
        #f"CELLREF : {output[2]}",
        #f"NETWORK : {output_network}",
        {"MSISDN" : output[0],
        "IMSI" : output[3],
        "IMEI" : output[4],
        "Dttm" : output[1] + " UTC +7",
        "Cell ID" : lac_out_dong + "-" + ci_out_dong,
        "Azimuth" : azimuth+"°",
        "Lat" : latitude_output_dong,
        "Long" : longitude_output_dong,
        "Maps" : output[6],
        "Location " : situs_name},
    ] #Simpan ke object

    print("MACAN NUSANTARA SPARACINGTEAM FORMAT") #PRINT formatted_output
    # print(formatted_output) #PRINT formatted_output
    print("MACAN NUSANTARA SPARACINGTEAM FORMAT") #PRINT formatted_output
    # processed_text = "\n".join(formatted_output)
    # Menyimpan teks ke dalam file
    # with open("hasil_akhir_macan_sparacingteam.txt", "w") as file:
    #     file.write(formatted_output)
    # print("Data telah disimpan dalam hasil_akhir_macan_sparacingteam.txt")
    print("MACAN NUSANTARA SPARACINGTEAM FORMAT") #PRINT formatted_output
    print("MACAN NUSANTARA SPARACINGTEAM FORMAT") #PRINT formatted_output

    ####PENGAMBILAN ARSIRAN AZIMUTH
    # Mengonversi string menjadi float
    if latitude_output_dong is not None and str(latitude_output_dong) not in ["null", "NULL", "Null", ""] and longitude_output_dong is not None and str(longitude_output_dong) not in ["null", "NULL", "Null", ""]:
        latitude_output_dong = float(latitude_output_dong)
        longitude_output_dong = float(longitude_output_dong)
    else:
        print("LATLONG TIDAK ADA DAN DOWNLOAD CELLFINDER.JPG")
        # Salin file cellfindernotfound.jpg menjadi maps_azimuth_macan_sparacingteam.jpg
        shutil.copy("cellfindernotfound.jpg", "maps_azimuth_macan_sparacingteam.jpg")
        return  # Menghentikan eksekusi fungsi jika kondisi tidak terpenuhi

    if azimuth is not None and str(azimuth) not in ["null", "NULL", "Null", ""]:
        azimuth = float(azimuth)

    # Menentukan nilai radius berdasarkan jaringan
    if output_network == "2G":
        radius = 35000  # 35 km dalam meter
        zoom_start = 10.5
    elif output_network == "4G":
        radius = 1000  # 1 km dalam meter
        zoom_start = 15
    else:
        radius = 20000  # Default radius 20 km
        zoom_start = 10.5

    # URL gambar marker
    icon_url = 'tower.png'
    if output_network not in ["2G", "4G"]:
        print("BUKAN 2G 4G DAN DOWNLOAD CELLFINDER.JPG")
        # Salin file cellfindernotfound.jpg menjadi maps_azimuth_macan_sparacingteam.jpg
        shutil.copy("cellfindernotfound.jpg", "maps_azimuth_macan_sparacingteam.jpg")
    else:
        if latitude_output_dong is not None and str(latitude_output_dong) not in ["null", "NULL", "Null", ""] and longitude_output_dong is not None and str(longitude_output_dong) not in ["null", "NULL", "Null", ""]:
            # Membuat objek peta
            mymap = folium.Map(location=[latitude_output_dong, longitude_output_dong], zoom_start=zoom_start, zoom_control=False)  # Menghilangkan kontrol zoom

            # Menambahkan marker dengan gambar dari URL dan teks yang ditingkatkan
            popup_text = f"""<div style='text-align: left; white-space: nowrap;'>
            <span style='font-size: 14px;'><b>LOKASI BTS</b></span><br>
            <b>CELL ID</b>&nbsp;&nbsp;&nbsp;&nbsp;{lac_out_dong}-{ci_out_dong}<br>
            <b>AZIMUTH</b>&nbsp;&nbsp;&nbsp;&nbsp;{azimuth}°
            </div>"""

            # Menambahkan marker dengan gambar dari URL
            icon = folium.features.CustomIcon(icon_url, icon_size=(20, 50))
            folium.Marker([latitude_output_dong, longitude_output_dong], popup=popup_text, icon=icon).add_to(mymap)

            # Menghitung titik-titik untuk membuat poligon yang menyerupai lingkaran parsial
            num_points = 100  # jumlah titik yang digunakan untuk membentuk lingkaran
            radius_deg = radius / 111000  # 1 derajat = 111 km

            if azimuth is not None and str(azimuth) not in ["null", ""]:
                if azimuth == 0:
                    start_angle = 150
                    end_angle = 270
                elif azimuth == 15:
                    start_angle = 135
                    end_angle = 265
                elif azimuth == 30:
                    start_angle = 120
                    end_angle = 250
                elif azimuth == 45:
                    start_angle = 105
                    end_angle = 235
                elif azimuth == 60:
                    start_angle = 90
                    end_angle = 220
                elif azimuth == 75:
                    start_angle = 75
                    end_angle = 205
                elif azimuth == 90:
                    start_angle = 60
                    end_angle = 190
                elif azimuth == 105:
                    start_angle = 45
                    end_angle = 175
                elif azimuth == 120:
                    start_angle = 30
                    end_angle = 150
                elif azimuth == 135:
                    start_angle = 15
                    end_angle = 135
                elif azimuth == 150:
                    start_angle = 0
                    end_angle = 120
                elif azimuth == 165:
                    start_angle = 225
                    end_angle = 105
                elif azimuth == 180:
                    start_angle = 210
                    end_angle = 90
                elif azimuth == 195:
                    start_angle = 195
                    end_angle = 75
                elif azimuth == 210:
                    start_angle = 180
                    end_angle = 60
                elif azimuth == 225:
                    start_angle = 165
                    end_angle = 45
                elif azimuth == 240:
                    start_angle = 150
                    end_angle = 30
                elif azimuth == 255:
                    start_angle = 135
                    end_angle = 15
                elif azimuth == 270:
                    start_angle = 120
                    end_angle = 0
                elif azimuth == 285:
                    start_angle = 225
                    end_angle = 345
                elif azimuth == 300:
                    start_angle = 210
                    end_angle = 330
                elif azimuth == 315:
                    start_angle = 195
                    end_angle = 315
                elif azimuth == 330:
                    start_angle = 180
                    end_angle = 300
                elif azimuth == 345:
                    start_angle = 165
                    end_angle = 285
                elif azimuth == 360:
                    start_angle = 150
                    end_angle = 270
                else:
                    # Jika azimuth tidak ditemukan, cari data azimuth yang mendekati
                    azimuth_list = [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345, 360]
                    closest_azimuth = min(azimuth_list, key=lambda x: abs(x - azimuth))
                    start_index = azimuth_list.index(closest_azimuth)
                    if start_index == 0:
                        start_angle = 150
                        end_angle = 270
                    elif start_index == len(azimuth_list) - 1:
                        start_angle = 150
                        end_angle = 270
                    else:
                        start_angle = 135 - (closest_azimuth - azimuth)
                        end_angle = 265 - (closest_azimuth - azimuth)

                polygon_points = [tuple([latitude_output_dong, longitude_output_dong])]

                for i in range(num_points + 1):
                    angle = math.radians(start_angle + (start_angle - end_angle) * i / num_points)  # Konversi ke radian
                    dx = radius_deg * math.cos(angle)
                    dy = radius_deg * math.sin(angle)
                    point = (latitude_output_dong + dy, longitude_output_dong + dx)
                    polygon_points.append(point)

                polygon_points.append(tuple([latitude_output_dong, longitude_output_dong]))  # Menambahkan titik tengah lagi untuk menutup poligon

                # Menambahkan poligon
                folium.Polygon(locations=polygon_points, color='blue', fill=True, fill_color='blue', fill_opacity=0.2).add_to(mymap)

                # Setelah menambahkan marker dan poligon ke peta, hitung batas-batas dari semua objek
                all_coords = [(latitude_output_dong, longitude_output_dong)]
                all_coords.extend(polygon_points)  # Menambahkan koordinat titik poligon
                min_lat = min(coord[0] for coord in all_coords)
                max_lat = max(coord[0] for coord in all_coords)
                min_lon = min(coord[1] for coord in all_coords)
                max_lon = max(coord[1] for coord in all_coords)

                # Menyesuaikan tampilan peta agar semua objek terlihat pada satu halaman dan berada di tengah
                mymap.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

                # Menyimpan peta dalam file html
                mymap.save('maps_azimuth_macan_sparacingteam.html')
            else:
                print("CIRCLE")
                # Jika azimuth adalah None atau "null", membuat lingkaran dengan radius 35 km
                folium.Circle(
                    location=[latitude_output_dong, longitude_output_dong],
                    radius=35000,  # Radius 35 km dalam meter
                    color='blue',
                    fill=True,
                    fill_color='blue',
                    fill_opacity=0.2
                ).add_to(mymap)

                # Setelah menambahkan lingkaran ke peta, hitung batas-batas dari lingkaran
                min_lat = latitude_output_dong - (35000 / 111000)  # Menghitung perubahan koordinat dalam derajat
                max_lat = latitude_output_dong + (35000 / 111000)
                min_lon = longitude_output_dong - (35000 / (111000 * math.cos(math.radians(latitude_output_dong))))  # Menghitung perubahan koordinat dalam derajat
                max_lon = longitude_output_dong + (35000 / (111000 * math.cos(math.radians(latitude_output_dong))))

                # Menyesuaikan tampilan peta agar hanya mencakup lingkaran dengan radiusnya
                mymap.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
                mymap.save('maps_azimuth_macan_sparacingteam.html')
        else:
            print("LATLONG TIDAK ADA DAN DOWNLOAD CELLFINDER.JPG")
            # Salin file cellfindernotfound.jpg menjadi maps_azimuth_macan_sparacingteam.jpg
            shutil.copy("cellfindernotfound.jpg", "maps_azimuth_macan_sparacingteam.jpg")

        #################################### SAVE TO JPG
        # Mendapatkan direktori saat ini
        direktori_sekarang = os.path.dirname(__file__)

        # Mengatur path file HTML
        html_file_path = os.path.join(direktori_sekarang, "maps_azimuth_macan_sparacingteam.html")
        # print(direktori_sekarang)

        # Pengaturan WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Menjalankan browser tanpa GUI (diam-diam)

        # Inisialisasi WebDriver
        driver = webdriver.Chrome(options=chrome_options)

        # Mengunjungi halaman web
        driver.get("file://" + html_file_path)
        time.sleep(2)

        # Mengambil screenshot dan menyimpannya sebagai file 'maps.jpg' di direktori saat ini
        driver.save_screenshot(os.path.join(direktori_sekarang, "maps_azimuth_macan_sparacingteam.png"))
        with open("maps_azimuth_macan_sparacingteam.jpg", "rb") as imagefile:
            map_SS = base64.b64encode(imagefile.read())
        # map_SS = {"Map Screenshot" : map_SS.decode('utf-8')}
        formatted_output[0]["Map Screenshot"] = map_SS.decode('utf-8')
        with open('hasil_akhir_macan_sparacingteam.json', 'w') as f:
            json.dump(formatted_output, f)
        # print(formatted_output)
        # print(direktori_sekarang)
        print("nyampe sini dengan selamat")
        # Menutup WebDriver
        driver.quit()
        #################################### SAVE TO JPG

    ####PENGAMBILAN ARSIRAN AZIMUTH

    return formatted_output



input_message = """"KHUSUS ANGGOTA. TIDAK DIGUNAKAN UNTUK KEPENTINGAN PRIBADI, HANYA UNTUK KEGIATAN PENEGAKAN HUKUM."

PHONE       : 6282189584353
OPERATOR    : TELKOMSEL
NETWORK     : 4G
DEVICE      : XIAOMI, MI 11T PRO (2107113SG)
IMEI        : NONE
IMSI        : 510108962584353
LAC         : 1271
CCI         : 33564999
MCC         : 510
MNC         : 10
MAP         : https://maps.google.com/maps?q=-6.137706,106.758583
LAST SEEN   : 2024-07-13 01:20:05
ADDRESS     : INDONESIA, JABOTABEK, DKI JAKARTA, JAKARTA BARAT, KEL. KAPUK-CENGKARENG

macanarya"""
# process_detected_text_macan(input_message)






app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

@app.route('/macanarya', methods=['POST'])
def generate_output ():
    raw = json.loads(request.data)
    output=process_detected_text_macan(raw['input'])
    return jsonify(output)


if __name__ == '__main__':
    app.run(port=5000)

# def forward_message_to_bororing(message):

#     phone_number = message
#     # Menghapus tanda '-' dan spasi dari nomor telepon
#     phone_number = phone_number.replace('-', '').replace(' ', '')
#     # Memeriksa apakah nomor telepon diawali dengan '08'
#     if phone_number.startswith('08'):
#         phone_number = '628' + phone_number[2:]
#     elif not phone_number.startswith('628'):
#         print("Mohon masukkan nomor telepon yang benar (Indonesia Provider Only)")
#         return



#     print("Mohon tunggu permintaan sedang di proses...")
#     # Menyiapkan pesan berdasarkan awalan nomor
#     if phone_number.startswith(('62811', '62812', '62813', '6282', '62851', '62852', '62853')):
#         message_prefix = '/MCNcp '
#     else:
#         message_prefix = '/Ccp '
    
#     # Teruskan pesan ke pengolah1 "7075880127"
#     print(f"{message_prefix}{phone_number}")
#     print(barcode_number_msisdn_from_caption(f"{message_prefix}{phone_number}"))



# forward_message_to_bororing("6282333120599")
