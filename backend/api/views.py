from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import json, time

@api_view(['GET'])
def datos(request):
    data = {"mensaje": "Hola desde Django!"}
    return Response(data)


def Login():

    usuario = "steevenandresmaila@gmail.com"
    contraseña = "Vasodeagua11"

    options = Options()
    #options.add_argument("--headless")  # opcional: sin abrir ventana
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)
    driver.get("https://aromotor.com/web#action=206&model=account.move&view_type=list&cids=1&menu_id=124")

    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/main/div/form")))

    driver.find_element(By.XPATH, "/html/body/div[1]/main/div/form/div[1]/input").send_keys(usuario)
    driver.find_element(By.XPATH, "/html/body/div[1]/main/div/form/div[2]/input").send_keys(contraseña)
    driver.find_element(By.XPATH, "/html/body/div[1]/main/div/form/div[3]/button").click()

    return driver



@api_view(['GET'])
def obtener_datos_clientes(request):


    driver = Login()

    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[2]/div/div[1]/table")))
    time.sleep(3) 

    soup = BeautifulSoup(driver.page_source, "html.parser")

    table = soup.find("table", class_="o_list_table")

    headers = []
    for th in table.find("thead").find_all("th"):
        text = th.get_text(strip=True)
        if text and len(text) > 1:
            headers.append(text)

    print(headers)


    data = []
    filas = soup.select("table.o_list_table tbody tr")
    for f in filas:
        celdas = [c.get_text(strip=True) for c in f.find_all("td")]
        data.append(celdas)

    
    return Response(data)