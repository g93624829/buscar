# import undetected_chromedriver.v2 as uc
from django.http import JsonResponse
from django.shortcuts import render
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
from .models import Datos


def mostrar_pagina(request):
    dni_id = '00003603'  # Valor de inicio del DNI como cadena
    resultados_dni = []  # Lista para almacenar los resultados de las búsquedas

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ejecutar en modo headless
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Inicializa el navegador una sola vez
    driver = webdriver.Chrome(options=chrome_options)

    try:
        while int(dni_id) <= 99999999:
            dni_str = dni_id.zfill(8)
            print(f'Consultando DNI: {dni_str}')
            
            # Pasando el DNI como parámetro adecuado
            resultados_dni.extend(buscar(driver, dni_str))  # Acumular los resultados de cada búsqueda
            
            # Incrementar el DNI para la siguiente iteración
            dni_id = str(int(dni_id) + 1).zfill(8)
        
    finally:
        driver.quit()  # Asegúrate de cerrar el navegador al final

    return render(request, 'index.html', {
        'dni_id': dni_id,
        'resultados_dni': resultados_dni,  # Pasar los resultados a la vista
    })


def buscar(driver, dni_varios):
    data_collected = []  # Lista para almacenar los datos recolectados

    try:
        dni_str = dni_varios.zfill(8)  # Asegurarse que el DNI tenga 8 dígitos

        # Ingresar al sitio de consulta de SUNAT
        driver.get('https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp')
        time.sleep(2)  # Esperar para que cargue la página

        # Buscar el DNI
        try:
            btn_por_documento = driver.find_element(By.ID, 'btnPorDocumento')
            btn_por_documento.click()
            time.sleep(1)
        except Exception as e:
            print(f"Error al hacer clic en el botón 'Por Documento': {e}")
            return data_collected

        try:
            dni_input = driver.find_element(By.ID, 'txtNumeroDocumento')
            dni_input.clear()
            dni_input.send_keys(dni_str)
            time.sleep(1)
        except Exception as e:
            print(f"Error al ingresar el DNI: {e}")
            return data_collected

        try:
            btn_buscar = driver.find_element(By.ID, 'btnAceptar')
            btn_buscar.click()
            time.sleep(3)
        except Exception as e:
            print(f"Error al hacer clic en el botón 'Buscar': {e}")
            return data_collected

        # Extraer el nombre de la página SUNAT si está disponible
        nombre = None
        try:
            response = driver.page_source
            soup = BeautifulSoup(response, 'html.parser')
            nombre_elements = soup.find_all('h4', class_='list-group-item-heading')
            if len(nombre_elements) > 1:
                nombre = nombre_elements[1].text.strip()

            if nombre:
                # Guardar la información en la base de datos
                Datos.objects.update_or_create(dni=dni_str, defaults={"nombres_completos": nombre})
                data_collected.append({"dni": dni_str, "nombre_completo": nombre})
        except Exception as e:
            print(f"Error al extraer la información de la página de SUNAT: {e}")

        # Si no se encuentra el nombre en SUNAT, consultar la página eldni.com
        if not nombre:
            try:
                driver.get('https://eldni.com/')
                time.sleep(2)
                dni_input = driver.find_element(By.ID, 'dni')
                dni_input.clear()
                dni_input.send_keys(dni_str)
                time.sleep(1)

                btn_buscar = driver.find_element(By.ID, 'btn-buscar-datos-por-dni')
                btn_buscar.click()
                time.sleep(5)

                response = driver.page_source
                soup = BeautifulSoup(response, 'html.parser')
                apellidop = soup.find('input', {'id': 'apellidop'})['value'].strip()
                apellidom = soup.find('input', {'id': 'apellidom'})['value'].strip()
                nombres = soup.find('input', {'id': 'nombres'})['value'].strip()
                nombre = f"{apellidop} {apellidom} {nombres}"

                Datos.objects.update_or_create(dni=dni_str, defaults={"nombres_completos": nombre})
                data_collected.append({"dni": dni_str, "nombre_completo": nombre})
            except Exception as e:
                print(f"Error al extraer la información de la página eldni.com: {e}")
                Datos.objects.update_or_create(dni=dni_str, defaults={"nombres_completos": "No encontrado"})

        return data_collected  # Devolver solo los datos recolectados

    except Exception as e:
        print(f"Error general en la función buscar: {e}")
        return data_collected
